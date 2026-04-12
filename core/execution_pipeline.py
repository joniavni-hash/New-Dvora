#!/usr/bin/env python3
"""
Execution Pipeline — PR2: Dvorah as governor only.

Dvorah's role post-PR2:
  1. Daily cost gate
  2. Route (NO_REPLY fast-path)
  3. Dispatch to agent via agent_executor
  4. Receive FinalPayload — do NOT rewrite final_text
  5. QA (validate payload contract)
  6. Approval gate (if requires_approval)
  7. Write actions (files, state)
  8. Delivery
  9. Fallback if status=error

PR1 enforcements (unchanged): output cap, single_message_mode, daily cost.
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
    ModelSelector, MAX_OUTPUT_TOKENS, MAX_DAILY_COST_USD
)
from domain_agent_base import FinalPayload   # type: ignore

SINGLE_MESSAGE_MODE = True
NO_PROGRESS_MESSAGES = True


def enforce_output_length(text: str, tier: str) -> str:
    if not text or tier == "none":
        return text
    max_chars = MAX_OUTPUT_TOKENS.get(tier, 400) * 4
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
        start   = datetime.now()
        exec_id = f"exec_{start.strftime('%Y%m%d_%H%M%S')}_{id(message)}"
        metadata = metadata or {}

        try:
            # ── 1. Daily cost gate ────────────────────────────────────────────
            ms = ModelSelector(str(self.workspace))
            today = ms._get_today_cost()
            if today >= MAX_DAILY_COST_USD:
                rec = self._make_record(exec_id, start, message, channel,
                                        group_id, status="blocked_daily_cost")
                self._log(rec)
                return {"status": "blocked", "execution_id": exec_id,
                        "reason": f"Daily cap ${MAX_DAILY_COST_USD} (today=${today:.4f})",
                        "pr1_enforcement": "daily_cost_cap"}

            # ── 2. Route ──────────────────────────────────────────────────────
            routing = route_message(message, channel, group_id)

            # ── 3. NO_REPLY fast-path ─────────────────────────────────────────
            if routing["routing_decision"]["action"] == "no_reply":
                rec = self._make_record(exec_id, start, message, channel,
                                        group_id, status="no_reply",
                                        cost=0.0, tier="none")
                self._log(rec)
                return {"status": "no_reply", "execution_id": exec_id,
                        "cost_usd": 0.0, "pr1_enforcement": "no_reply_fast_path",
                        "execution_summary": rec}

            # ── Context guard ─────────────────────────────────────────────────
            ctx = context_status()
            if ctx["status"] == "critical":
                emergency_compact()

            # ── 4. Dispatch to agent ──────────────────────────────────────────
            agent_name = routing["routing_decision"]["agent"]
            tier       = routing.get("model", "tier2")

            if routing["routing_decision"]["action"] == "handle_direct":
                payload = self._direct_payload(message, routing)
            else:
                payload = self.agent_executor.execute_agent_task(
                    agent_name, message, routing,
                    {**metadata, "execution_id": exec_id}
                )

            # ── 5. Dvorah does NOT rewrite — only enforces output cap (PR1) ──
            if isinstance(payload, FinalPayload):
                payload.final_text = enforce_output_length(
                    payload.final_text, tier
                )
            else:
                # Shouldn't happen — fallback
                payload = self._error_payload(agent_name, "non-FinalPayload returned")

            # ── 6. QA gate ────────────────────────────────────────────────────
            qa = self._qa(payload, routing)

            # ── 7. Write actions ──────────────────────────────────────────────
            if payload.status not in ("error", "no_reply"):
                self._apply_write_actions(payload.write_actions)

            # ── 8. Approval gate + delivery ───────────────────────────────────
            # Convert FinalPayload to dict expected by legacy action_executor
            agent_dict = {**payload.to_dict(),
                          "requires_approval": payload.requires_approval,
                          "draft_actions": {
                              "approval_reason": "agent requires approval"
                              if payload.requires_approval else ""
                          }}
            exec_result = execute_if_approved(agent_dict, qa, channel)
            resp_result = send_response_if_ready(
                exec_result, channel, metadata.get("sender_id")
            )

            # ── 9. Log ────────────────────────────────────────────────────────
            cost = payload.metadata.get("cost_usd", 0.0) if hasattr(payload, "metadata") else 0.0
            rec  = self._make_record(exec_id, start, message, channel, group_id,
                                     status=payload.status, cost=cost, tier=tier,
                                     agent=agent_name, qa_passed=qa["passed"])
            self._log(rec)

            return {
                "status":           "success",
                "execution_id":     exec_id,
                "routing":          routing,
                "agent_payload":    payload.to_dict(),
                "qa_result":        qa,
                "execution_result": exec_result,
                "response_result":  resp_result,
                "execution_summary": rec,
            }

        except Exception as e:
            rec = self._make_record(exec_id, start, message, channel,
                                    group_id, status="error", error=str(e))
            self._log(rec)
            return {"status": "error", "execution_id": exec_id,
                    "error": str(e), "execution_summary": rec}

    # ── Direct handler (Dvorah handles, no agent) ─────────────────────────────

    def _direct_payload(self, message: str, routing: Dict) -> FinalPayload:
        return FinalPayload(
            status="ok",
            agent="דבורה",
            final_text="",          # Dvorah generates in LLM turn, not here
            should_send=True,
            requires_approval=False,
            metadata={
                "model_used":   "anthropic/claude-sonnet-4-20250514",
                "model_reason": "direct/general — Dvorah handles",
                "output_mode":  "direct_send",
                "routing_reason": routing["classification"]["reason"],
            },
        )

    def _error_payload(self, agent: str, reason: str) -> FinalPayload:
        return FinalPayload(
            status="error", agent=agent, final_text="",
            should_send=False, requires_approval=False,
            metadata={"model_used": "none", "model_reason": reason,
                      "output_mode": "error"},
        )

    # ── QA ────────────────────────────────────────────────────────────────────

    def _qa(self, payload: FinalPayload, routing: Dict) -> Dict:
        checks = {}

        # Contract check
        required = ["status", "agent", "final_text", "should_send",
                    "requires_approval", "write_actions", "metadata"]
        missing = [k for k in required if not hasattr(payload, k)]
        checks["contract"] = {
            "passed": len(missing) == 0,
            "details": f"missing: {missing}" if missing else "ok",
            "blocking": len(missing) > 0,
        }

        # Metadata keys
        meta_keys = ["model_used", "model_reason", "output_mode"]
        meta_missing = [k for k in meta_keys
                        if k not in (payload.metadata or {})]
        checks["metadata_contract"] = {
            "passed": len(meta_missing) == 0,
            "details": f"missing meta: {meta_missing}" if meta_missing else "ok",
            "blocking": False,
        }

        # Legal approval gate
        if routing["classification"]["domain"] == "legal":
            checks["legal_approval"] = {
                "passed": payload.requires_approval,
                "details": "legal must require approval",
                "blocking": not payload.requires_approval,
            }

        # Context overflow
        ctx = context_status()
        checks["context"] = {
            "passed": ctx["status"] != "critical",
            "details": ctx["status"],
            "blocking": ctx["status"] == "critical",
        }

        passed = sum(1 for c in checks.values() if c["passed"])
        total  = len(checks)
        blocking = [n for n, c in checks.items()
                    if not c["passed"] and c.get("blocking")]
        recs     = [f"Fix: {n}" for n, c in checks.items() if not c["passed"]]

        return {
            "passed":          passed == total,
            "score":           passed / total,
            "checks":          checks,
            "blocking_issues": blocking,
            "recommendations": recs,
        }

    # ── Write actions ─────────────────────────────────────────────────────────

    def _apply_write_actions(self, actions: List[Dict]):
        for act in (actions or []):
            try:
                path = self.workspace / act["path"]
                if act["type"] == "append_file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(act["content"])
                elif act["type"] == "write_file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(act["content"], encoding="utf-8")
            except Exception:
                pass   # fail silently — don't break execution for I/O

    # ── Logging ───────────────────────────────────────────────────────────────

    def _make_record(self, execution_id, start, message, channel, group_id,
                     status="unknown", cost=0.0, tier="unknown",
                     agent=None, qa_passed=None, error=None) -> Dict:
        return {
            "execution_id": execution_id,
            "timestamp":    start.isoformat(),
            "message":      message[:80] + "…" if len(message) > 80 else message,
            "channel":      channel,
            "group_id":     group_id,
            "status":       status,
            "tier":         tier,
            "agent":        agent,
            "cost_usd":     cost,
            "qa_passed":    qa_passed,
            "error":        error,
            "duration_ms":  int((datetime.now() - start).total_seconds() * 1000),
        }

    def _log(self, record: Dict):
        self.execution_log.append(record)
        trace = (self.workspace / "state" / "traces" /
                 f"execution_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
        trace.parent.mkdir(exist_ok=True)
        try:
            with open(trace, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ── Global singleton ──────────────────────────────────────────────────────────
pipeline = ExecutionPipeline()


def execute_message(message: str, channel: str = None,
                    group_id: str = None, metadata: Dict = None) -> Dict:
    return pipeline.execute(message, channel, group_id, metadata)
