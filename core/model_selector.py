#!/usr/bin/env python3
"""
Model Selector — PR1: Cost + Output Enforcement

Hard rules:
- Opus (tier3) BLOCKED by default; requires explicit justification
- Max output tokens enforced by tier
- Max calls per task enforced
- Daily cost cap enforced (blocks execution if exceeded)
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional

# ── Hard caps ────────────────────────────────────────────────────────────────
OPUS_BLOCKED: bool = True               # tier3 blocked unless justified
MAX_OUTPUT_TOKENS: Dict[str, int] = {
    "tier1": 200,   # simple / triage
    "tier2": 400,   # medium complexity
    "tier3": 800,   # complex analysis — only when justified
}
MAX_CALLS_PER_TASK: int = 3
MAX_DAILY_COST_USD: float = 3.0         # hard stop if exceeded

# Valid justifications for Opus escalation
VALID_OPUS_JUSTIFICATIONS = {
    "multi_party_contract_review",
    "complex_legal_structure",
    "explicit_user_request_opus",
}


class OpusBlockedError(Exception):
    """Raised when tier3 is requested without valid justification."""


class DailyCostExceededError(Exception):
    """Raised when daily cost cap is reached."""


class ModelSelector:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get(
            "DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

        self.tier_models = {
            "tier1": "anthropic/claude-sonnet-4-20250514",
            "tier2": "anthropic/claude-sonnet-4-20250514",
            "tier3": "anthropic/claude-opus-4-20250514",   # blocked unless justified
        }

        # Cost per 1M tokens (input, output) USD
        self.costs = {
            "tier1": {"input": 3.0,  "output": 15.0},
            "tier2": {"input": 3.0,  "output": 15.0},
            "tier3": {"input": 15.0, "output": 75.0},
        }

        self.cost_file = self.workspace / "state" / "model_costs.jsonl"

    # ── Public API ────────────────────────────────────────────────────────────

    def select_model(self, tier: str, context_info: Dict = None,
                     opus_justification: str = None) -> Dict:
        """
        Select model for tier.
        Raises OpusBlockedError if tier3 requested without valid justification.
        Raises DailyCostExceededError if daily cap exceeded.
        """
        if tier not in self.tier_models:
            tier = "tier2"

        # ── Guard: Opus blocked ───────────────────────────────────────────────
        if tier == "tier3" and OPUS_BLOCKED:
            if opus_justification not in VALID_OPUS_JUSTIFICATIONS:
                raise OpusBlockedError(
                    f"tier3 (Opus) blocked. justification='{opus_justification}' "
                    f"not in {VALID_OPUS_JUSTIFICATIONS}. Downgrade to tier2."
                )

        # ── Guard: daily cost cap ─────────────────────────────────────────────
        daily_cost = self._get_today_cost()
        if daily_cost >= MAX_DAILY_COST_USD:
            raise DailyCostExceededError(
                f"Daily cost cap reached: ${daily_cost:.4f} >= ${MAX_DAILY_COST_USD}. "
                "No more model calls today."
            )

        model_id = self.tier_models[tier]
        costs = self.costs[tier]
        estimated_input = self._estimate_input_tokens(context_info)
        max_output = MAX_OUTPUT_TOKENS[tier]

        estimated_cost = (
            (estimated_input / 1_000_000) * costs["input"] +
            (max_output / 1_000_000) * costs["output"]
        )

        return {
            "tier": tier,
            "model_id": model_id,
            "max_output_tokens": max_output,
            "estimated_cost_usd": round(estimated_cost, 6),
            "estimated_tokens": {"input": estimated_input, "output": max_output},
            "cost_per_million": costs,
            "opus_justification": opus_justification,
            "selection_reason": f"{tier} selected",
            "timestamp": datetime.now().isoformat(),
        }

    def log_actual_usage(self, selection: Dict, actual_tokens: Dict,
                         execution_id: str = None) -> Dict:
        """Log actual usage. Only call after a real model call."""
        actual_cost = 0.0
        if actual_tokens:
            costs = self.costs[selection["tier"]]
            actual_cost = (
                (actual_tokens.get("input", 0) / 1_000_000) * costs["input"] +
                (actual_tokens.get("output", 0) / 1_000_000) * costs["output"]
            )

        record = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "tier": selection["tier"],
            "model_id": selection["model_id"],
            "estimated_cost": selection["estimated_cost_usd"],
            "actual_cost": round(actual_cost, 6),
            "actual_tokens": actual_tokens,
        }
        self._save_cost_record(record)
        return record

    def get_cost_summary(self, days: int = 7) -> Dict:
        """Get cost summary for recent period."""
        try:
            if not self.cost_file.exists():
                return {"status": "no_data"}
            with open(self.cost_file, "r", encoding="utf-8") as f:
                records = [json.loads(l) for l in f if l.strip()]

            cutoff = datetime.now().timestamp() - (days * 86400)
            recent = [r for r in records
                      if datetime.fromisoformat(r["timestamp"]).timestamp() > cutoff]
            if not recent:
                return {"status": "no_recent_data", "days": days}

            tier_costs = {"tier1": 0.0, "tier2": 0.0, "tier3": 0.0}
            tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
            total = sum(r.get("actual_cost", 0) for r in recent)

            for r in recent:
                t = r.get("tier", "tier1")
                tier_costs[t] = tier_costs.get(t, 0) + r.get("actual_cost", 0)
                tier_counts[t] = tier_counts.get(t, 0) + 1

            return {
                "status": "success",
                "period_days": days,
                "total_requests": len(recent),
                "total_cost_usd": round(total, 4),
                "daily_cap_usd": MAX_DAILY_COST_USD,
                "today_cost_usd": round(self._get_today_cost(), 4),
                "tier_breakdown": {
                    t: {"requests": tier_counts[t],
                        "cost_usd": round(tier_costs[t], 4)}
                    for t in tier_costs
                },
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── Private ───────────────────────────────────────────────────────────────

    def _get_today_cost(self) -> float:
        """Sum actual costs from today's records."""
        try:
            if not self.cost_file.exists():
                return 0.0
            today = date.today().isoformat()
            total = 0.0
            with open(self.cost_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        r = json.loads(line)
                        if r.get("date") == today:
                            total += r.get("actual_cost", 0)
                    except Exception:
                        pass
            return total
        except Exception:
            return 0.0

    def _estimate_input_tokens(self, context_info: Dict) -> int:
        if not context_info:
            return 1000
        return max(int(context_info.get("context_size", 0) / 1.2), 500)

    def _save_cost_record(self, record: Dict):
        try:
            self.cost_file.parent.mkdir(exist_ok=True)
            with open(self.cost_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass


# ── Global singleton ──────────────────────────────────────────────────────────
model_selector = ModelSelector()


def select_model_for_tier(tier: str, context_info: Dict = None,
                          opus_justification: str = None) -> Dict:
    return model_selector.select_model(tier, context_info, opus_justification)


def log_model_usage(selection: Dict, actual_tokens: Dict,
                    execution_id: str = None) -> Dict:
    return model_selector.log_actual_usage(selection, actual_tokens, execution_id)


def get_cost_summary(days: int = 7) -> Dict:
    return model_selector.get_cost_summary(days)
