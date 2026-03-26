#!/usr/bin/env python3
"""
Agent Executor — PR2: Thin dispatch wrapper.

PR2: this file no longer contains per-agent logic.
It calls agent_registry.dispatch() and returns FinalPayload.
Dvorah (execution_pipeline) receives FinalPayload and handles:
  QA | approval | delivery | fallback
"""

import os
import sys
from pathlib import Path
from typing import Dict

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "agents" / "_shared"))
sys.path.insert(0, str(WORKSPACE / "core"))

from domain_agent_base import FinalPayload
from model_selector import OpusBlockedError, DailyCostExceededError

# Lazy import to avoid circular deps at module load
_registry = None


def _get_registry():
    global _registry
    if _registry is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_registry",
            str(WORKSPACE / "agents" / "_shared" / "agent_registry.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _registry = mod
    return _registry


class AgentExecutor:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or WORKSPACE)

    def execute_agent_task(self, agent_name: str, message: str,
                           routing_result: Dict,
                           metadata: Dict = None) -> FinalPayload:
        """
        PR2: single entry point.
        Delegates entirely to agent_registry.dispatch().
        Returns FinalPayload. Never rewrites it.
        """
        metadata = metadata or {}

        # PR1 guard: NO_REPLY fast-path
        action = routing_result.get("routing_decision", {}).get("action", "")
        if action == "no_reply" or agent_name == "no_reply":
            return FinalPayload(
                status="no_reply",
                agent="no_reply",
                final_text="",
                should_send=False,
                requires_approval=False,
                metadata={
                    "model_used":   "none",
                    "model_reason": "NO_REPLY fast-path (PR1)",
                    "output_mode":  "no_reply",
                },
            )

        try:
            registry = _get_registry()
            context = {
                "routing": routing_result,
                **metadata,
            }
            payload = registry.dispatch(agent_name, message, context, metadata)
            return payload

        except OpusBlockedError as e:
            return FinalPayload(
                status="error",
                agent=agent_name,
                final_text="",
                should_send=False,
                requires_approval=False,
                metadata={
                    "model_used":   "none",
                    "model_reason": f"OpusBlocked: {e}",
                    "output_mode":  "error",
                    "pr1_enforcement": "opus_blocked",
                },
            )
        except DailyCostExceededError as e:
            return FinalPayload(
                status="error",
                agent=agent_name,
                final_text="",
                should_send=False,
                requires_approval=False,
                metadata={
                    "model_used":   "none",
                    "model_reason": f"DailyCap: {e}",
                    "output_mode":  "error",
                    "pr1_enforcement": "daily_cost_cap",
                },
            )
        except Exception as e:
            return FinalPayload(
                status="error",
                agent=agent_name,
                final_text="",
                should_send=False,
                requires_approval=False,
                metadata={
                    "model_used":   "none",
                    "model_reason": f"executor error: {e}",
                    "output_mode":  "error",
                },
            )


# ── Global singleton ──────────────────────────────────────────────────────────
agent_executor = AgentExecutor()


def execute_agent_task(agent_name: str, message: str,
                       routing_result: Dict,
                       metadata: Dict = None) -> FinalPayload:
    return agent_executor.execute_agent_task(
        agent_name, message, routing_result, metadata
    )
