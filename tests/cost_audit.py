#!/usr/bin/env python3
"""
Cost Audit - Analyze actual model usage and cost optimization opportunities.
Reviews cost logs, model selection patterns, and efficiency.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import argparse

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

class CostAuditor:
    def __init__(self):
        self.cost_log_file = WORKSPACE / "state" / "model_costs.jsonl"
        self.execution_log_file = WORKSPACE / "state" / "traces" / "execution_2026-03-24.jsonl"
        
    def load_cost_data(self, days: int = 7) -> list:
        """Load cost data from logs"""
        costs = []
        
        if self.cost_log_file.exists():
            with open(self.cost_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            costs.append(record)
                        except json.JSONDecodeError:
                            continue
        
        return costs
    
    def load_execution_data(self) -> list:
        """Load execution trace data"""
        executions = []
        
        if self.execution_log_file.exists():
            with open(self.execution_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            executions.append(record)
                        except json.JSONDecodeError:
                            continue
        
        return executions
    
    def analyze_model_usage(self, costs: list) -> dict:
        """Analyze model usage patterns"""
        if not costs:
            return {"error": "No cost data available"}
        
        # Group by tier/model
        tier_stats = {}
        model_stats = {}
        
        for record in costs:
            tier = record.get("tier", "unknown")
            model = record.get("model_id", "unknown")
            cost = record.get("actual_cost", 0)
            
            # Tier statistics
            if tier not in tier_stats:
                tier_stats[tier] = {"count": 0, "total_cost": 0, "costs": []}
            tier_stats[tier]["count"] += 1
            tier_stats[tier]["total_cost"] += cost
            tier_stats[tier]["costs"].append(cost)
            
            # Model statistics  
            if model not in model_stats:
                model_stats[model] = {"count": 0, "total_cost": 0, "costs": []}
            model_stats[model]["count"] += 1
            model_stats[model]["total_cost"] += cost
            model_stats[model]["costs"].append(cost)
        
        # Calculate averages
        for tier in tier_stats:
            tier_stats[tier]["avg_cost"] = tier_stats[tier]["total_cost"] / tier_stats[tier]["count"]
            
        for model in model_stats:
            model_stats[model]["avg_cost"] = model_stats[model]["total_cost"] / model_stats[model]["count"]
        
        return {
            "tier_breakdown": tier_stats,
            "model_breakdown": model_stats,
            "total_records": len(costs),
            "total_cost": sum(r.get("actual_cost", 0) for r in costs)
        }
    
    def analyze_routing_efficiency(self, executions: list) -> dict:
        """Analyze routing efficiency and domain distribution"""
        if not executions:
            return {"error": "No execution data available"}
        
        domain_stats = {}
        agent_stats = {}
        tier_routing = {}
        
        for execution in executions:
            routing = execution.get("routing", {})
            domain = routing.get("domain", "unknown")
            agent = routing.get("agent", "unknown")
            
            # Extract model tier from context
            tier = "unknown"
            if "routing" in execution and "model" in execution["routing"]:
                tier = execution["routing"]["model"]
            
            # Domain statistics
            if domain not in domain_stats:
                domain_stats[domain] = {"count": 0, "agents": {}, "tiers": {}}
            domain_stats[domain]["count"] += 1
            
            # Track agent usage per domain
            if agent not in domain_stats[domain]["agents"]:
                domain_stats[domain]["agents"][agent] = 0
            domain_stats[domain]["agents"][agent] += 1
            
            # Track tier usage per domain
            if tier not in domain_stats[domain]["tiers"]:
                domain_stats[domain]["tiers"][tier] = 0
            domain_stats[domain]["tiers"][tier] += 1
            
            # Agent statistics
            if agent not in agent_stats:
                agent_stats[agent] = {"count": 0, "domains": {}}
            agent_stats[agent]["count"] += 1
            
            if domain not in agent_stats[agent]["domains"]:
                agent_stats[agent]["domains"][domain] = 0
            agent_stats[agent]["domains"][domain] += 1
            
            # Tier routing patterns
            route_key = f"{domain} → {agent} → {tier}"
            if route_key not in tier_routing:
                tier_routing[route_key] = 0
            tier_routing[route_key] += 1
        
        return {
            "domain_distribution": domain_stats,
            "agent_utilization": agent_stats, 
            "tier_routing_patterns": tier_routing,
            "total_executions": len(executions)
        }
    
    def identify_cost_optimization_opportunities(self, usage_analysis: dict, routing_analysis: dict) -> list:
        """Identify cost optimization opportunities"""
        opportunities = []
        
        # Check tier usage patterns
        tier_breakdown = usage_analysis.get("tier_breakdown", {})
        
        # High tier3 usage
        if "tier3" in tier_breakdown:
            tier3_count = tier_breakdown["tier3"]["count"] 
            total_count = sum(t["count"] for t in tier_breakdown.values())
            tier3_percentage = (tier3_count / total_count * 100) if total_count > 0 else 0
            
            if tier3_percentage > 15:  # More than 15% tier3 usage
                opportunities.append({
                    "type": "tier_optimization", 
                    "issue": "High tier3 (Opus) usage",
                    "details": f"{tier3_percentage:.1f}% of requests use expensive tier3",
                    "potential_savings": "Consider if some tier3 tasks can use tier2",
                    "priority": "medium"
                })
        
        # Check for domains that might be over-tiered
        domain_dist = routing_analysis.get("domain_distribution", {})
        
        for domain, stats in domain_dist.items():
            tier_usage = stats.get("tiers", {})
            if tier_usage.get("tier3", 0) > 0 and domain not in ["legal"]:
                opportunities.append({
                    "type": "domain_tier_mismatch",
                    "issue": f"Domain '{domain}' using tier3",
                    "details": f"Non-legal domain using expensive model",
                    "potential_savings": "Review if tier3 is necessary for this domain",
                    "priority": "high"
                })
        
        # Check cost per domain
        if tier_breakdown and domain_dist:
            high_cost_domains = []
            for domain, stats in domain_dist.items():
                domain_count = stats["count"]
                # Rough estimate of domain cost
                tier_costs = stats.get("tiers", {})
                estimated_cost = (
                    tier_costs.get("tier1", 0) * 0.0025 +
                    tier_costs.get("tier2", 0) * 0.0025 + 
                    tier_costs.get("tier3", 0) * 0.15
                )
                
                if estimated_cost > 0.5 and domain_count > 3:  # High cost, frequent domain
                    high_cost_domains.append((domain, estimated_cost, domain_count))
            
            if high_cost_domains:
                opportunities.append({
                    "type": "high_cost_domains",
                    "issue": "Domains with high cumulative cost",
                    "details": f"Domains: {[d[0] for d in high_cost_domains]}",
                    "potential_savings": "Optimize frequently used high-cost domains",
                    "priority": "high"
                })
        
        # Check for unused agents
        agent_util = routing_analysis.get("agent_utilization", {})
        unused_agents = [agent for agent, stats in agent_util.items() if stats["count"] == 0]
        if unused_agents:
            opportunities.append({
                "type": "unused_agents",
                "issue": "Agents not being utilized",
                "details": f"Unused: {unused_agents}",
                "potential_savings": "Remove or fix routing to unused agents", 
                "priority": "low"
            })
        
        return opportunities
    
    def generate_cost_audit_report(self) -> dict:
        """Generate comprehensive cost audit report"""
        print("📊 Loading cost and execution data...")
        
        costs = self.load_cost_data()
        executions = self.load_execution_data()
        
        print(f"📈 Loaded {len(costs)} cost records and {len(executions)} execution records")
        
        usage_analysis = self.analyze_model_usage(costs)
        routing_analysis = self.analyze_routing_efficiency(executions)
        optimization_opportunities = self.identify_cost_optimization_opportunities(usage_analysis, routing_analysis)
        
        # Calculate efficiency metrics
        total_cost = usage_analysis.get("total_cost", 0)
        total_executions = routing_analysis.get("total_executions", 0)
        
        efficiency_metrics = {
            "cost_per_execution": (total_cost / total_executions) if total_executions > 0 else 0,
            "tier1_percentage": 0,
            "tier2_percentage": 0, 
            "tier3_percentage": 0
        }
        
        tier_breakdown = usage_analysis.get("tier_breakdown", {})
        total_tier_count = sum(t["count"] for t in tier_breakdown.values())
        
        if total_tier_count > 0:
            efficiency_metrics["tier1_percentage"] = (tier_breakdown.get("tier1", {}).get("count", 0) / total_tier_count * 100)
            efficiency_metrics["tier2_percentage"] = (tier_breakdown.get("tier2", {}).get("count", 0) / total_tier_count * 100)  
            efficiency_metrics["tier3_percentage"] = (tier_breakdown.get("tier3", {}).get("count", 0) / total_tier_count * 100)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "audit_period": "Last 7 days",
            "summary": {
                "total_cost": round(total_cost, 6),
                "total_executions": total_executions,
                "unique_cost_records": len(costs),
                "cost_per_execution": round(efficiency_metrics["cost_per_execution"], 6)
            },
            "efficiency_metrics": efficiency_metrics,
            "model_usage_analysis": usage_analysis,
            "routing_efficiency_analysis": routing_analysis,
            "optimization_opportunities": optimization_opportunities,
            "recommendations": self._generate_cost_recommendations(optimization_opportunities)
        }
        
        return report
    
    def _generate_cost_recommendations(self, opportunities: list) -> list:
        """Generate actionable cost recommendations"""
        recommendations = []
        
        # Priority-based recommendations
        high_priority = [opp for opp in opportunities if opp.get("priority") == "high"]
        medium_priority = [opp for opp in opportunities if opp.get("priority") == "medium"]
        
        if high_priority:
            recommendations.append("🔥 High Priority: " + "; ".join([opp["potential_savings"] for opp in high_priority]))
        
        if medium_priority:
            recommendations.append("⚠️ Medium Priority: " + "; ".join([opp["potential_savings"] for opp in medium_priority]))
        
        # General recommendations
        recommendations.extend([
            "💰 Monitor tier3 usage closely - each call costs ~15-20x more than tier1",
            "🎯 Ensure legal domain gets tier3, others should prefer tier1/tier2",
            "📊 Review cost logs weekly to catch optimization opportunities early"
        ])
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="Cost audit for Dvorah system")
    parser.add_argument("--output", default="cost_audit_report.json", help="Output file")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze")
    
    args = parser.parse_args()
    
    auditor = CostAuditor()
    
    print("💰 Dvorah Cost Audit")
    print("=" * 40)
    
    report = auditor.generate_cost_audit_report()
    
    # Save report
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 Cost Audit Summary:")
    summary = report["summary"]
    print(f"💰 Total Cost: ${summary['total_cost']:.6f}")
    print(f"🔄 Total Executions: {summary['total_executions']}")
    print(f"📈 Cost per Execution: ${summary['cost_per_execution']:.6f}")
    
    efficiency = report["efficiency_metrics"]
    print(f"\n⚡ Efficiency Breakdown:")
    print(f"   Tier1 (cheap): {efficiency['tier1_percentage']:.1f}%")
    print(f"   Tier2 (mid): {efficiency['tier2_percentage']:.1f}%") 
    print(f"   Tier3 (expensive): {efficiency['tier3_percentage']:.1f}%")
    
    opportunities = report["optimization_opportunities"]
    if opportunities:
        print(f"\n🎯 Optimization Opportunities: {len(opportunities)} found")
        for opp in opportunities[:3]:  # Show top 3
            print(f"   • {opp['issue']} - {opp['potential_savings']}")
    
    print(f"\n💡 Key Recommendations:")
    for rec in report["recommendations"][:3]:  # Show top 3
        print(f"   • {rec}")
    
    print(f"\n📄 Full report: {args.output}")

if __name__ == "__main__":
    main()