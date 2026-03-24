#!/usr/bin/env python3
"""
Model Selector - Maps tiers to actual OpenClaw models with cost tracking.

Implements the cost optimization strategy:
- Tier 1 (70-85%): Sonnet (cheap)
- Tier 2 (10-25%): Sonnet enhanced
- Tier 3 (5-10%): Opus (expensive)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

class ModelSelector:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        
        # Model configuration
        self.tier_models = {
            "tier1": "anthropic/claude-sonnet-4-20250514",
            "tier2": "anthropic/claude-sonnet-4-20250514", 
            "tier3": "anthropic/claude-opus-4-20250514"
        }
        
        # Cost per 1M tokens (input, output) in USD
        self.costs = {
            "tier1": {"input": 3.0, "output": 15.0},
            "tier2": {"input": 3.0, "output": 15.0}, 
            "tier3": {"input": 15.0, "output": 75.0}
        }
        
        # Cost tracking
        self.cost_log = []
        self.cost_file = self.workspace / "state" / "model_costs.jsonl"
        
    def select_model(self, tier: str, context_info: Dict = None) -> Dict:
        """Select model based on tier with cost estimation"""
        
        if tier not in self.tier_models:
            tier = "tier2"  # Fallback to mid-tier
            
        model_id = self.tier_models[tier]
        costs = self.costs[tier]
        
        # Estimate tokens from context info
        estimated_input_tokens = self._estimate_input_tokens(context_info)
        estimated_output_tokens = self._estimate_output_tokens(tier)
        
        # Calculate estimated cost
        estimated_cost = (
            (estimated_input_tokens / 1_000_000) * costs["input"] +
            (estimated_output_tokens / 1_000_000) * costs["output"]
        )
        
        selection = {
            "tier": tier,
            "model_id": model_id,
            "estimated_cost_usd": round(estimated_cost, 6),
            "estimated_tokens": {
                "input": estimated_input_tokens,
                "output": estimated_output_tokens
            },
            "cost_per_million": costs,
            "selection_reason": f"{tier} selected for complexity/domain routing",
            "timestamp": datetime.now().isoformat()
        }
        
        return selection
    
    def _estimate_input_tokens(self, context_info: Dict) -> int:
        """Estimate input tokens from context"""
        if not context_info:
            return 1000  # Default estimate
            
        context_size = context_info.get("context_size", 0)
        # Conservative estimate: 1.2 chars per token
        return max(int(context_size / 1.2), 500)
    
    def _estimate_output_tokens(self, tier: str) -> int:
        """Estimate output tokens by tier"""
        estimates = {
            "tier1": 200,   # Simple responses
            "tier2": 500,   # Medium complexity
            "tier3": 1000   # Complex analysis
        }
        return estimates.get(tier, 500)
    
    def log_actual_usage(self, selection: Dict, actual_tokens: Dict, 
                        execution_id: str = None) -> Dict:
        """Log actual model usage for cost tracking"""
        
        actual_cost = 0
        if actual_tokens:
            costs = self.costs[selection["tier"]]
            actual_cost = (
                (actual_tokens.get("input", 0) / 1_000_000) * costs["input"] +
                (actual_tokens.get("output", 0) / 1_000_000) * costs["output"]
            )
        
        usage_record = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "tier": selection["tier"],
            "model_id": selection["model_id"],
            "estimated_cost": selection["estimated_cost_usd"],
            "actual_cost": round(actual_cost, 6),
            "estimated_tokens": selection["estimated_tokens"],
            "actual_tokens": actual_tokens,
            "cost_difference": round(actual_cost - selection["estimated_cost_usd"], 6)
        }
        
        self.cost_log.append(usage_record)
        self._save_cost_record(usage_record)
        
        return usage_record
    
    def _save_cost_record(self, record: Dict):
        """Save cost record to file"""
        try:
            self.cost_file.parent.mkdir(exist_ok=True)
            with open(self.cost_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Fail silently
    
    def get_cost_summary(self, days: int = 7) -> Dict:
        """Get cost summary for recent period"""
        try:
            if not self.cost_file.exists():
                return {"status": "no_data"}
            
            with open(self.cost_file, "r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f if line.strip()]
            
            # Filter by date
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            recent = [r for r in records if datetime.fromisoformat(r["timestamp"]).timestamp() > cutoff]
            
            if not recent:
                return {"status": "no_recent_data", "days": days}
            
            # Calculate totals by tier
            tier_costs = {"tier1": 0, "tier2": 0, "tier3": 0}
            tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
            
            total_actual = sum(r["actual_cost"] for r in recent)
            total_estimated = sum(r["estimated_cost"] for r in recent)
            
            for record in recent:
                tier = record["tier"]
                tier_costs[tier] += record["actual_cost"]
                tier_counts[tier] += 1
            
            return {
                "status": "success",
                "period_days": days,
                "total_requests": len(recent),
                "total_cost_usd": round(total_actual, 4),
                "estimated_cost_usd": round(total_estimated, 4),
                "cost_accuracy": round(total_actual / max(total_estimated, 0.0001), 2),
                "tier_breakdown": {
                    tier: {
                        "requests": tier_counts[tier],
                        "cost_usd": round(tier_costs[tier], 4),
                        "percentage": round(tier_costs[tier] / max(total_actual, 0.0001) * 100, 1)
                    }
                    for tier in tier_costs
                },
                "cost_per_request": round(total_actual / len(recent), 4)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global instance
model_selector = ModelSelector()

def select_model_for_tier(tier: str, context_info: Dict = None) -> Dict:
    """Global function to select model for tier"""
    return model_selector.select_model(tier, context_info)

def log_model_usage(selection: Dict, actual_tokens: Dict, execution_id: str = None) -> Dict:
    """Global function to log actual usage"""
    return model_selector.log_actual_usage(selection, actual_tokens, execution_id)

def get_cost_summary(days: int = 7) -> Dict:
    """Global function to get cost summary"""
    return model_selector.get_cost_summary(days)