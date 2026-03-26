#!/usr/bin/env python3
"""
🏖️ טלי (Tali) — Villa Marketing Domain Agent

Handles: Villa Lithos social media marketing, content creation,
         performance tracking, and Larry's methodology integration.
Integrates with: villa-lithos-tiktok/larry-system/, workspace/villa-lithos/,
                 Postiz API for TikTok/Instagram automation.

Multi-tier routing:
- Tier 1 (70-85%): status checks, caption generation, hook variations, scheduling
- Tier 2 (10-25%): performance analysis, A/B test evaluation, content strategy
- Tier 3 (5-10%): comprehensive campaign planning, audience research, brand strategy
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from domain_agent_base import (
    DomainAgent, AgentOutput, FinalPayload, RoutingResult, ModelTier, WORKSPACE
)

LARRY_SYSTEM = WORKSPACE / "villa-lithos-tiktok" / "larry-system"
VILLA_CONFIG = WORKSPACE / "workspace" / "villa-lithos"


class TaliAgent(DomainAgent):
    """Villa Lithos marketing domain agent."""
    
    AGENT_NAME = "טלי"
    AGENT_EMOJI = "🏖️"
    DOMAIN = "marketing"
    KEYWORDS = [
        "villa", "וילה", "lithos", "ליתוס", "tiktok", "טיקטוק",
        "instagram", "אינסטגרם", "postiz", "פוסט", "post",
        "hook", "הוק", "caption", "slide", "שקופית", "carousel",
        "marketing", "שיווק", "content", "תוכן", "analytics",
        "performance", "ביצועים", "views", "צפיות", "engagement",
        "larry", "לארי", "campaign", "קמפיין",
    ]
    
    TASK_TYPES = {
        "status_check": {"tier": "tier1", "keywords": ["status", "מצב", "מה הסטטוס"]},
        "caption_gen": {"tier": "tier1", "keywords": ["caption", "כיתוב", "טקסט לפוסט"]},
        "hook_variation": {"tier": "tier1", "keywords": ["hook", "הוק", "variation", "וריאציה"]},
        "schedule_post": {"tier": "tier1", "keywords": ["schedule", "תזמן", "לפרסם", "post"]},
        "performance_check": {"tier": "tier2", "keywords": ["analytics", "ביצועים", "צפיות", "performance"]},
        "ab_test": {"tier": "tier2", "keywords": ["a/b", "test", "מבחן", "compare"]},
        "content_strategy": {"tier": "tier2", "keywords": ["strategy", "אסטרטגיה", "תוכנית תוכן"]},
        "campaign_plan": {"tier": "tier3", "keywords": ["campaign", "קמפיין", "תוכנית שיווק"]},
        "audience_research": {"tier": "tier3", "keywords": ["audience", "קהל", "research"]},
    }
    
    def can_handle(self, message: str, context: Dict, attachments: List[str] = None) -> RoutingResult:
        """Check if this is a marketing-related request."""
        score = self.keyword_match(message)
        
        # Strong signal: villa/lithos mention
        if re.search(r'(villa\s*lithos|וילה\s*ליתוס)', message, re.IGNORECASE):
            score = max(score, 0.95)
        
        # Medium signal: social media context
        if re.search(r'(tiktok|instagram|postiz|פוסט)', message, re.IGNORECASE):
            score = max(score, 0.7)
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        
        return RoutingResult(
            can_handle=score >= 0.3,
            confidence=score,
            domain=self.DOMAIN,
            tier=tier,
            estimated_cost_usd=self.estimate_cost(tier),
            reason=f"Marketing task: {task_type} → {tier.value}",
        )
    

    def execute(self, message: str, context: dict, attachments=None):
        """PR2 stub — returns FinalPayload."""
        from datetime import datetime
        task_type = self._classify_task(message) if hasattr(self, '_classify_task') else 'general'
        return FinalPayload(
            status="ok",
            agent=self.AGENT_NAME,
            final_text=f"[{self.AGENT_NAME}] {task_type}: {message[:80]}",
            should_send=True,
            requires_approval=False,
            metadata={
                "model_used":   "anthropic/claude-sonnet-4-20250514",
                "model_reason": f"{self.DOMAIN}/{task_type} — tier1",
                "output_mode":  "direct_send",
            },
        )

    def process(self, message: str, context: Dict, attachments: List[str] = None) -> AgentOutput:
        """Process marketing request."""
        self._start_timer()
        
        task_type = self._classify_task(message)
        tier = self._get_tier(task_type)
        
        # Load relevant data
        hook_data = self._load_hook_data()
        config = self._load_config()
        
        prompt = self._build_prompt(task_type, message, hook_data, config, context)
        
        return AgentOutput(
            decision="complete",
            confidence=0.85,
            domain=self.DOMAIN,
            agent_name=self.AGENT_NAME,
            model_tier=tier.value,
            cost_usd=self.estimate_cost(tier),
            summary=f"Marketing task processed: {task_type}",
            details=prompt,
            draft={
                "type": task_type,
                "prompt": prompt,
                "tier": tier.value,
                "larry_system_loaded": hook_data is not None,
            },
            tools_used=["read"],
            duration_ms=self._elapsed_ms(),
            qa_result="pass",
        )
    
    def _classify_task(self, message: str) -> str:
        msg = message.lower()
        for task_type, config in self.TASK_TYPES.items():
            if any(kw in msg for kw in config["keywords"]):
                return task_type
        return "status_check"
    
    def _get_tier(self, task_type: str) -> ModelTier:
        config = self.TASK_TYPES.get(task_type, {})
        tier_str = config.get("tier", "tier1")
        return {
            "tier1": ModelTier.TIER1_CHEAP,
            "tier2": ModelTier.TIER2_MID,
            "tier3": ModelTier.TIER3_PREMIUM,
        }.get(tier_str, ModelTier.TIER1_CHEAP)
    
    def _load_hook_data(self) -> Optional[str]:
        try:
            return (LARRY_SYSTEM / "hooks" / "hook-performance.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
    
    def _load_config(self) -> Optional[str]:
        try:
            return (LARRY_SYSTEM / "config" / "villa-lithos.json").read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
    
    def _build_prompt(self, task_type: str, message: str, hook_data: Optional[str], 
                      config: Optional[str], context: Dict) -> str:
        base = f"""You are טלי (Tali), Villa Lithos marketing agent working under Dvorah.
Task: {task_type}
User message: {message}

Larry's Decision Framework:
| Views | Action |
|-------|--------|
| 50K+ | 🚀 VIRAL — 3 variations immediately |
| 10K-50K | 🟢 STRONG — scale, increase frequency |
| 5K-10K | 🟡 GOOD — keep in rotation |
| 1K-5K | 🟠 DECENT — test 1 variation |
| <1K (twice) | 🔴 DROP — different category |

Hook Performance Data:
{hook_data or 'No performance data yet.'}

Config:
{config or 'No config loaded.'}
"""
        return base


def test_tali():
    tali = TaliAgent()
    print(f"Agent: {tali}")
    
    tests = [
        "מה הסטטוס של Villa Lithos?",
        "תכתבי caption לפוסט הבא בטיקטוק",
        "כמה צפיות קיבלנו השבוע?",
        "מה מזג האוויר?",
    ]
    
    for msg in tests:
        result = tali.can_handle(msg, {"sender": "yoni"})
        print(f"\n'{msg}'")
        print(f"  Can handle: {result.can_handle} (conf: {result.confidence:.2f})")
        print(f"  Tier: {result.tier.value}")


if __name__ == "__main__":
    test_tali()
