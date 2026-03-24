#!/usr/bin/env python3
"""
Cost Tracker — Token estimation, cost tracking, and reporting for Masha Advanced.
Tracks every model call with tier, tokens, cost, and provides reporting.
"""

import json
import time
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


COST_LOG_DIR = Path(os.path.expanduser("~/.openclaw/workspace/agents/legal-agent/cost_logs"))


# Cost per 1M tokens (input, output) in USD
MODEL_COSTS = {
    "anthropic/claude-sonnet-4-20250514": (3.0, 15.0),
    "anthropic/claude-opus-4-20250514": (15.0, 75.0),
    # Tier labels for convenience
    "tier1": (3.0, 15.0),
    "tier2": (3.0, 15.0),
    "tier3": (15.0, 75.0),
}

# Tokens-per-word estimates by language
TOKENS_PER_WORD = {
    "hebrew": 2.5,   # Hebrew uses more tokens per word
    "english": 1.3,
    "mixed": 1.8,
}


@dataclass
class CostRecord:
    """A single cost record for one model invocation."""
    timestamp: float
    task_type: str
    pipeline_stage: str        # intake/extract/analyze/synthesize/qa
    model_tier: str            # tier1/tier2/tier3
    model_id: str              # Full model identifier
    input_tokens: int
    output_tokens: int
    cost_usd: float
    was_cached: bool = False   # True if result came from cache
    escalated_from: Optional[str] = None  # If this was an escalation, what tier it came from
    notes: str = ""


class CostTracker:
    """
    Tracks costs across all Masha Advanced operations.
    Provides real-time cost awareness and reporting.
    """

    def __init__(self):
        COST_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._session_records: List[CostRecord] = []

    # ============================================================
    # TOKEN ESTIMATION
    # ============================================================

    @staticmethod
    def estimate_tokens(text: str, language: str = "mixed") -> int:
        """Estimate token count for a text string."""
        if not text:
            return 0
        word_count = len(text.split())
        multiplier = TOKENS_PER_WORD.get(language, 1.8)
        return int(word_count * multiplier)

    @staticmethod
    def estimate_cost(input_tokens: int, output_tokens: int, model_or_tier: str) -> float:
        """Estimate cost for a model call."""
        costs = MODEL_COSTS.get(model_or_tier, MODEL_COSTS["tier2"])
        input_cost = (input_tokens / 1_000_000) * costs[0]
        output_cost = (output_tokens / 1_000_000) * costs[1]
        return round(input_cost + output_cost, 6)

    def estimate_pipeline_cost(self, task_type: str, document_text: Optional[str], tier: str) -> Dict:
        """
        Estimate the full pipeline cost before execution.
        Helps with cost-aware decision making.
        """
        doc_tokens = self.estimate_tokens(document_text or "", "mixed")
        prompt_overhead = 2500  # System prompts, checklists, formatting

        # Stage-by-stage estimates
        stages = []

        # Stage 0: Intake (always Tier 1)
        intake_input = min(doc_tokens, 500) + 500  # Sample + message
        intake_output = 200
        stages.append({
            "stage": "intake",
            "tier": "tier1",
            "input_tokens": intake_input,
            "output_tokens": intake_output,
            "cost_usd": self.estimate_cost(intake_input, intake_output, "tier1"),
        })

        # Stage 1: Extract (always Tier 1)
        extract_input = doc_tokens + prompt_overhead
        extract_output_map = {
            "clause_extraction": 1500,
            "legal_summary": 2000,
            "contract_review": 3000,
            "risk_analysis": 2500,
            "compare_versions": 3000,
            "draft_response": 1500,
            "negotiation_prep": 2000,
        }
        extract_output = extract_output_map.get(task_type, 2000)
        stages.append({
            "stage": "extract",
            "tier": "tier1",
            "input_tokens": extract_input,
            "output_tokens": extract_output,
            "cost_usd": self.estimate_cost(extract_input, extract_output, "tier1"),
        })

        # Stage 2: Analyze (Tier 1 or determined tier)
        analyze_tier = "tier1" if tier == "tier1" else tier
        analyze_input = extract_output + prompt_overhead  # Uses extraction output
        analyze_output_map = {
            "clause_extraction": 500,    # Just tagging
            "legal_summary": 1000,
            "contract_review": 2000,
            "risk_analysis": 2500,
            "compare_versions": 2000,
            "draft_response": 1000,
            "negotiation_prep": 2000,
        }
        analyze_output = analyze_output_map.get(task_type, 1500)
        stages.append({
            "stage": "analyze",
            "tier": analyze_tier,
            "input_tokens": analyze_input,
            "output_tokens": analyze_output,
            "cost_usd": self.estimate_cost(analyze_input, analyze_output, analyze_tier),
        })

        # Stage 3: Synthesize (only if tier2+)
        if tier in ("tier2", "tier3"):
            synth_tier = tier
            synth_input = analyze_output + extract_output + prompt_overhead
            synth_output_map = {
                "contract_review": 4000,
                "risk_analysis": 3000,
                "draft_response": 5000,
                "negotiation_prep": 6000,
                "compare_versions": 3500,
                "legal_summary": 2000,
                "clause_extraction": 1500,
            }
            synth_output = synth_output_map.get(task_type, 3000)
            stages.append({
                "stage": "synthesize",
                "tier": synth_tier,
                "input_tokens": synth_input,
                "output_tokens": synth_output,
                "cost_usd": self.estimate_cost(synth_input, synth_output, synth_tier),
            })

        # Stage 4: QA (always Tier 1)
        qa_input = sum(s["output_tokens"] for s in stages) + 500
        qa_output = 300
        stages.append({
            "stage": "qa",
            "tier": "tier1",
            "input_tokens": qa_input,
            "output_tokens": qa_output,
            "cost_usd": self.estimate_cost(qa_input, qa_output, "tier1"),
        })

        total_cost = sum(s["cost_usd"] for s in stages)
        total_input = sum(s["input_tokens"] for s in stages)
        total_output = sum(s["output_tokens"] for s in stages)

        return {
            "stages": stages,
            "total_cost_usd": round(total_cost, 4),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "primary_tier": tier,
            "opus_equivalent_cost": self.estimate_cost(
                total_input, total_output, "tier3"
            ),
            "savings_vs_opus_pct": round(
                (1 - total_cost / max(self.estimate_cost(total_input, total_output, "tier3"), 0.001)) * 100, 1
            ),
        }

    # ============================================================
    # RECORDING
    # ============================================================

    def record_from_response(
        self,
        task_type: str,
        pipeline_stage: str,
        model_tier: str,
        response,  # ModelResponse from model_client
        escalated_from: Optional[str] = None,
        notes: str = "",
    ) -> "CostRecord":
        """Record from a real ModelResponse object (live API usage)."""
        return self.record(
            task_type=task_type,
            pipeline_stage=pipeline_stage,
            model_tier=model_tier,
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            was_cached=False,
            escalated_from=escalated_from,
            notes=notes,
        )

    def record(
        self,
        task_type: str,
        pipeline_stage: str,
        model_tier: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        was_cached: bool = False,
        escalated_from: Optional[str] = None,
        notes: str = "",
    ) -> "CostRecord":
        """Record a model invocation."""
        cost = 0.0 if was_cached else self.estimate_cost(input_tokens, output_tokens, model_tier)

        record = CostRecord(
            timestamp=time.time(),
            task_type=task_type,
            pipeline_stage=pipeline_stage,
            model_tier=model_tier,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            was_cached=was_cached,
            escalated_from=escalated_from,
            notes=notes,
        )

        self._session_records.append(record)
        self._persist_record(record)
        return record

    def _persist_record(self, record: CostRecord):
        """Append record to daily log file."""
        date_str = time.strftime("%Y-%m-%d")
        log_file = COST_LOG_DIR / f"costs_{date_str}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    # ============================================================
    # REPORTING
    # ============================================================

    def session_summary(self) -> Dict:
        """Get cost summary for current session."""
        if not self._session_records:
            return {"total_cost_usd": 0, "total_calls": 0, "by_tier": {}}

        total_cost = sum(r.cost_usd for r in self._session_records)
        by_tier = {}
        by_stage = {}

        for r in self._session_records:
            by_tier[r.model_tier] = by_tier.get(r.model_tier, 0) + r.cost_usd
            by_stage[r.pipeline_stage] = by_stage.get(r.pipeline_stage, 0) + r.cost_usd

        cache_hits = sum(1 for r in self._session_records if r.was_cached)
        escalations = sum(1 for r in self._session_records if r.escalated_from)

        return {
            "total_cost_usd": round(total_cost, 4),
            "total_calls": len(self._session_records),
            "cache_hits": cache_hits,
            "escalations": escalations,
            "by_tier": {k: round(v, 4) for k, v in by_tier.items()},
            "by_stage": {k: round(v, 4) for k, v in by_stage.items()},
        }

    def daily_report(self, date_str: Optional[str] = None) -> Dict:
        """Generate daily cost report from log files."""
        date_str = date_str or time.strftime("%Y-%m-%d")
        log_file = COST_LOG_DIR / f"costs_{date_str}.jsonl"

        if not log_file.exists():
            return {"date": date_str, "total_cost_usd": 0, "total_calls": 0}

        records = []
        for line in log_file.read_text().strip().split("\n"):
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        total_cost = sum(r["cost_usd"] for r in records)
        by_tier = {}
        by_task = {}

        for r in records:
            tier = r["model_tier"]
            task = r["task_type"]
            by_tier[tier] = by_tier.get(tier, 0) + r["cost_usd"]
            by_task[task] = by_task.get(task, 0) + r["cost_usd"]

        # Calculate tier distribution
        total_calls = len(records)
        tier_distribution = {}
        for tier in by_tier:
            tier_calls = sum(1 for r in records if r["model_tier"] == tier)
            tier_distribution[tier] = round(tier_calls / max(total_calls, 1) * 100, 1)

        return {
            "date": date_str,
            "total_cost_usd": round(total_cost, 4),
            "total_calls": total_calls,
            "by_tier": {k: round(v, 4) for k, v in by_tier.items()},
            "by_task_type": {k: round(v, 4) for k, v in by_task.items()},
            "tier_distribution_pct": tier_distribution,
            "cache_hits": sum(1 for r in records if r.get("was_cached")),
            "escalations": sum(1 for r in records if r.get("escalated_from")),
        }

    def format_cost_report(self, report: Dict) -> str:
        """Format a cost report as readable text."""
        lines = [
            f"# 💰 Masha Cost Report — {report.get('date', 'Session')}",
            "",
            f"**Total Cost:** ${report['total_cost_usd']:.4f}",
            f"**Total Calls:** {report['total_calls']}",
        ]

        if report.get("cache_hits"):
            lines.append(f"**Cache Hits:** {report['cache_hits']} (saved ${report.get('estimated_savings', 0):.4f})")

        if report.get("by_tier"):
            lines.append("\n## By Tier")
            for tier, cost in report["by_tier"].items():
                pct = report.get("tier_distribution_pct", {}).get(tier, "?")
                lines.append(f"- **{tier}:** ${cost:.4f} ({pct}% of calls)")

        if report.get("by_task_type"):
            lines.append("\n## By Task Type")
            for task, cost in sorted(report["by_task_type"].items(), key=lambda x: -x[1]):
                lines.append(f"- **{task}:** ${cost:.4f}")

        return "\n".join(lines)


def test_cost_tracker():
    """Test cost tracking."""
    tracker = CostTracker()

    # Estimate tokens
    tokens = tracker.estimate_tokens("This is a sample contract with many clauses." * 100)
    print(f"Estimated tokens: {tokens}")

    # Estimate pipeline cost
    estimate = tracker.estimate_pipeline_cost(
        task_type="contract_review",
        document_text="Contract text " * 2000,
        tier="tier1",
    )
    print(f"\nPipeline estimate:")
    print(f"  Total cost: ${estimate['total_cost_usd']:.4f}")
    print(f"  Opus equivalent: ${estimate['opus_equivalent_cost']:.4f}")
    print(f"  Savings vs Opus: {estimate['savings_vs_opus_pct']}%")
    for stage in estimate["stages"]:
        print(f"  {stage['stage']}: {stage['tier']} — ${stage['cost_usd']:.4f}")

    # Record some calls
    tracker.record("contract_review", "intake", "tier1", "anthropic/claude-sonnet-4-20250514", 1000, 200)
    tracker.record("contract_review", "extract", "tier1", "anthropic/claude-sonnet-4-20250514", 5000, 3000)
    tracker.record("contract_review", "analyze", "tier2", "anthropic/claude-sonnet-4-20250514", 4000, 2000)

    print(f"\nSession summary: {json.dumps(tracker.session_summary(), indent=2)}")


if __name__ == "__main__":
    test_cost_tracker()
