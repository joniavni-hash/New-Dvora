#!/usr/bin/env python3
"""
🤖 אתי (Eti) — Automation Domain Agent

Handles: system monitoring, health checks, automation planning,
         process optimization, alerting and reporting.
Integrates with: workspace-eti/, scripts/health_check.py, HEARTBEAT.md.

Multi-tier routing:
- Tier 1 (70-85%): status checks, health reports, simple alerts
- Tier 2 (10-25%): automation analysis, workflow design, optimization
- Tier 3 (5-10%): complex system architecture, multi-system integration
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from domain_agent_base import (
    DomainAgent, AgentOutput, RoutingResult, ModelTier, WORKSPACE
)

ETI_WORKSPACE = WORKSPACE / "workspace-eti"
AUTOMATION_INVENTORY = ETI_WORKSPACE / "AUTOMATION_INVENTORY.md"
HEALTH_CHECK_STATE = WORKSPACE / "state" / "health_check.json"


class EtiAgent(DomainAgent):
    """Automation and system monitoring domain agent."""
    
    AGENT_NAME = "אתי"
    AGENT_EMOJI = "🤖"
    DOMAIN = "automation"
    KEYWORDS = [
        "אוטומציה", "automation", "automate", "מוניטור", "monitor",
        "health", "בריאות מערכת", "בריאות המערכת", "status", "סטטוס מערכת",
        "alert", "התראה", "cron", "heartbeat",
        "script", "סקריפט", "workflow", "תהליך",
        "optimize", "אופטימיזציה", "bottleneck",
        "integration", "אינטגרציה", "API",
        "backup", "גיבוי", "log", "לוג",
    ]
    
    TASK_TYPES = {
        "health_check": {"tier": "tier1", "keywords": ["health", "בריאות", "status", "סטטוס מערכת"]},
        "alert_review": {"tier": "tier1", "keywords": ["alert", "התראה", "שגיאה", "error"]},
        "automation_status": {"tier": "tier1", "keywords": ["automation status", "מצב אוטומציות"]},
        "process_analysis": {"tier": "tier2", "keywords": ["analyze", "ניתוח תהליך", "workflow"]},
        "automation_design": {"tier": "tier2", "keywords": ["automate", "אוטומציה חדשה", "design"]},
        "optimization": {"tier": "tier2", "keywords": ["optimize", "אופטימיזציה", "improve", "שיפור"]},
        "system_architecture": {"tier": "tier3", "keywords": ["architecture", "ארכיטקטורה", "system design"]},
        "integration_plan": {"tier": "tier3", "keywords": ["integration", "אינטגרציה", "multi-system"]},
    }
    
    def can_handle(self, message: str, context: Dict, attachments: List[str] = None) -> RoutingResult:
        """Check if this is an automation/monitoring request."""
        score = self.keyword_match(message)
        
        # Boost for system-related queries
        if re.search(r'(health.?check|בריאות מערכת|system status)', message, re.IGNORECASE):
            score = max(score, 0.9)
        
        # Boost for automation requests
        if re.search(r'(אוטומציה|automate|automation)', message, re.IGNORECASE):
            score = max(score, 0.85)
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        
        return RoutingResult(
            can_handle=score >= 0.3,
            confidence=score,
            domain=self.DOMAIN,
            tier=tier,
            estimated_cost_usd=self.estimate_cost(tier),
            reason=f"Automation task: {task_type} → {tier.value}",
        )
    
    def process(self, message: str, context: Dict, attachments: List[str] = None) -> AgentOutput:
        """Process automation request."""
        self._start_timer()
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        
        inventory = self._load_inventory()
        health = self._load_health_state()
        
        prompt = self._build_prompt(task_type, message, inventory, health, context)
        
        return AgentOutput(
            decision="complete",
            confidence=0.85,
            domain=self.DOMAIN,
            agent_name=self.AGENT_NAME,
            model_tier=tier.value,
            cost_usd=self.estimate_cost(tier),
            summary=f"Automation task processed: {task_type}",
            details=prompt,
            draft={
                "type": task_type,
                "prompt_file": "agents/eti-automation/eti_prompt.md",
                "tier": tier.value,
                "inventory_loaded": inventory is not None,
                "health_loaded": health is not None,
            },
            tools_used=["read", "exec"],
            duration_ms=self._elapsed_ms(),
            qa_result="pass",
        )
    
    def _classify_task(self, message: str) -> str:
        msg = message.lower()
        for task_type, config in self.TASK_TYPES.items():
            if any(kw in msg for kw in config["keywords"]):
                return task_type
        return "health_check"
    
    def _get_tier(self, task_type: str) -> ModelTier:
        config = self.TASK_TYPES.get(task_type, {})
        tier_str = config.get("tier", "tier1")
        return {
            "tier1": ModelTier.TIER1_CHEAP,
            "tier2": ModelTier.TIER2_MID,
            "tier3": ModelTier.TIER3_PREMIUM,
        }.get(tier_str, ModelTier.TIER1_CHEAP)
    
    def _load_inventory(self) -> Optional[str]:
        try:
            return AUTOMATION_INVENTORY.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
    
    def _load_health_state(self) -> Optional[str]:
        try:
            return HEALTH_CHECK_STATE.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
    
    def _build_prompt(self, task_type: str, message: str, inventory: Optional[str],
                      health: Optional[str], context: Dict) -> str:
        return f"""You are אתי (Eti), an Automation & Monitoring Agent working under Dvorah.
Task: {task_type}
User message: {message}

Active Automations (from inventory):
{inventory[:2000] if inventory else 'No inventory loaded.'}

Health State:
{health[:1000] if health else 'No health data.'}

Guidelines:
- 10 active automations + 6 support scripts in current system
- Health check runs daily at 07:00
- Monitor 6 core systems: Outlook, Gmail, WhatsApp, Calendar, etc.
- Report issues factually, don't invent metrics
"""


def test_eti():
    eti = EtiAgent()
    print(f"Agent: {eti}")
    
    tests = [
        "מה מצב בריאות המערכת?",
        "תתכנני אוטומציה לגיבוי יומי",
        "האם יש התראות?",
        "מה מזג האוויר?",
    ]
    
    for msg in tests:
        result = eti.can_handle(msg, {"sender": "yoni"})
        print(f"\n'{msg}'")
        print(f"  Can handle: {result.can_handle} (conf: {result.confidence:.2f})")
        print(f"  Tier: {result.tier.value}")


if __name__ == "__main__":
    test_eti()
