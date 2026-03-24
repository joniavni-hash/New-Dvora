#!/usr/bin/env python3
"""
Proactive Monitor - Watches for opportunities and alerts
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class Alert:
    id: str
    alert_type: str  # "opportunity", "risk", "trend", "deadline"
    title: str
    description: str
    urgency: str  # "low", "medium", "high", "critical"
    source: str
    created_at: str
    expires_at: Optional[str]
    related_entities: List[str]
    actionable_items: List[str]
    confidence_score: float
    dismissed: bool = False

@dataclass
class MonitoringRule:
    id: str
    name: str
    rule_type: str  # "keyword", "threshold", "pattern", "time_based"
    conditions: Dict[str, Any]
    alert_template: Dict[str, Any]
    enabled: bool = True
    created_at: str = None
    last_triggered: Optional[str] = None

class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProactiveMonitor:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE",
                                                             Path.home() / ".openclaw" / "workspace"))
        self.monitor_dir = self.workspace / "monitoring"
        self.monitor_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitor configuration files
        self.rules_file = self.monitor_dir / "monitoring_rules.json"
        self.alerts_file = self.monitor_dir / "active_alerts.json"
        self.triggers_log = self.monitor_dir / "triggers.log"
        
        # Initialize with default rules
        self._initialize_default_rules()
        
        # Load active alerts and rules
        self.monitoring_rules = self._load_rules()
        self.active_alerts = self._load_alerts()
    
    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""
        
        default_rules = [
            MonitoringRule(
                id="high_value_investment",
                name="High Value Investment Opportunity",
                rule_type="threshold",
                conditions={
                    "funding_amount_min": 10_000_000,  # $10M+
                    "keywords": ["Series A", "Series B", "AI", "Israeli startup"],
                    "relevance_threshold": 0.8
                },
                alert_template={
                    "alert_type": "opportunity",
                    "title": "High-Value Investment Opportunity Detected",
                    "urgency": "high",
                    "actionable_items": [
                        "Research company background",
                        "Analyze market opportunity",
                        "Schedule due diligence call"
                    ]
                },
                created_at=datetime.now().isoformat()
            ),
            MonitoringRule(
                id="ai_breakthrough",
                name="AI Technology Breakthrough",
                rule_type="keyword",
                conditions={
                    "keywords": ["breakthrough", "state-of-the-art", "surpasses", "benchmark"],
                    "domains": ["AI", "machine learning", "Claude", "GPT"],
                    "confidence_min": 0.7
                },
                alert_template={
                    "alert_type": "trend",
                    "title": "Significant AI Breakthrough Detected",
                    "urgency": "medium",
                    "actionable_items": [
                        "Assess impact on AI investment thesis",
                        "Review portfolio implications",
                        "Consider strategic adjustments"
                    ]
                },
                created_at=datetime.now().isoformat()
            ),
            MonitoringRule(
                id="competitive_threat",
                name="Competitive Threat Alert",
                rule_type="pattern",
                conditions={
                    "competitor_keywords": ["linear motors", "automation", "motion control"],
                    "threat_indicators": ["funding", "partnership", "acquisition", "IPO"],
                    "market_overlap_threshold": 0.6
                },
                alert_template={
                    "alert_type": "risk",
                    "title": "Competitive Threat Identified",
                    "urgency": "medium",
                    "actionable_items": [
                        "Analyze competitive positioning",
                        "Review product roadmap",
                        "Consider strategic response"
                    ]
                },
                created_at=datetime.now().isoformat()
            ),
            MonitoringRule(
                id="legal_deadline_approaching",
                name="Legal Deadline Alert",
                rule_type="time_based",
                conditions={
                    "days_before_deadline": 7,
                    "task_types": ["legal", "compliance", "contract"],
                    "priority_threshold": "medium"
                },
                alert_template={
                    "alert_type": "deadline",
                    "title": "Legal Deadline Approaching",
                    "urgency": "high",
                    "actionable_items": [
                        "Review task status",
                        "Allocate resources if needed",
                        "Confirm completion timeline"
                    ]
                },
                created_at=datetime.now().isoformat()
            ),
            MonitoringRule(
                id="market_volatility",
                name="Market Volatility Alert",
                rule_type="threshold",
                conditions={
                    "volatility_threshold": 0.15,  # 15% change
                    "markets": ["NASDAQ", "TASE"],
                    "sectors": ["technology", "AI"]
                },
                alert_template={
                    "alert_type": "risk", 
                    "title": "Significant Market Volatility Detected",
                    "urgency": "medium",
                    "actionable_items": [
                        "Review portfolio exposure",
                        "Consider position adjustments",
                        "Monitor key holdings"
                    ]
                },
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Save if rules file doesn't exist
        if not self.rules_file.exists():
            self._save_rules(default_rules)
    
    def add_monitoring_rule(self, name: str, rule_type: str, conditions: Dict[str, Any],
                           alert_template: Dict[str, Any]) -> str:
        """Add new monitoring rule"""
        
        rule_id = f"custom_{int(time.time())}"
        
        rule = MonitoringRule(
            id=rule_id,
            name=name,
            rule_type=rule_type,
            conditions=conditions,
            alert_template=alert_template,
            created_at=datetime.now().isoformat()
        )
        
        self.monitoring_rules.append(rule)
        self._save_rules(self.monitoring_rules)
        
        return rule_id
    
    def evaluate_research_results(self, research_results: List[Dict[str, Any]]) -> List[Alert]:
        """Evaluate research results against monitoring rules"""
        
        new_alerts = []
        
        for result in research_results:
            findings = result.get("findings", [])
            
            for rule in self.monitoring_rules:
                if not rule.enabled:
                    continue
                
                alert = self._evaluate_rule_against_findings(rule, findings, result)
                if alert:
                    new_alerts.append(alert)
        
        # Add new alerts to active alerts
        self.active_alerts.extend(new_alerts)
        self._save_alerts(self.active_alerts)
        
        return new_alerts
    
    def _evaluate_rule_against_findings(self, rule: MonitoringRule, 
                                      findings: List[Dict[str, Any]], 
                                      research_result: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate specific rule against research findings"""
        
        if rule.rule_type == "threshold":
            return self._evaluate_threshold_rule(rule, findings, research_result)
        elif rule.rule_type == "keyword":
            return self._evaluate_keyword_rule(rule, findings, research_result)
        elif rule.rule_type == "pattern":
            return self._evaluate_pattern_rule(rule, findings, research_result)
        elif rule.rule_type == "time_based":
            return self._evaluate_time_rule(rule, findings, research_result)
        
        return None
    
    def _evaluate_threshold_rule(self, rule: MonitoringRule, 
                               findings: List[Dict[str, Any]], 
                               research_result: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate threshold-based rule"""
        
        conditions = rule.conditions
        
        # Check funding threshold
        if "funding_amount_min" in conditions:
            for finding in findings:
                # Look for funding amounts in findings
                funding_text = str(finding).lower()
                
                # Simple pattern matching for funding amounts
                import re
                amounts = re.findall(r'\$(\d+(?:\.\d+)?)\s*([mb])', funding_text)
                
                for amount_str, unit in amounts:
                    amount = float(amount_str)
                    if unit == 'm':
                        amount *= 1_000_000
                    elif unit == 'b':
                        amount *= 1_000_000_000
                    
                    if amount >= conditions["funding_amount_min"]:
                        # Check additional keyword conditions
                        if self._check_keywords(finding, conditions.get("keywords", [])):
                            return self._create_alert_from_template(
                                rule, finding, research_result, 
                                f"${amount/1_000_000:.1f}M funding opportunity"
                            )
        
        # Check relevance threshold
        if "relevance_threshold" in conditions:
            high_relevance_findings = [f for f in findings 
                                     if f.get("relevance_score", 0) >= conditions["relevance_threshold"]]
            
            if high_relevance_findings and self._check_keywords(high_relevance_findings[0], 
                                                              conditions.get("keywords", [])):
                return self._create_alert_from_template(
                    rule, high_relevance_findings[0], research_result,
                    "High relevance threshold met"
                )
        
        return None
    
    def _evaluate_keyword_rule(self, rule: MonitoringRule,
                             findings: List[Dict[str, Any]],
                             research_result: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate keyword-based rule"""
        
        conditions = rule.conditions
        keywords = conditions.get("keywords", [])
        domains = conditions.get("domains", [])
        confidence_min = conditions.get("confidence_min", 0.5)
        
        for finding in findings:
            finding_text = str(finding).lower()
            
            # Check if keywords are present
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in finding_text)
            domain_matches = sum(1 for domain in domains if domain.lower() in finding_text)
            
            keyword_score = keyword_matches / len(keywords) if keywords else 1.0
            domain_score = domain_matches / len(domains) if domains else 1.0
            
            combined_score = (keyword_score + domain_score) / 2
            
            if combined_score >= confidence_min:
                return self._create_alert_from_template(
                    rule, finding, research_result,
                    f"Keyword pattern match (score: {combined_score:.2f})"
                )
        
        return None
    
    def _evaluate_pattern_rule(self, rule: MonitoringRule,
                             findings: List[Dict[str, Any]],
                             research_result: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate pattern-based rule"""
        
        conditions = rule.conditions
        competitor_keywords = conditions.get("competitor_keywords", [])
        threat_indicators = conditions.get("threat_indicators", [])
        
        for finding in findings:
            finding_text = str(finding).lower()
            
            # Check for competitor keyword presence
            has_competitor = any(keyword.lower() in finding_text for keyword in competitor_keywords)
            
            # Check for threat indicators
            has_threat = any(indicator.lower() in finding_text for indicator in threat_indicators)
            
            if has_competitor and has_threat:
                return self._create_alert_from_template(
                    rule, finding, research_result,
                    "Competitive threat pattern detected"
                )
        
        return None
    
    def _evaluate_time_rule(self, rule: MonitoringRule,
                          findings: List[Dict[str, Any]],
                          research_result: Dict[str, Any]) -> Optional[Alert]:
        """Evaluate time-based rule (checks system state, not research findings)"""
        
        # This would check actual system deadlines, tasks, etc.
        # For now, placeholder implementation
        
        conditions = rule.conditions
        days_before = conditions.get("days_before_deadline", 7)
        
        # Check open tasks for approaching deadlines
        try:
            tasks_file = self.workspace / "state" / "OPEN_TASKS.md"
            if tasks_file.exists():
                content = tasks_file.read_text()
                
                # Simple deadline detection (would be more sophisticated in real implementation)
                if "🔴" in content and "deadline" in content.lower():
                    return self._create_alert_from_template(
                        rule, {"title": "System deadline check", "content": "Urgent tasks detected"}, 
                        research_result, "Deadline approaching detected"
                    )
        except:
            pass
        
        return None
    
    def _check_keywords(self, finding: Dict[str, Any], keywords: List[str]) -> bool:
        """Check if finding contains specified keywords"""
        
        finding_text = str(finding).lower()
        return any(keyword.lower() in finding_text for keyword in keywords)
    
    def _create_alert_from_template(self, rule: MonitoringRule, finding: Dict[str, Any],
                                  research_result: Dict[str, Any], context: str) -> Alert:
        """Create alert from rule template"""
        
        template = rule.alert_template
        timestamp = datetime.now()
        
        alert = Alert(
            id=f"{rule.id}_{int(timestamp.timestamp())}",
            alert_type=template["alert_type"],
            title=template["title"],
            description=f"{context}. Source: {finding.get('title', 'Research finding')}",
            urgency=template["urgency"],
            source=f"Monitor rule: {rule.name}",
            created_at=timestamp.isoformat(),
            expires_at=(timestamp + timedelta(days=7)).isoformat(),  # Alerts expire after 7 days
            related_entities=[research_result.get("query_id", "unknown")],
            actionable_items=template["actionable_items"],
            confidence_score=research_result.get("confidence_score", 0.7)
        )
        
        # Update rule last triggered
        rule.last_triggered = timestamp.isoformat()
        
        return alert
    
    def get_active_alerts(self, urgency_filter: str = None, 
                         alert_type_filter: str = None) -> List[Alert]:
        """Get active alerts with optional filtering"""
        
        # Remove expired alerts
        now = datetime.now()
        active = []
        
        for alert in self.active_alerts:
            if alert.dismissed:
                continue
                
            if alert.expires_at and datetime.fromisoformat(alert.expires_at) < now:
                continue
                
            if urgency_filter and alert.urgency != urgency_filter:
                continue
                
            if alert_type_filter and alert.alert_type != alert_type_filter:
                continue
            
            active.append(alert)
        
        # Sort by urgency and creation time
        urgency_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        return sorted(active, key=lambda a: (
            urgency_order.get(a.urgency, 0),
            datetime.fromisoformat(a.created_at)
        ), reverse=True)
    
    def dismiss_alert(self, alert_id: str, reason: str = None):
        """Dismiss an alert"""
        
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.dismissed = True
                break
        
        self._save_alerts(self.active_alerts)
    
    def generate_alert_summary(self) -> Dict[str, Any]:
        """Generate summary of current alerts"""
        
        active = self.get_active_alerts()
        
        summary = {
            "total_active_alerts": len(active),
            "by_urgency": {
                "critical": len([a for a in active if a.urgency == "critical"]),
                "high": len([a for a in active if a.urgency == "high"]),
                "medium": len([a for a in active if a.urgency == "medium"]),
                "low": len([a for a in active if a.urgency == "low"])
            },
            "by_type": {
                "opportunity": len([a for a in active if a.alert_type == "opportunity"]),
                "risk": len([a for a in active if a.alert_type == "risk"]),
                "trend": len([a for a in active if a.alert_type == "trend"]),
                "deadline": len([a for a in active if a.alert_type == "deadline"])
            },
            "urgent_alerts": [
                {
                    "id": a.id,
                    "title": a.title,
                    "urgency": a.urgency,
                    "created_at": a.created_at,
                    "actionable_items": a.actionable_items[:2]  # First 2 actions
                }
                for a in active if a.urgency in ["critical", "high"]
            ][:5],  # Top 5 urgent alerts
            "monitoring_status": {
                "total_rules": len(self.monitoring_rules),
                "active_rules": len([r for r in self.monitoring_rules if r.enabled]),
                "last_evaluation": datetime.now().isoformat()
            }
        }
        
        return summary
    
    def process_proactive_checks(self) -> Dict[str, Any]:
        """Run proactive checks on system state"""
        
        checks_performed = []
        alerts_generated = []
        
        # Check 1: Task deadlines
        task_alerts = self._check_task_deadlines()
        alerts_generated.extend(task_alerts)
        checks_performed.append("task_deadlines")
        
        # Check 2: System health
        health_alerts = self._check_system_health()
        alerts_generated.extend(health_alerts)
        checks_performed.append("system_health")
        
        # Check 3: Financial thresholds
        financial_alerts = self._check_financial_thresholds()
        alerts_generated.extend(financial_alerts)
        checks_performed.append("financial_thresholds")
        
        # Add new alerts
        self.active_alerts.extend(alerts_generated)
        self._save_alerts(self.active_alerts)
        
        return {
            "checks_performed": checks_performed,
            "alerts_generated": len(alerts_generated),
            "new_alerts": [a.id for a in alerts_generated]
        }
    
    def _check_task_deadlines(self) -> List[Alert]:
        """Check for approaching task deadlines"""
        
        alerts = []
        
        try:
            tasks_file = self.workspace / "state" / "OPEN_TASKS.md"
            if not tasks_file.exists():
                return alerts
            
            content = tasks_file.read_text()
            
            # Count urgent tasks (🔴)
            urgent_count = content.count("🔴")
            
            if urgent_count > 2:  # More than 2 urgent tasks
                alert = Alert(
                    id=f"task_overload_{int(time.time())}",
                    alert_type="risk",
                    title="High Number of Urgent Tasks",
                    description=f"{urgent_count} urgent tasks require attention",
                    urgency="medium",
                    source="Proactive task monitoring",
                    created_at=datetime.now().isoformat(),
                    expires_at=(datetime.now() + timedelta(days=3)).isoformat(),
                    related_entities=["task_management"],
                    actionable_items=[
                        "Review task priorities",
                        "Delegate if possible",
                        "Extend deadlines if necessary"
                    ],
                    confidence_score=1.0
                )
                alerts.append(alert)
        
        except Exception as e:
            pass
        
        return alerts
    
    def _check_system_health(self) -> List[Alert]:
        """Check system health indicators"""
        
        alerts = []
        
        # Check integration status
        try:
            integration_file = self.workspace / "cache" / "fast_path" / "integration_status.json"
            if integration_file.exists():
                with open(integration_file, 'r') as f:
                    status = json.load(f)
                    
                    healthy_count = status.get("healthy_count", 0)
                    total_count = status.get("total_count", 1)
                    
                    if healthy_count / total_count < 0.7:  # Less than 70% healthy
                        alert = Alert(
                            id=f"integration_health_{int(time.time())}",
                            alert_type="risk",
                            title="Integration Health Below Threshold",
                            description=f"Only {healthy_count}/{total_count} integrations healthy",
                            urgency="medium",
                            source="System health monitoring",
                            created_at=datetime.now().isoformat(),
                            expires_at=(datetime.now() + timedelta(days=1)).isoformat(),
                            related_entities=["system_integrations"],
                            actionable_items=[
                                "Check integration logs",
                                "Restart failed services",
                                "Update credentials if needed"
                            ],
                            confidence_score=0.9
                        )
                        alerts.append(alert)
        except:
            pass
        
        return alerts
    
    def _check_financial_thresholds(self) -> List[Alert]:
        """Check financial/cost thresholds"""
        
        alerts = []
        
        # Check cost optimizer data
        try:
            usage_file = self.workspace / "cache" / "usage_stats.json"
            if usage_file.exists():
                with open(usage_file, 'r') as f:
                    usage = json.load(f)
                    
                    total_cost = usage.get("total_cost", 0)
                    
                    # Alert if daily cost exceeds threshold
                    if total_cost > 5.0:  # $5 daily threshold
                        alert = Alert(
                            id=f"cost_threshold_{int(time.time())}",
                            alert_type="risk",
                            title="Daily Cost Threshold Exceeded",
                            description=f"Daily cost ${total_cost:.2f} exceeds $5.00 threshold",
                            urgency="medium",
                            source="Cost monitoring",
                            created_at=datetime.now().isoformat(),
                            expires_at=(datetime.now() + timedelta(days=1)).isoformat(),
                            related_entities=["cost_optimization"],
                            actionable_items=[
                                "Review expensive queries",
                                "Optimize model tier selection",
                                "Check for runaway processes"
                            ],
                            confidence_score=1.0
                        )
                        alerts.append(alert)
        except:
            pass
        
        return alerts
    
    def _load_rules(self) -> List[MonitoringRule]:
        """Load monitoring rules from file"""
        
        if not self.rules_file.exists():
            return []
        
        try:
            with open(self.rules_file, 'r') as f:
                data = json.load(f)
                return [MonitoringRule(**r) for r in data]
        except:
            return []
    
    def _save_rules(self, rules: List[MonitoringRule]):
        """Save monitoring rules to file"""
        
        try:
            with open(self.rules_file, 'w') as f:
                json.dump([asdict(r) for r in rules], f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _load_alerts(self) -> List[Alert]:
        """Load active alerts from file"""
        
        if not self.alerts_file.exists():
            return []
        
        try:
            with open(self.alerts_file, 'r') as f:
                data = json.load(f)
                return [Alert(**a) for a in data]
        except:
            return []
    
    def _save_alerts(self, alerts: List[Alert]):
        """Save active alerts to file"""
        
        try:
            with open(self.alerts_file, 'w') as f:
                json.dump([asdict(a) for a in alerts], f, indent=2, ensure_ascii=False)
        except:
            pass

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  proactive_monitor.py alerts [urgency] [type]")
        print("  proactive_monitor.py summary")
        print("  proactive_monitor.py dismiss <alert_id>")
        print("  proactive_monitor.py check")
        print("  proactive_monitor.py rules")
        print("  proactive_monitor.py add-rule '<name>' <type> '<conditions_json>' '<template_json>'")
        return
    
    monitor = ProactiveMonitor()
    command = sys.argv[1]
    
    if command == "alerts":
        urgency_filter = sys.argv[2] if len(sys.argv) > 2 else None
        type_filter = sys.argv[3] if len(sys.argv) > 3 else None
        
        alerts = monitor.get_active_alerts(urgency_filter, type_filter)
        
        print(f"🚨 Active Alerts ({len(alerts)}):")
        for alert in alerts:
            urgency_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            type_emoji = {"opportunity": "💰", "risk": "⚠️", "trend": "📈", "deadline": "⏰"}
            
            print(f"  {urgency_emoji.get(alert.urgency, '🔵')} {type_emoji.get(alert.alert_type, '📋')} {alert.title}")
            print(f"      {alert.description}")
            print(f"      Created: {alert.created_at[:10]}, Confidence: {alert.confidence_score}")
            print(f"      Actions: {', '.join(alert.actionable_items[:2])}")
            print()
    
    elif command == "summary":
        summary = monitor.generate_alert_summary()
        
        print("📊 Alert Summary:")
        print(f"  Total active: {summary['total_active_alerts']}")
        print(f"  By urgency: {summary['by_urgency']}")
        print(f"  By type: {summary['by_type']}")
        print()
        
        if summary['urgent_alerts']:
            print("🚨 Urgent Alerts:")
            for alert in summary['urgent_alerts']:
                print(f"  • {alert['title']} ({alert['urgency']})")
    
    elif command == "dismiss" and len(sys.argv) >= 3:
        alert_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else "Manual dismissal"
        
        monitor.dismiss_alert(alert_id, reason)
        print(f"✅ Alert {alert_id} dismissed")
    
    elif command == "check":
        result = monitor.process_proactive_checks()
        
        print("🔍 Proactive Checks Completed:")
        print(f"  Checks performed: {', '.join(result['checks_performed'])}")
        print(f"  New alerts generated: {result['alerts_generated']}")
        
        if result['new_alerts']:
            print(f"  Alert IDs: {', '.join(result['new_alerts'])}")
    
    elif command == "rules":
        print("📋 Monitoring Rules:")
        for rule in monitor.monitoring_rules:
            status = "🟢" if rule.enabled else "🔴"
            print(f"  {status} {rule.name} ({rule.rule_type})")
            print(f"      Last triggered: {rule.last_triggered or 'Never'}")
            print()
    
    elif command == "add-rule" and len(sys.argv) >= 5:
        name = sys.argv[2]
        rule_type = sys.argv[3]
        
        try:
            conditions = json.loads(sys.argv[4])
            template = json.loads(sys.argv[5])
            
            rule_id = monitor.add_monitoring_rule(name, rule_type, conditions, template)
            print(f"✅ Added monitoring rule: {rule_id}")
        except json.JSONDecodeError:
            print("❌ Invalid JSON in conditions or template")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()