#!/usr/bin/env python3
"""
Monitoring Dashboard - System health and performance tracking.

Provides real-time insights into:
- Cost breakdown by tier and agent
- QA failure rates
- Agent performance
- Context usage patterns
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class MonitoringDashboard:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        
        self.cost_file = self.workspace / "state" / "model_costs.jsonl"
        self.trace_dir = self.workspace / "state" / "traces"
        
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        
        try:
            cost_summary = self._get_cost_metrics()
            qa_summary = self._get_qa_metrics()
            agent_summary = self._get_agent_metrics()
            context_summary = self._get_context_metrics()
            
            # Calculate overall health score
            health_score = self._calculate_health_score(cost_summary, qa_summary, agent_summary)
            
            return {
                "status": "healthy" if health_score > 0.8 else "warning" if health_score > 0.6 else "critical",
                "health_score": round(health_score, 2),
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "cost": cost_summary,
                    "qa": qa_summary,
                    "agents": agent_summary,
                    "context": context_summary
                },
                "alerts": self._generate_alerts(cost_summary, qa_summary, agent_summary)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_cost_metrics(self, days: int = 1) -> Dict:
        """Get cost breakdown and trends"""
        
        if not self.cost_file.exists():
            return {"status": "no_data"}
        
        try:
            with open(self.cost_file, "r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f if line.strip()]
            
            # Filter recent records
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            recent = [r for r in records if r["timestamp"] > cutoff]
            
            if not recent:
                return {"status": "no_recent_data"}
            
            # Calculate metrics
            total_cost = sum(r["actual_cost"] for r in recent)
            tier_costs = defaultdict(float)
            tier_counts = defaultdict(int)
            
            for record in recent:
                tier = record["tier"]
                tier_costs[tier] += record["actual_cost"]
                tier_counts[tier] += 1
            
            # Cost efficiency (actual vs estimated)
            total_estimated = sum(r["estimated_cost"] for r in recent)
            cost_efficiency = total_cost / max(total_estimated, 0.0001)
            
            return {
                "status": "success",
                "total_cost_usd": round(total_cost, 4),
                "total_requests": len(recent),
                "cost_per_request": round(total_cost / len(recent), 4),
                "cost_efficiency": round(cost_efficiency, 2),
                "tier_distribution": {
                    tier: {
                        "count": tier_counts[tier],
                        "cost_usd": round(tier_costs[tier], 4),
                        "percentage": round(tier_costs[tier] / max(total_cost, 0.0001) * 100, 1)
                    }
                    for tier in ["tier1", "tier2", "tier3"]
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_qa_metrics(self, days: int = 1) -> Dict:
        """Get QA pass/fail rates and common issues"""
        
        trace_files = list(self.trace_dir.glob("execution_*.jsonl"))
        
        if not trace_files:
            return {"status": "no_data"}
        
        try:
            records = []
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            for file in trace_files:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            if record.get("timestamp", "") > cutoff:
                                records.append(record)
            
            if not records:
                return {"status": "no_recent_data"}
            
            # Calculate QA metrics
            qa_passed = sum(1 for r in records if r.get("qa_passed"))
            qa_total = len(records)
            qa_rate = qa_passed / max(qa_total, 1)
            
            # Common failures
            failure_reasons = defaultdict(int)
            for record in records:
                if not record.get("qa_passed"):
                    failure_reasons["qa_failure"] += 1
            
            return {
                "status": "success",
                "qa_pass_rate": round(qa_rate, 2),
                "total_requests": qa_total,
                "passed_requests": qa_passed,
                "failed_requests": qa_total - qa_passed,
                "common_failures": dict(failure_reasons)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_agent_metrics(self, days: int = 1) -> Dict:
        """Get agent usage and performance stats"""
        
        trace_files = list(self.trace_dir.glob("execution_*.jsonl"))
        
        if not trace_files:
            return {"status": "no_data"}
        
        try:
            records = []
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            for file in trace_files:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            if record.get("timestamp", "") > cutoff:
                                records.append(record)
            
            if not records:
                return {"status": "no_recent_data"}
            
            # Agent usage stats
            agent_counts = defaultdict(int)
            agent_success = defaultdict(int)
            
            for record in records:
                agent = record.get("routing", {}).get("agent", "unknown")
                agent_counts[agent] += 1
                
                if record.get("action_executed") == "completed":
                    agent_success[agent] += 1
            
            agent_stats = {}
            for agent, count in agent_counts.items():
                success_rate = agent_success[agent] / count if count > 0 else 0
                agent_stats[agent] = {
                    "requests": count,
                    "success_rate": round(success_rate, 2),
                    "success_count": agent_success[agent]
                }
            
            return {
                "status": "success",
                "agent_stats": agent_stats,
                "most_used_agent": max(agent_counts, key=agent_counts.get) if agent_counts else "none",
                "total_agent_requests": sum(agent_counts.values())
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_context_metrics(self) -> Dict:
        """Get context usage patterns"""
        
        # This would track context usage from context_guard
        # For now, return basic info
        return {
            "status": "basic_info",
            "max_context_chars": 160000,
            "essential_files_protected": ["IDENTITY.md", "SOUL.md", "USER.md"],
            "truncation_active": True
        }
    
    def _calculate_health_score(self, cost: Dict, qa: Dict, agents: Dict) -> float:
        """Calculate overall system health score (0-1)"""
        
        score = 1.0
        
        # Cost efficiency penalty
        if cost.get("status") == "success":
            cost_efficiency = cost.get("cost_efficiency", 1.0)
            if cost_efficiency > 1.5:  # 50% over estimate
                score -= 0.2
            elif cost_efficiency > 2.0:  # 100% over estimate  
                score -= 0.4
        
        # QA failure penalty
        if qa.get("status") == "success":
            qa_rate = qa.get("qa_pass_rate", 1.0)
            score -= (1.0 - qa_rate) * 0.3
        
        # Agent failure penalty
        if agents.get("status") == "success":
            agent_stats = agents.get("agent_stats", {})
            if agent_stats:
                avg_success_rate = sum(s["success_rate"] for s in agent_stats.values()) / len(agent_stats)
                score -= (1.0 - avg_success_rate) * 0.3
        
        return max(score, 0.0)
    
    def _generate_alerts(self, cost: Dict, qa: Dict, agents: Dict) -> List[str]:
        """Generate alerts based on metrics"""
        
        alerts = []
        
        # Cost alerts
        if cost.get("status") == "success":
            if cost.get("cost_efficiency", 1.0) > 2.0:
                alerts.append("High cost overrun - estimates 100%+ off")
            
            tier_dist = cost.get("tier_distribution", {})
            tier3_pct = tier_dist.get("tier3", {}).get("percentage", 0)
            if tier3_pct > 50:
                alerts.append(f"High Opus usage: {tier3_pct}% of costs")
        
        # QA alerts  
        if qa.get("status") == "success":
            qa_rate = qa.get("qa_pass_rate", 1.0)
            if qa_rate < 0.8:
                alerts.append(f"Low QA pass rate: {int(qa_rate * 100)}%")
        
        # Agent alerts
        if agents.get("status") == "success":
            agent_stats = agents.get("agent_stats", {})
            for agent, stats in agent_stats.items():
                if stats["success_rate"] < 0.7:
                    alerts.append(f"Agent {agent} low success rate: {int(stats['success_rate'] * 100)}%")
        
        return alerts
    
    def generate_report(self, days: int = 7) -> str:
        """Generate human-readable system report"""
        
        health = self.get_system_health()
        
        if health["status"] == "error":
            return f"❌ System Health Check Failed: {health['error']}"
        
        # Build report
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️", 
            "critical": "🔴"
        }
        
        report = f"""
{status_emoji.get(health['status'], '❓')} System Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}

Health Score: {health['health_score']}/1.0 ({health['status'].upper()})

💰 Cost Metrics:"""
        
        cost = health["metrics"]["cost"]
        if cost["status"] == "success":
            report += f"""
• Total Cost: ${cost['total_cost_usd']:.4f} ({cost['total_requests']} requests)
• Cost per Request: ${cost['cost_per_request']:.4f}
• Cost Efficiency: {cost['cost_efficiency']:.2f}x (1.0 = perfect estimate)

Tier Distribution:
• Tier 1 (Sonnet): {cost['tier_distribution']['tier1']['count']} requests, ${cost['tier_distribution']['tier1']['cost_usd']:.4f} ({cost['tier_distribution']['tier1']['percentage']:.1f}%)
• Tier 2 (Enhanced): {cost['tier_distribution']['tier2']['count']} requests, ${cost['tier_distribution']['tier2']['cost_usd']:.4f} ({cost['tier_distribution']['tier2']['percentage']:.1f}%)
• Tier 3 (Opus): {cost['tier_distribution']['tier3']['count']} requests, ${cost['tier_distribution']['tier3']['cost_usd']:.4f} ({cost['tier_distribution']['tier3']['percentage']:.1f}%)"""
        else:
            report += f"\n• Status: {cost['status']}"
        
        report += f"\n\n🔍 QA Metrics:"
        qa = health["metrics"]["qa"]
        if qa["status"] == "success":
            report += f"""
• QA Pass Rate: {qa['qa_pass_rate']*100:.1f}% ({qa['passed_requests']}/{qa['total_requests']})
• Failed Requests: {qa['failed_requests']}"""
        else:
            report += f"\n• Status: {qa['status']}"
        
        report += f"\n\n🤖 Agent Performance:"
        agents = health["metrics"]["agents"]
        if agents["status"] == "success":
            report += f"\n• Most Used: {agents['most_used_agent']}"
            for agent, stats in agents["agent_stats"].items():
                report += f"\n• {agent}: {stats['requests']} requests, {stats['success_rate']*100:.1f}% success"
        else:
            report += f"\n• Status: {agents['status']}"
        
        if health["alerts"]:
            report += f"\n\n🚨 Alerts:\n" + "\n".join(f"• {alert}" for alert in health["alerts"])
        else:
            report += f"\n\n✅ No alerts"
        
        return report.strip()

# Global dashboard instance
dashboard = MonitoringDashboard()

def get_system_health() -> Dict:
    """Global function to get system health"""
    return dashboard.get_system_health()

def generate_system_report(days: int = 7) -> str:
    """Global function to generate system report"""
    return dashboard.generate_report(days)