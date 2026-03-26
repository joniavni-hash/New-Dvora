#!/usr/bin/env python3
"""
Agent Executor — PR1: Cost + Output Enforcement

Changes:
- NO_REPLY action exits immediately with $0 cost
- tier3 (Opus) blocked without explicit justification
- Max output tokens enforced per tier
- No simulated token logging (zero cost until real model call exists)
- No progress messages
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from model_selector import ModelSelector, OpusBlockedError, DailyCostExceededError, MAX_OUTPUT_TOKENS


class AgentExecutor:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get(
            "DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
        sys.path.insert(0, str(self.workspace))

    def execute_agent_task(self, agent_name: str, message: str,
                           routing_result: Dict, metadata: Dict = None) -> Dict:
        """
        Execute agent task.

        PR1: NO_REPLY fast-path checked first — exits before any model call.
        """
        metadata = metadata or {}

        # ── PR1: NO_REPLY fast-path ───────────────────────────────────────────
        action = routing_result.get("routing_decision", {}).get("action", "")
        if action == "no_reply" or agent_name == "no_reply":
            return {
                "status": "no_reply",
                "agent": "no_reply",
                "cost_usd": 0.0,
                "model_tier": "none",
                "reason": "NO_REPLY fast-path: trivial group message",
                "pr1_enforcement": "no_reply_before_model_call",
            }

        try:
            if agent_name == "masha":
                return self._execute_masha(message, routing_result, metadata)
            elif agent_name == "dana":
                return self._execute_dana(message, routing_result, metadata)
            elif agent_name == "odya":
                return self._execute_odya(message, routing_result, metadata)
            elif agent_name == "tzofit":
                return self._execute_tzofit(message, routing_result, metadata)
            else:
                return self._execute_fallback(agent_name, message, routing_result)

        except OpusBlockedError as e:
            return {
                "status": "blocked",
                "agent": agent_name,
                "reason": str(e),
                "fallback": "Downgraded to tier2 — retry with tier2",
                "pr1_enforcement": "opus_blocked",
            }
        except DailyCostExceededError as e:
            return {
                "status": "blocked",
                "agent": agent_name,
                "reason": str(e),
                "pr1_enforcement": "daily_cost_cap",
            }
        except Exception as e:
            return {
                "status": "execution_error",
                "agent": agent_name,
                "error": str(e),
                "fallback_action": "manual_review_required",
            }

    # ── Agent handlers ────────────────────────────────────────────────────────

    def _execute_masha(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """
        Legal task via מאשה.

        PR1: Default tier = tier2 (not tier3).
        Opus escalation only with valid justification.
        """
        tier = routing.get("model", "tier2")   # PR1: was tier3

        # Determine if Opus is justified for this task
        opus_justification = self._assess_legal_complexity(message)
        if tier == "tier3" and not opus_justification:
            tier = "tier2"   # Downgrade — no justification

        model_selection = ModelSelector(str(self.workspace)).select_model(
            tier, routing["context"], opus_justification
        )

        from agents.masha.masha_agent import handle_legal_task
        agent_response = handle_legal_task(message, {
            "routing": routing,
            "metadata": metadata,
        })

        # NOTE: actual_tokens = None until real model call exists
        # Do NOT simulate tokens — that was causing inflated cost logs
        agent_response["execution_details"] = {
            "model_used": model_selection["model_id"],
            "tier": model_selection["tier"],
            "max_output_tokens": model_selection["max_output_tokens"],
            "opus_justification": opus_justification,
            "cost_usd": 0.0,   # real value populated after actual model call
            "note": "cost=0 until real model call implemented",
        }
        return agent_response

    def _execute_dana(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Fitness task — tier1 always."""
        tier = "tier1"
        model_selection = ModelSelector(str(self.workspace)).select_model(
            tier, routing["context"]
        )

        fitness_data = self._parse_fitness_message(message)

        if fitness_data["type"] in ("meal", "weight"):
            self._update_fitness_tracker(fitness_data)
            return {
                "status": "executed",
                "agent": "דנה",
                "domain": "fitness",
                "action_taken": f"Updated {fitness_data['type']} data",
                "data_logged": fitness_data,
                "file_updated": "state/fitness_tracker.md",
                "execution_details": {
                    "model_used": model_selection["model_id"],
                    "tier": tier,
                    "max_output_tokens": model_selection["max_output_tokens"],
                    "cost_usd": 0.0,
                },
                "summary": f"רשמתי {fitness_data.get('description','נתונים')} במעקב הכושר",
            }

        return {
            "status": "no_action_needed",
            "agent": "דנה",
            "reason": "No fitness data detected",
        }

    def _execute_odya(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """
        Group message — tier1 only, NO_REPLY checked first.

        PR1: Never escalate group triage to tier2/tier3.
        """
        tier = "tier1"
        model_selection = ModelSelector(str(self.workspace)).select_model(
            tier, routing["context"]
        )

        group_id = (metadata or {}).get("group_id")
        analysis = self._analyze_group_message(message, group_id)

        return {
            "status": "analysis_ready",
            "agent": "אודיה",
            "domain": "whatsapp_group",
            "analysis": analysis,
            "requires_approval": True,
            "execution_details": {
                "model_used": model_selection["model_id"],
                "tier": tier,
                "max_output_tokens": model_selection["max_output_tokens"],
                "cost_usd": 0.0,
                "pr1_enforcement": "group_tier1_only",
            },
        }

    def _execute_tzofit(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Research — tier2."""
        tier = "tier2"
        model_selection = ModelSelector(str(self.workspace)).select_model(
            tier, routing["context"]
        )

        return {
            "status": "research_ready",
            "agent": "צופית",
            "domain": "research",
            "query": self._extract_research_query(message),
            "results": {"status": "pending_implementation"},
            "execution_details": {
                "model_used": model_selection["model_id"],
                "tier": tier,
                "max_output_tokens": model_selection["max_output_tokens"],
                "cost_usd": 0.0,
            },
        }

    def _execute_fallback(self, agent_name: str, message: str, routing: Dict) -> Dict:
        return {
            "status": "not_implemented",
            "agent": agent_name,
            "message": f"Agent {agent_name} not implemented",
            "fallback_action": "handle_as_direct",
        }

    # ── Legal complexity assessment ───────────────────────────────────────────

    def _assess_legal_complexity(self, message: str) -> Optional[str]:
        """
        Returns an Opus justification string only for genuinely complex legal tasks.
        Otherwise returns None (stay at tier2).
        """
        msg = message.lower()
        if any(k in msg for k in ["multi.*party", "complex.*structure", "international"]):
            return "multi_party_contract_review"
        if "explicit.*opus" in msg:
            return "explicit_user_request_opus"
        return None   # default: no escalation

    # ── Fitness helpers ───────────────────────────────────────────────────────

    def _parse_fitness_message(self, message: str) -> Dict:
        msg = message.lower()
        if any(w in msg for w in ["אכלתי", "ארוחה", "meal", "ate"]):
            return {"type": "meal", "description": message,
                    "timestamp": datetime.now().isoformat()}
        if any(w in msg for w in ["שקלתי", "משקל", "weight"]):
            return {"type": "weight", "description": message,
                    "timestamp": datetime.now().isoformat()}
        return {"type": "unknown", "description": message}

    def _update_fitness_tracker(self, fitness_data: Dict) -> Dict:
        try:
            tracker = self.workspace / "state" / "fitness_tracker.md"
            content = tracker.read_text(encoding="utf-8") if tracker.exists() else ""
            entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{fitness_data['description']}\n"
            tracker.write_text(content + entry, encoding="utf-8")
            return {"status": "updated"}
        except Exception as e:
            return {"status": "update_failed", "error": str(e)}

    # ── Group helpers ─────────────────────────────────────────────────────────

    def _analyze_group_message(self, message: str, group_id: str = None) -> Dict:
        msg = message.lower()
        should_respond = any(w in msg for w in
                             ["דבורה", "dvorah", "?", "מי", "איך", "מה", "כמה"])
        return {
            "should_respond": should_respond,
            "confidence": 0.7 if should_respond else 0.3,
            "message_type": "question" if "?" in message else "statement",
            "mentions_dvorah": "דבורה" in msg or "dvorah" in msg,
            "group_id": group_id,
        }

    # ── Research helpers ──────────────────────────────────────────────────────

    def _extract_research_query(self, message: str) -> str:
        for indicator in ["תחקרי", "חקרי", "בדקי", "מצאי"]:
            if indicator in message:
                parts = message.split(indicator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return message


# ── Global singleton ──────────────────────────────────────────────────────────
agent_executor = AgentExecutor()


def execute_agent_task(agent_name: str, message: str,
                       routing_result: Dict, metadata: Dict = None) -> Dict:
    return agent_executor.execute_agent_task(
        agent_name, message, routing_result, metadata
    )
