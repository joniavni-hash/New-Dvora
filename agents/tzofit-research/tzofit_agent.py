#!/usr/bin/env python3
"""
🔍 צופית (Tzofit) — Research Domain Agent

Handles: systematic research, market analysis, competitive intelligence,
         fact-checking, data gathering from web sources.

Multi-tier routing:
- Tier 1 (70-85%): quick-check, simple fact lookup, single-source queries
- Tier 2 (10-25%): focused research, multi-source cross-referencing, analysis
- Tier 3 (5-10%): broad/deep research, comprehensive market analysis, reports
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


class TzofitAgent(DomainAgent):
    """Research domain agent."""
    
    AGENT_NAME = "צופית"
    AGENT_EMOJI = "🔍"
    DOMAIN = "research"
    KEYWORDS = [
        "חקרי", "תחקרי", "research", "חיפוש", "מחקר",
        "השוואה", "compare", "analysis", "ניתוח",
        "מתחרים", "competitive", "שוק", "market",
        "מצאי", "תמצאי", "find", "בדקי", "תבדקי",
        "מה ההבדל", "מה עדיף", "אפשרויות",
        "סקירה", "review", "survey", "סקר",
    ]
    
    TASK_TYPES = {
        "quick_check": {"tier": "tier1", "keywords": ["בדקי", "תבדקי", "check"]},
        "fact_lookup": {"tier": "tier1", "keywords": ["מצאי", "תמצאי", "find", "מה"]},
        "comparison": {"tier": "tier2", "keywords": ["השוואה", "compare", "מה עדיף", "מה ההבדל"]},
        "focused_research": {"tier": "tier2", "keywords": ["חקרי", "תחקרי", "research"]},
        "market_analysis": {"tier": "tier3", "keywords": ["שוק", "market", "analysis"]},
        "competitive_intel": {"tier": "tier3", "keywords": ["מתחרים", "competitive"]},
        "deep_survey": {"tier": "tier3", "keywords": ["סקירה", "survey", "סקר מקיף"]},
    }
    
    # Scope mapping for prompt generation
    TASK_TO_SCOPE = {
        "quick_check": "quick-check",
        "fact_lookup": "quick-check",
        "comparison": "focused",
        "focused_research": "focused",
        "market_analysis": "broad",
        "competitive_intel": "broad",
        "deep_survey": "broad",
    }
    
    def can_handle(self, message: str, context: Dict, attachments: List[str] = None) -> RoutingResult:
        """Check if this is a research request."""
        score = self.keyword_match(message)
        
        # Boost for explicit research requests
        if re.search(r'(תחקרי|חקרי|research)', message, re.IGNORECASE):
            score = max(score, 0.9)
        
        # Boost for comparison requests
        if re.search(r'(השוואה|compare|מה עדיף|מה ההבדל)', message, re.IGNORECASE):
            score = max(score, 0.8)
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        
        return RoutingResult(
            can_handle=score >= 0.3,
            confidence=score,
            domain=self.DOMAIN,
            tier=tier,
            estimated_cost_usd=self.estimate_cost(tier),
            reason=f"Research task: {task_type} → {tier.value}",
        )
    
    def process(self, message: str, context: Dict, attachments: List[str] = None) -> AgentOutput:
        """Process research request — returns prompt for spawning."""
        self._start_timer()
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        scope = self.TASK_TO_SCOPE.get(task_type, "focused")
        
        return AgentOutput(
            decision="complete",
            confidence=0.85,
            domain=self.DOMAIN,
            agent_name=self.AGENT_NAME,
            model_tier=tier.value,
            cost_usd=self.estimate_cost(tier),
            summary=f"Research task: {task_type} (scope: {scope})",
            details="",
            draft={
                "type": task_type,
                "scope": scope,
                "prompt_file": "agents/tzofit-research/tzofit_prompt.md",
                "tier": tier.value,
                "input": {
                    "question": message,
                    "context": context.get("additional_context", ""),
                    "scope": scope,
                    "language": "auto",
                },
            },
            tools_used=[],
            duration_ms=self._elapsed_ms(),
            qa_result="pass",
        )
    
    def _classify_task(self, message: str) -> str:
        msg = message.lower()
        for task_type, config in self.TASK_TYPES.items():
            if any(kw in msg for kw in config["keywords"]):
                return task_type
        return "fact_lookup"
    
    def _get_tier(self, task_type: str) -> ModelTier:
        config = self.TASK_TYPES.get(task_type, {})
        tier_str = config.get("tier", "tier1")
        return {
            "tier1": ModelTier.TIER1_CHEAP,
            "tier2": ModelTier.TIER2_MID,
            "tier3": ModelTier.TIER3_PREMIUM,
        }.get(tier_str, ModelTier.TIER1_CHEAP)


def test_tzofit():
    tzofit = TzofitAgent()
    print(f"Agent: {tzofit}")
    
    tests = [
        "תחקרי טיסות למינכן באוגוסט",
        "מה ההבדל בין Postiz ל-Buffer?",
        "בדקי מה שעות הפתיחה של איקאה",
        "ניתוח שוק השכרת וילות ביוון",
    ]
    
    for msg in tests:
        result = tzofit.can_handle(msg, {"sender": "yoni"})
        print(f"\n'{msg}'")
        print(f"  Can handle: {result.can_handle} (conf: {result.confidence:.2f})")
        print(f"  Tier: {result.tier.value}")


if __name__ == "__main__":
    test_tzofit()
