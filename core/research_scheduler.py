#!/usr/bin/env python3
"""
Research Scheduler - Orchestrates proactive research and monitoring
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add workspace to path
workspace = Path(__file__).parent.parent
sys.path.append(str(workspace))

try:
    from core.research_engine import TzofitResearchEngine
    from core.proactive_monitor import ProactiveMonitor
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class TzofitResearchScheduler:
    """
    Orchestrates the complete Tzofit research and monitoring system
    Called by heartbeat to run proactive research
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or workspace)
        self.research_engine = TzofitResearchEngine(workspace_path)
        self.monitor = ProactiveMonitor(workspace_path)
        
        # Scheduling configuration
        self.config = {
            "max_daily_queries": 3,
            "max_research_time_minutes": 10,
            "min_confidence_threshold": 0.6,
            "alert_urgency_threshold": "medium"
        }
    
    def run_scheduled_research(self) -> Dict[str, Any]:
        """
        Main entry point for scheduled research execution
        Called by heartbeat system
        """
        
        start_time = datetime.now()
        
        # Step 1: Get pending research queries
        pending_queries = self.research_engine.get_pending_queries()
        
        if not pending_queries:
            return {
                "status": "no_pending_research",
                "message": "No research queries due for execution",
                "execution_time_ms": 0
            }
        
        # Step 2: Execute research (limited by max_daily_queries)
        max_queries = self.config["max_daily_queries"]
        research_results = self.research_engine.process_pending_research(max_queries)
        
        # Step 3: Evaluate results for alerts
        new_alerts = self.monitor.evaluate_research_results([
            {
                "query_id": r.query_id,
                "findings": r.findings,
                "confidence_score": r.confidence_score,
                "timestamp": r.timestamp
            }
            for r in research_results
        ])
        
        # Step 4: Run proactive system checks
        proactive_checks = self.monitor.process_proactive_checks()
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "completed",
            "research_queries_processed": len(research_results),
            "new_insights_generated": sum(len(r.insights) for r in research_results),
            "new_alerts_created": len(new_alerts),
            "proactive_checks_completed": len(proactive_checks["checks_performed"]),
            "execution_time_ms": round(execution_time, 1),
            "next_scheduled_research": self._get_next_research_time(),
            "urgent_alerts": [a for a in new_alerts if a.urgency in ["critical", "high"]],
            "research_summary": self._generate_execution_summary(research_results, new_alerts)
        }
    
    def generate_intelligence_briefing(self, period_hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive intelligence briefing
        Called for daily/weekly reports
        """
        
        # Get research briefing from engine
        research_briefing = self.research_engine.generate_daily_briefing()
        
        # Get alert summary from monitor
        alert_summary = self.monitor.generate_alert_summary()
        
        # Get urgent alerts
        urgent_alerts = self.monitor.get_active_alerts(urgency_filter="high")
        critical_alerts = self.monitor.get_active_alerts(urgency_filter="critical")
        
        # Get opportunities
        opportunities = self.monitor.get_active_alerts(alert_type_filter="opportunity")
        
        # Combine into comprehensive briefing
        briefing = {
            "briefing_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period_hours": period_hours,
            "executive_summary": self._generate_executive_summary(
                research_briefing, alert_summary, urgent_alerts + critical_alerts
            ),
            "research_insights": {
                "queries_processed": research_briefing["summary"]["research_queries_processed"],
                "key_findings": research_briefing.get("key_insights", [])[:3],
                "research_areas_covered": research_briefing.get("research_areas_covered", [])
            },
            "opportunities_identified": [
                {
                    "title": opp.title,
                    "description": opp.description,
                    "urgency": opp.urgency,
                    "actions": opp.actionable_items[:2],
                    "confidence": opp.confidence_score
                }
                for opp in opportunities[:3]
            ],
            "risks_and_alerts": {
                "critical_alerts": len(critical_alerts),
                "high_priority_alerts": len(urgent_alerts),
                "total_active_alerts": alert_summary["total_active_alerts"],
                "top_risks": [
                    {
                        "title": alert.title,
                        "urgency": alert.urgency,
                        "created": alert.created_at[:10]
                    }
                    for alert in urgent_alerts[:3]
                ]
            },
            "recommended_actions": self._generate_action_recommendations(
                research_briefing, alert_summary, opportunities, urgent_alerts
            ),
            "system_status": {
                "research_engine_health": "healthy",
                "monitoring_rules_active": alert_summary["monitoring_status"]["active_rules"],
                "last_research_execution": research_briefing["date"]
            }
        }
        
        # Save briefing to file
        self._save_briefing(briefing)
        
        return briefing
    
    def _generate_executive_summary(self, research_briefing: Dict[str, Any], 
                                   alert_summary: Dict[str, Any], 
                                   urgent_alerts: List) -> str:
        """Generate executive summary for briefing"""
        
        summary_parts = []
        
        # Research activity
        queries_processed = research_briefing["summary"]["research_queries_processed"]
        insights_found = research_briefing["summary"]["key_insights_found"]
        
        if queries_processed > 0:
            summary_parts.append(f"Processed {queries_processed} research queries, generating {insights_found} key insights")
        
        # Alert status
        total_alerts = alert_summary["total_active_alerts"]
        critical_count = alert_summary["by_urgency"]["critical"]
        high_count = alert_summary["by_urgency"]["high"]
        
        if critical_count > 0:
            summary_parts.append(f"🔴 {critical_count} critical alerts require immediate attention")
        elif high_count > 0:
            summary_parts.append(f"🟠 {high_count} high-priority alerts identified")
        elif total_alerts == 0:
            summary_parts.append("✅ No active alerts - system running smoothly")
        
        # Opportunity count
        opportunities = alert_summary["by_type"]["opportunity"]
        if opportunities > 0:
            summary_parts.append(f"💰 {opportunities} new opportunities identified")
        
        if not summary_parts:
            return "System monitoring active, no significant developments to report"
        
        return ". ".join(summary_parts) + "."
    
    def _generate_action_recommendations(self, research_briefing: Dict[str, Any],
                                       alert_summary: Dict[str, Any],
                                       opportunities: List,
                                       urgent_alerts: List) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Urgent alert actions
        if urgent_alerts:
            recommendations.append(f"Review and address {len(urgent_alerts)} urgent alerts within 24 hours")
        
        # Opportunity actions
        high_value_opportunities = [opp for opp in opportunities if opp.confidence_score > 0.8]
        if high_value_opportunities:
            recommendations.append(f"Prioritize due diligence on {len(high_value_opportunities)} high-confidence opportunities")
        
        # Research follow-ups
        actionable_items = research_briefing.get("important_actions", [])
        if actionable_items:
            recommendations.append("Execute research follow-up actions within planned timeframes")
        
        # System health
        if alert_summary["total_active_alerts"] > 10:
            recommendations.append("Consider increasing monitoring thresholds - high alert volume detected")
        
        if not recommendations:
            recommendations.append("Continue current monitoring and research schedule")
        
        return recommendations
    
    def _generate_execution_summary(self, research_results: List, new_alerts: List) -> str:
        """Generate summary of research execution"""
        
        if not research_results:
            return "No research executed"
        
        total_findings = sum(len(r.findings) for r in research_results)
        total_insights = sum(len(r.insights) for r in research_results)
        
        summary = f"Executed {len(research_results)} research queries"
        
        if total_findings > 0:
            summary += f", found {total_findings} relevant findings"
        
        if total_insights > 0:
            summary += f", generated {total_insights} insights"
        
        if new_alerts:
            urgent_count = len([a for a in new_alerts if a.urgency in ["critical", "high"]])
            if urgent_count > 0:
                summary += f", created {urgent_count} urgent alerts"
        
        return summary
    
    def _get_next_research_time(self) -> str:
        """Get next scheduled research time"""
        
        pending = self.research_engine.get_pending_queries()
        
        if not pending:
            # If no pending, next research in 24 hours
            return (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
        
        # Find earliest next run time
        next_runs = [q.next_run for q in pending if q.next_run]
        
        if next_runs:
            earliest = min(next_runs)
            return datetime.fromisoformat(earliest).strftime("%Y-%m-%d %H:%M")
        
        return (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    
    def _save_briefing(self, briefing: Dict[str, Any]):
        """Save intelligence briefing to file"""
        
        briefings_dir = self.workspace / "research" / "briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"intelligence_briefing_{timestamp}.json"
        
        try:
            with open(briefings_dir / filename, 'w') as f:
                json.dump(briefing, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete Tzofit system status"""
        
        research_status = self.research_engine.get_research_status()
        alert_summary = self.monitor.generate_alert_summary()
        
        return {
            "research_engine": {
                "active_queries": research_status["active_queries"],
                "pending_queries": research_status["pending_queries"],
                "results_last_week": research_status["results_last_week"],
                "research_areas": research_status["research_areas"]
            },
            "monitoring_system": {
                "total_alerts": alert_summary["total_active_alerts"],
                "urgent_alerts": alert_summary["by_urgency"]["critical"] + alert_summary["by_urgency"]["high"],
                "monitoring_rules": alert_summary["monitoring_status"]["active_rules"],
                "system_health": "healthy" if alert_summary["by_urgency"]["critical"] == 0 else "attention_needed"
            },
            "overall_health": "healthy" if (
                research_status["pending_queries"] < 10 and 
                alert_summary["by_urgency"]["critical"] == 0
            ) else "attention_needed",
            "last_execution": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    def format_briefing_for_message(self, briefing: Dict[str, Any]) -> str:
        """Format briefing for message delivery"""
        
        message = f"🔬 **Tzofit Intelligence Briefing — {briefing['briefing_date'][:10]}**\n\n"
        
        # Executive summary
        message += f"📊 **{briefing['executive_summary']}**\n\n"
        
        # Research insights
        research = briefing['research_insights']
        if research['queries_processed'] > 0:
            message += "🧠 **Key Research Insights:**\n"
            for insight in research['key_findings']:
                message += f"• {insight}\n"
            message += "\n"
        
        # Opportunities
        opportunities = briefing.get('opportunities_identified', [])
        if opportunities:
            message += "💰 **Opportunities Identified:**\n"
            for opp in opportunities:
                confidence_emoji = "🟢" if opp['confidence'] > 0.8 else "🟡" if opp['confidence'] > 0.6 else "🔴"
                message += f"{confidence_emoji} **{opp['title']}** ({opp['urgency']})\n"
                message += f"   {opp['description']}\n\n"
        
        # Risks and alerts
        risks = briefing['risks_and_alerts']
        if risks['critical_alerts'] > 0 or risks['high_priority_alerts'] > 0:
            message += "⚠️ **Attention Required:**\n"
            for risk in risks['top_risks']:
                urgency_emoji = "🔴" if risk['urgency'] == "critical" else "🟠"
                message += f"{urgency_emoji} {risk['title']} ({risk['created']})\n"
            message += "\n"
        
        # Recommended actions
        actions = briefing.get('recommended_actions', [])
        if actions:
            message += "🎯 **Recommended Actions:**\n"
            for i, action in enumerate(actions[:3], 1):
                message += f"{i}. {action}\n"
        
        return message.strip()

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  research_scheduler.py run-scheduled")
        print("  research_scheduler.py briefing [hours]")
        print("  research_scheduler.py status")
        print("  research_scheduler.py message-briefing [hours]")
        return
    
    scheduler = TzofitResearchScheduler()
    command = sys.argv[1]
    
    if command == "run-scheduled":
        result = scheduler.run_scheduled_research()
        
        print("🔬 Tzofit Research Execution:")
        print(f"   Status: {result['status']}")
        
        if result['status'] == "completed":
            print(f"   Queries processed: {result['research_queries_processed']}")
            print(f"   Insights generated: {result['new_insights_generated']}")
            print(f"   New alerts: {result['new_alerts_created']}")
            print(f"   Execution time: {result['execution_time_ms']:.1f}ms")
            print(f"   Summary: {result['research_summary']}")
            
            # Show urgent alerts
            if result['urgent_alerts']:
                print("\n🚨 Urgent Alerts Created:")
                for alert in result['urgent_alerts']:
                    print(f"   • {alert.title} ({alert.urgency})")
        else:
            print(f"   Message: {result['message']}")
    
    elif command == "briefing":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        briefing = scheduler.generate_intelligence_briefing(hours)
        
        print("📋 Intelligence Briefing:")
        print(json.dumps({
            "date": briefing["briefing_date"],
            "executive_summary": briefing["executive_summary"],
            "research_insights": briefing["research_insights"],
            "opportunities": len(briefing.get("opportunities_identified", [])),
            "alerts": briefing["risks_and_alerts"]["total_active_alerts"],
            "actions": briefing.get("recommended_actions", [])
        }, indent=2, ensure_ascii=False))
    
    elif command == "message-briefing":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        briefing = scheduler.generate_intelligence_briefing(hours)
        message = scheduler.format_briefing_for_message(briefing)
        
        print("📨 Formatted Briefing Message:")
        print(message)
    
    elif command == "status":
        status = scheduler.get_system_status()
        
        print("🔬 Tzofit System Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()