#!/usr/bin/env python3
"""
Cost Optimizer - Smart model selection and resource usage optimization
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class ModelTier:
    name: str
    cost_per_1k_tokens: float
    capability_level: int  # 1-5 scale
    max_context: int
    recommended_use: List[str]

@dataclass
class UsageStats:
    total_requests: int = 0
    total_cost: float = 0.0
    avg_response_time_ms: float = 0.0
    tier1_usage: int = 0
    tier2_usage: int = 0
    tier3_usage: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

class CostOptimizer:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.usage_file = self.workspace / "cache" / "usage_stats.json"
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Model tier definitions
        self.tiers = {
            "tier1": ModelTier(
                name="haiku",
                cost_per_1k_tokens=0.0005,
                capability_level=2,
                max_context=200000,
                recommended_use=["simple_queries", "status_checks", "acknowledgments", "greetings"]
            ),
            "tier2": ModelTier(
                name="sonnet",
                cost_per_1k_tokens=0.006,
                capability_level=4,
                max_context=200000, 
                recommended_use=["general_tasks", "analysis", "writing", "planning"]
            ),
            "tier3": ModelTier(
                name="opus",
                cost_per_1k_tokens=0.075,
                capability_level=5,
                max_context=200000,
                recommended_use=["complex_reasoning", "legal_analysis", "critical_decisions", "code_generation"]
            )
        }
        
        # Domain to tier mapping
        self.domain_tiers = {
            "fitness": "tier1",
            "general": "tier1", 
            "email": "tier2",
            "group": "tier2",
            "legal": "tier3",
            "finance": "tier3",
            "marketing": "tier2"
        }
        
        # Load usage statistics
        self.stats = self._load_usage_stats()
    
    def select_optimal_tier(self, domain: str, complexity_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select optimal model tier based on domain, complexity, and cost constraints
        
        Args:
            domain: Task domain (general, legal, email, etc.)
            complexity_indicators: Dict with context_size, requires_reasoning, has_tools, etc.
        
        Returns:
            Dict with tier, model, estimated_cost, confidence, reason
        """
        
        # Start with domain default
        suggested_tier = self.domain_tiers.get(domain, "tier2")
        confidence = 0.7
        reasons = [f"domain_{domain}"]
        
        # Adjust based on complexity indicators
        context_size = complexity_indicators.get("context_size", 0)
        requires_reasoning = complexity_indicators.get("requires_reasoning", False)
        has_tools = complexity_indicators.get("has_tools", False)
        is_urgent = complexity_indicators.get("is_urgent", False)
        user_preference = complexity_indicators.get("user_preference")
        
        # Context size adjustments
        if context_size > 100000:
            if suggested_tier == "tier1":
                suggested_tier = "tier2"
                confidence = 0.8
                reasons.append("large_context")
        
        # Reasoning requirements
        if requires_reasoning:
            if suggested_tier == "tier1":
                suggested_tier = "tier2"
                confidence = 0.85
                reasons.append("requires_reasoning")
        
        # Tool usage typically needs more capable models
        if has_tools and len(complexity_indicators.get("tools", [])) > 3:
            if suggested_tier == "tier1":
                suggested_tier = "tier2"
                confidence = 0.8
                reasons.append("complex_tools")
        
        # User override
        if user_preference and user_preference in self.tiers:
            suggested_tier = user_preference
            confidence = 0.9
            reasons.append("user_override")
        
        # Cost-based optimization during high usage
        if self._is_high_cost_period():
            if suggested_tier == "tier3" and not domain in ["legal", "finance"]:
                suggested_tier = "tier2"
                confidence = 0.75
                reasons.append("cost_optimization")
        
        # Emergency tier downgrade if budget exceeded
        if self._is_budget_exceeded():
            if suggested_tier in ["tier2", "tier3"] and not is_urgent:
                suggested_tier = "tier1"
                confidence = 0.6
                reasons.append("budget_constraint")
        
        tier_info = self.tiers[suggested_tier]
        estimated_tokens = max(context_size, 1000)  # Minimum estimate
        estimated_cost = (estimated_tokens / 1000) * tier_info.cost_per_1k_tokens
        
        return {
            "tier": suggested_tier,
            "model": tier_info.name,
            "estimated_cost": estimated_cost,
            "estimated_tokens": estimated_tokens,
            "confidence": confidence,
            "reasons": reasons,
            "capability_level": tier_info.capability_level,
            "max_context": tier_info.max_context
        }
    
    def track_usage(self, tier: str, actual_cost: float, response_time_ms: float, 
                   tokens_used: int, was_cached: bool = False):
        """Track actual usage for optimization learning"""
        
        self.stats.total_requests += 1
        self.stats.total_cost += actual_cost
        
        # Update average response time
        current_avg = self.stats.avg_response_time_ms
        total_requests = self.stats.total_requests
        self.stats.avg_response_time_ms = ((current_avg * (total_requests - 1)) + response_time_ms) / total_requests
        
        # Track tier usage
        if tier == "tier1":
            self.stats.tier1_usage += 1
        elif tier == "tier2":
            self.stats.tier2_usage += 1
        elif tier == "tier3":
            self.stats.tier3_usage += 1
        
        # Track cache performance
        if was_cached:
            self.stats.cache_hits += 1
        else:
            self.stats.cache_misses += 1
        
        # Save updated stats
        self._save_usage_stats()
    
    def get_usage_report(self, period_days: int = 7) -> Dict[str, Any]:
        """Get usage and cost report"""
        
        cache_hit_rate = 0.0
        if (self.stats.cache_hits + self.stats.cache_misses) > 0:
            cache_hit_rate = self.stats.cache_hits / (self.stats.cache_hits + self.stats.cache_misses)
        
        avg_cost_per_request = 0.0
        if self.stats.total_requests > 0:
            avg_cost_per_request = self.stats.total_cost / self.stats.total_requests
        
        # Tier distribution
        total_tier_usage = self.stats.tier1_usage + self.stats.tier2_usage + self.stats.tier3_usage
        tier_distribution = {}
        
        if total_tier_usage > 0:
            tier_distribution = {
                "tier1": (self.stats.tier1_usage / total_tier_usage) * 100,
                "tier2": (self.stats.tier2_usage / total_tier_usage) * 100,
                "tier3": (self.stats.tier3_usage / total_tier_usage) * 100
            }
        
        # Estimate cost savings from optimization
        naive_cost = self.stats.total_requests * self.tiers["tier2"].cost_per_1k_tokens * 2  # Assume avg 2k tokens
        optimization_savings = max(0, naive_cost - self.stats.total_cost)
        savings_percentage = (optimization_savings / naive_cost * 100) if naive_cost > 0 else 0
        
        return {
            "period_days": period_days,
            "total_requests": self.stats.total_requests,
            "total_cost": round(self.stats.total_cost, 4),
            "avg_cost_per_request": round(avg_cost_per_request, 4),
            "avg_response_time_ms": round(self.stats.avg_response_time_ms, 1),
            "cache_hit_rate": round(cache_hit_rate * 100, 1),
            "tier_distribution": {k: round(v, 1) for k, v in tier_distribution.items()},
            "estimated_savings": round(optimization_savings, 4),
            "savings_percentage": round(savings_percentage, 1),
            "cost_per_day": round(self.stats.total_cost / max(period_days, 1), 4)
        }
    
    def optimize_context_loading(self, domain: str, query: str) -> Dict[str, Any]:
        """
        Determine which context files to load based on domain and query analysis
        
        Returns optimization strategy for lazy loading
        """
        
        # Essential files (always load)
        essential_files = ["IDENTITY.md", "SOUL.md"]
        
        # Domain-specific file mapping
        domain_files = {
            "fitness": ["state/fitness_tracker.md"],
            "email": ["state/OUTLOOK.md", "state/OPEN_TASKS.md"],
            "legal": ["state/LEGAL_CASES.md", "memory/legal_matters.md"],
            "group": ["state/KNOWN_GROUPS.md", "state/groups/"],
            "marketing": ["templates/marketing/", "state/publishing_queue.json"],
            "general": ["state/OPEN_TASKS.md"]
        }
        
        # Query-based hints
        query_lower = query.lower()
        conditional_files = []
        
        if any(word in query_lower for word in ["מייל", "email", "outlook"]):
            conditional_files.extend(["state/OUTLOOK.md", "integrations/email/"])
        
        if any(word in query_lower for word in ["משימה", "task", "todo"]):
            conditional_files.append("state/OPEN_TASKS.md")
        
        if any(word in query_lower for word in ["קבוצה", "group", "whatsapp"]):
            conditional_files.extend(["state/KNOWN_GROUPS.md", "state/groups/"])
        
        if any(word in query_lower for word in ["זיכרון", "memory", "זוכר"]):
            conditional_files.extend(["memory/", "MEMORY_INDEX.md"])
        
        # Estimate context size
        suggested_files = essential_files + domain_files.get(domain, []) + conditional_files
        suggested_files = list(set(suggested_files))  # Remove duplicates
        
        # Estimate total context size (rough)
        estimated_context_size = len(suggested_files) * 2000  # Rough estimate per file
        
        # Optimization strategy
        strategy = "minimal"
        if len(suggested_files) <= 3:
            strategy = "minimal"
        elif len(suggested_files) <= 6:
            strategy = "selective"
        else:
            strategy = "lazy_load"
        
        return {
            "strategy": strategy,
            "essential_files": essential_files,
            "suggested_files": suggested_files,
            "estimated_context_size": estimated_context_size,
            "load_priority": {
                "immediate": essential_files,
                "on_demand": conditional_files,
                "domain_specific": domain_files.get(domain, [])
            }
        }
    
    def _load_usage_stats(self) -> UsageStats:
        """Load usage statistics from file"""
        
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    return UsageStats(**data)
        except:
            pass
        
        return UsageStats()
    
    def _save_usage_stats(self):
        """Save usage statistics to file"""
        
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.stats.__dict__, f, indent=2)
        except:
            pass
    
    def _is_high_cost_period(self) -> bool:
        """Check if we're in a high-cost usage period"""
        
        # High cost if we've spent more than $1 in the last hour (approximate)
        # This is a placeholder - real implementation would track hourly usage
        return self.stats.total_cost > 1.0 and self.stats.total_requests > 50
    
    def _is_budget_exceeded(self) -> bool:
        """Check if daily budget is exceeded"""
        
        # Daily budget threshold (configurable)
        daily_budget = float(os.environ.get("DVORAH_DAILY_BUDGET", "5.0"))
        
        # Rough daily cost estimate
        daily_cost = self.stats.total_cost  # Simplified - should be actual daily tracking
        
        return daily_cost > daily_budget
    
    def reset_stats(self):
        """Reset usage statistics (for testing or new periods)"""
        
        self.stats = UsageStats()
        self._save_usage_stats()
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for further optimization"""
        
        recommendations = []
        
        # Cache hit rate analysis
        cache_hit_rate = 0.0
        if (self.stats.cache_hits + self.stats.cache_misses) > 0:
            cache_hit_rate = self.stats.cache_hits / (self.stats.cache_hits + self.stats.cache_misses)
        
        if cache_hit_rate < 0.3:
            recommendations.append("Consider caching more responses - current hit rate is low")
        
        # Tier usage analysis
        total_tier_usage = self.stats.tier1_usage + self.stats.tier2_usage + self.stats.tier3_usage
        
        if total_tier_usage > 0:
            tier3_percentage = (self.stats.tier3_usage / total_tier_usage) * 100
            
            if tier3_percentage > 30:
                recommendations.append("High tier3 usage - review if all require complex reasoning")
            
            tier1_percentage = (self.stats.tier1_usage / total_tier_usage) * 100
            
            if tier1_percentage < 20:
                recommendations.append("Consider using tier1 model for more simple queries")
        
        # Response time analysis
        if self.stats.avg_response_time_ms > 2000:
            recommendations.append("Average response time is high - consider fast path optimization")
        
        # Cost analysis
        if self.stats.total_requests > 0:
            avg_cost = self.stats.total_cost / self.stats.total_requests
            if avg_cost > 0.01:
                recommendations.append("Average cost per request is high - review tier selection")
        
        return recommendations

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  cost_optimizer.py select <domain> [complexity_json]")
        print("  cost_optimizer.py track <tier> <cost> <time_ms> <tokens> [cached]")
        print("  cost_optimizer.py report [days]")
        print("  cost_optimizer.py optimize-context <domain> '<query>'")
        print("  cost_optimizer.py recommendations")
        print("  cost_optimizer.py reset")
        return
    
    optimizer = CostOptimizer()
    command = sys.argv[1]
    
    if command == "select" and len(sys.argv) >= 3:
        domain = sys.argv[2]
        complexity = {}
        
        if len(sys.argv) > 3:
            try:
                complexity = json.loads(sys.argv[3])
            except:
                complexity = {"context_size": 5000}
        
        result = optimizer.select_optimal_tier(domain, complexity)
        
        print(f"🎯 Optimal tier selection for domain '{domain}':")
        print(f"   Tier: {result['tier']} ({result['model']})")
        print(f"   Estimated cost: ${result['estimated_cost']:.4f}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reasons: {', '.join(result['reasons'])}")
        print(f"   Capability level: {result['capability_level']}/5")
    
    elif command == "track" and len(sys.argv) >= 6:
        tier = sys.argv[2]
        cost = float(sys.argv[3])
        time_ms = float(sys.argv[4])
        tokens = int(sys.argv[5])
        cached = len(sys.argv) > 6 and sys.argv[6].lower() == "true"
        
        optimizer.track_usage(tier, cost, time_ms, tokens, cached)
        print(f"✅ Tracked usage: {tier}, ${cost:.4f}, {time_ms:.1f}ms, {tokens} tokens")
    
    elif command == "report":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        report = optimizer.get_usage_report(days)
        
        print(f"📊 Usage Report ({days} days):")
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif command == "optimize-context" and len(sys.argv) >= 4:
        domain = sys.argv[2]
        query = sys.argv[3]
        
        result = optimizer.optimize_context_loading(domain, query)
        
        print(f"🔧 Context optimization for '{domain}':")
        print(f"   Strategy: {result['strategy']}")
        print(f"   Suggested files: {len(result['suggested_files'])}")
        print(f"   Estimated context size: {result['estimated_context_size']:,} characters")
        print(f"   Load priority:")
        for priority, files in result['load_priority'].items():
            if files:
                print(f"     {priority}: {len(files)} files")
    
    elif command == "recommendations":
        recommendations = optimizer.get_optimization_recommendations()
        
        print("💡 Optimization Recommendations:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   No specific recommendations - system is well optimized!")
    
    elif command == "reset":
        optimizer.reset_stats()
        print("✅ Usage statistics reset")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()