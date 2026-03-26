#!/usr/bin/env python3
"""
Execution Pipeline — PR1: Cost + Output Enforcement

Changes:
- single_message_mode: one response only, no progress messages
- output enforced to MAX_OUTPUT_TOKENS per tier
- NO_REPLY fast-path exits before any model work
- Daily cost check at pipeline entry
- No simulated cost logging
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from router import route_message
from context_guard import context_status, emergency_compact
from agent_executor import AgentExecutor
from action_executor import execute_if_approved, send_response_if_ready
from model_selector import (
    ModelSelector, MAX_OUTPUT_TOKENS, MAX_DAILY_COST_USD,
    DailyCostExceededError
)

# ── PR1 output enforcement ────────────────────────────────────────────────────
SINGLE_MESSAGE_MODE: bool = True   # never send more than one message per turn
NO_PROGRESS_MESSAGES: bool = True  # never send "processing..." style messages


def enforce_output_length(text: str, tier: str) -> str:
    """Truncate output to MAX_OUTPUT_TOKENS estimate (chars ≈ tokens * 4)."""
    if not text or tier == "none":
        return text
    max_tokens = MAX_OUTPUT_TOKENS.get(tier, 400)
    max_chars = max_tokens * 4   # rough char→token ratio
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " [קוצר]"


class ExecutionPipeline:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get(
            "DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
        self.execution_log = []
        self.agent_executor = AgentExecutor(workspace_path)

    def execute(self, message: str, channel: str = None,
                group_id: str = None, metadata: Dict = None) -> Dict:
        """
        Main execution.

        PR1 order:
        1. Daily cost gate (hard stop)
        2. Route (includes NO_REPLY fast-path)
        3. NO_REPLY → return immediately, $0
        4. Execute agent
        5. Enforce output length
        6. Single-message QA
        7. Log
        """
        start = datetime.now()
        execution_id = f"exec_{start.strftime('%Y%m%d_%H%M%S')}_{id(message)}"
        metadata = metadata or {}

        try:
            # ── 1. Daily cost gate ────────────────────────────────────────────
            ms = ModelSelector(str(self.workspace))
            today_cost = ms._get_today_cost()
            if today_cost >= MAX_DAILY_COST_USD:
                record = self._make_record(execution_id, start, message,
                                           channel, group_id,
                                           status="blocked_daily_cost")
                self._log_execution(record)
                return {
                    "status": "blocked",
                    "execution_id": execution_id,
                    "reason": f"Daily cost cap ${MAX_DAILY_COST_USD} reached "
                              f"(today=${today_cost:.4f})",
                    "pr1_enforcement": "daily_cost_cap",
                }

            # ── 2. Route ──────────────────────────────────────────────────────
            routing = route_message(message, channel, group_id)

            # ── 3. NO_REPLY fast-path ─────────────────────────────────────────
            if routing["routing_decision"]["action"] == "no_reply":
                record = self._make_record(execution_id, start, message,
                                           channel, group_id,
                                           status="no_reply", cost=0.0,
                                           tier="none")
                self._log_execution(record)
                return {
                    "status": "no_reply",
                    "execution_id": execution_id,
                    "routing": routing,
                    "cost_usd": 0.0,
                    "pr1_enforcement": "no_reply_fast_path",
                    "execution_summary": record,
                }

            # ── Context guard ─────────────────────────────────────────────────
            ctx = context_status()
            if ctx["status"] == "critical":
                emergency_compact()
                ctx = context_status()

            # ── 4. Execute agent ──────────────────────────────────────────────
            if routing["routing_decision"]["action"] == "handle_direct":
                result = self._handle_direct(message, routing, metadata)
            else:
                agent_name = routing["routing_decision"]["agent"]
                result = self.agent_executor.execute_agent_task(
                    agent_name, message, routing,
                    {**metadata, "execution_id": execution_id}
                )

            # ── 5. Output length enforcement ──────────────────────────────────
            tier = routing.get("model", "tier2")
            if "summary" in result:
                result["summary"] = enforce_output_length(result["summary"], tier)
            if "response" in result:
                result["response"] = enforce_output_length(result["response"], tier)

            # ── 6. QA ─────────────────────────────────────────────────────────
            qa_result = self._qa_check(result, routing)

            # ── 7. Action + response ──────────────────────────────────────────
            exec_result = execute_if_approved(result, qa_result, channel)
            resp_result = send_response_if_ready(
                exec_result, channel, metadata.get("sender_id")
            )

            cost = result.get("execution_details", {}).get("cost_usd", 0.0)
            record = self._make_record(execution_id, start, message,
                                       channel, group_id,
                                       status="success", cost=cost,
                                       tier=tier,
                                       agent=routing["routing_decision"].get("agent"),
                                       qa_passed=qa_result["passed"])
            self._log_execution(record)

            return {
                "status": "success",
                "execution_id": execution_id,
                "routing": routing,
                "agent_result": result,
                "qa_result": qa_result,
                "execution_result": exec_result,
                "response_result": resp_result,
                "execution_summary": record,
            }

        except Exception as e:
            record = self._make_record(execution_id, start, message,
                                       channel, group_id,
                                       status="error", error=str(e))
            self._log_execution(record)
            return {
                "status": "error",
                "execution_id": execution_id,
                "error": str(e),
                "execution_summary": record,
            }

    # ── Direct handler ────────────────────────────────────────────────────────

    def _handle_direct(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        return {
            "status": "direct_response",
            "agent": "dvorah_direct",
            "response_type": "conversational",
            "requires_approval": False,
            "routing_reason": routing["classification"]["reason"],
            "confidence": routing["classification"]["confidence"],
            "response_ready": True,
            "metadata": {
                "model_tier": routing["model"],
                "context_files": routing["context"]["files_loaded"],
                "direct_processing": True,
            },
        }

    # ── QA ────────────────────────────────────────────────────────────────────

    def _qa_check(self, agent_result: Dict, routing: Dict) -> Dict:
        checks = {
            "context_overflow":       self._check_context_overflow(),
            "approval_required":      self._check_approval(agent_result),
            "response_completeness":  self._check_completeness(agent_result),
            "risk_assessment":        self._check_risk(agent_result, routing),
            "single_message":         self._check_single_message(agent_result),
        }
        passed = sum(1 for c in checks.values() if c["passed"])
        total = len(checks)

        blocking = [n for n, c in checks.items()
                    if not c["passed"] and c.get("blocking")]
        recommendations = [
            f"Fix: {n}" for n, c in checks.items()
            if not c["passed"]
        ]
        return {
            "passed": passed == total,
            "score": passed / total,
            "checks": checks,
            "blocking_issues": blocking,
            "recommendations": recommendations,
        }

    def _check_context_overflow(self) -> Dict:
        s = context_status()
        return {"name": "context_overflow", "passed": s["status"] != "critical",
                "details": s, "blocking": s["status"] == "critical"}

    def _check_approval(self, r: Dict) -> Dict:
        req = r.get("requires_approval", False)
        has_reason = bool(r.get("draft_actions", {}).get("approval_reason"))
        ok = not req or has_reason
        return {"name": "approval_required", "passed": ok,
                "details": f"approval={'required' if req else 'not required'}",
                "blocking": not ok}

    def _check_completeness(self, r: Dict) -> Dict:
        has_status = "status" in r
        has_content = any(k in r for k in
                          ["response", "analysis", "draft_actions", "summary",
                           "data_logged", "action_taken"])
        ok = has_status and has_content
        return {"name": "response_completeness", "passed": ok,
                "details": f"status={has_status}, content={has_content}",
                "blocking": not ok}

    def _check_risk(self, r: Dict, routing: Dict) -> Dict:
        domain = routing["classification"]["domain"]
        if domain == "legal":
            ok = r.get("requires_approval", False)
            return {"name": "risk_assessment", "passed": ok,
                    "details": "legal — approval required", "blocking": not ok}
        return {"name": "risk_assessment", "passed": True,
                "details": "low risk", "blocking": False}

    def _check_single_message(self, r: Dict) -> Dict:
        """PR1: response must not contain multiple messages."""
        if not SINGLE_MESSAGE_MODE:
            return {"name": "single_message", "passed": True, "details": "disabled"}
        chunks = r.get("_chunks", [])
        ok = len(chunks) <= 1
        return {"name": "single_message", "passed": ok,
                "details": f"chunks={len(chunks)}", "blocking": False}

    # ── Logging ───────────────────────────────────────────────────────────────

    def _make_record(self, execution_id: str, start: datetime,
                     message: str, channel: str, group_id: str,
                     status: str = "unknown", cost: float = 0.0,
                     tier: str = "unknown", agent: str = None,
                     qa_passed: bool = None, error: str = None) -> Dict:
        return {
            "execution_id": execution_id,
            "timestamp": start.isoformat(),
            "message": message[:80] + "…" if len(message) > 80 else message,
            "channel": channel,
            "group_id": group_id,
            "status": status,
            "tier": tier,
            "agent": agent,
            "cost_usd": cost,
            "qa_passed": qa_passed,
            "error": error,
            "duration_ms": int((datetime.now() - start).total_seconds() * 1000),
        }

    def _log_execution(self, record: Dict):
        self.execution_log.append(record)
        trace_file = (self.workspace / "state" / "traces" /
                      f"execution_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
        trace_file.parent.mkdir(exist_ok=True)
        try:
            with open(trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ── Global singleton ──────────────────────────────────────────────────────────
pipeline = ExecutionPipeline()


def execute_message(message: str, channel: str = None,
                    group_id: str = None, metadata: Dict = None) -> Dict:
    return pipeline.execute(message, channel, group_id, metadata)
