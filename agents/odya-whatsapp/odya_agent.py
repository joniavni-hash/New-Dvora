#!/usr/bin/env python3
"""
📱 אודיה (Odya) — WhatsApp Group Domain Agent

Handles: WhatsApp group message analysis, response decisions,
         group memory, role-based behavior.
Integrates with: state/KNOWN_GROUPS.md, state/GROUP_MEMORY.md,
                 scripts/group_messages.py, scripts/group_agent_context.py.

Multi-tier routing:
- Tier 1 (70-85%): noise filtering, simple replies, reaction suggestions
- Tier 2 (10-25%): context-heavy responses, proxy questions, research-backed answers
- Tier 3 (5-10%): sensitive group dynamics, representative mode, complex proxy

Backward compatible with existing whatsapp_group_agent.py interface.
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


class OdyaAgent(DomainAgent):
    """WhatsApp group messaging domain agent."""
    
    AGENT_NAME = "אודיה"
    AGENT_EMOJI = "📱"
    DOMAIN = "group"
    KEYWORDS = [
        "קבוצה", "group", "whatsapp", "וואטסאפ",
        "הודעה", "message", "תגובה", "reply",
        "דבורה", "דבי",  # Direct mentions in groups
    ]
    
    TASK_TYPES = {
        "noise_filter": {"tier": "tier1", "keywords": []},  # Default for most messages
        "simple_reply": {"tier": "tier1", "keywords": ["דבורה", "דבי"]},
        "reaction": {"tier": "tier1", "keywords": []},
        "proxy_response": {"tier": "tier2", "keywords": ["יוני", "yoni"]},
        "research_reply": {"tier": "tier2", "keywords": ["מה", "איך", "כמה", "?"]},
        "sensitive_reply": {"tier": "tier3", "keywords": []},
        "representative": {"tier": "tier3", "keywords": []},
    }
    
    def can_handle(self, message: str, context: Dict, attachments: List[str] = None) -> RoutingResult:
        """Check if this is a group message to handle."""
        # Group messages are always routed here by the orchestrator
        source = context.get("source", "")
        if source == "group":
            return RoutingResult(
                can_handle=True,
                confidence=0.95,
                domain=self.DOMAIN,
                tier=self._assess_tier(message, context),
                estimated_cost_usd=self.estimate_cost(ModelTier.TIER1_CHEAP),
                reason="Group message → Odya",
            )
        
        score = self.keyword_match(message)
        return RoutingResult(
            can_handle=score >= 0.5,
            confidence=score,
            domain=self.DOMAIN,
            tier=ModelTier.TIER1_CHEAP,
            estimated_cost_usd=self.estimate_cost(ModelTier.TIER1_CHEAP),
            reason=f"Group-related query (score: {score:.2f})",
        )
    
    def process(self, message: str, context: Dict, attachments: List[str] = None) -> AgentOutput:
        """Process group message — prepare for spawning with prompt."""
        self._start_timer()
        
        tier = self._assess_tier(message, context)
        role = context.get("role", "active")
        group_id = context.get("group_id", "unknown")
        
        return AgentOutput(
            decision="complete",
            confidence=0.85,
            domain=self.DOMAIN,
            agent_name=self.AGENT_NAME,
            model_tier=tier.value,
            cost_usd=self.estimate_cost(tier),
            summary=f"Group message processed for {group_id} (role: {role})",
            details="",
            draft={
                "type": "group_response",
                "prompt_file": "agents/odya-whatsapp/odya_prompt.md",
                "tier": tier.value,
                "group_id": group_id,
                "role": role,
                "prepare_cmd": f'python3 agents/whatsapp_group_agent.py --prepare --group-id "{group_id}"',
            },
            tools_used=[],
            duration_ms=self._elapsed_ms(),
            qa_result="pass",
        )
    
    def _assess_tier(self, message: str, context: Dict) -> ModelTier:
        """Assess which tier is needed based on message + context."""
        role = context.get("role", "active")
        
        # Observer → always Tier 1 (just to confirm silence)
        if role == "observer":
            return ModelTier.TIER1_CHEAP
        
        # Representative mode → Tier 3 (speaking for Yoni)
        if role == "representative":
            return ModelTier.TIER3_PREMIUM
        
        # Direct mention of דבורה + complex question → Tier 2
        if re.search(r'(דבורה|דבי)', message) and '?' in message:
            return ModelTier.TIER2_MID
        
        # Default: Tier 1
        return ModelTier.TIER1_CHEAP


# Backward compatibility: maintain existing interface
def prepare_group_response(group_id: str, new_message: dict) -> dict:
    """Backward-compatible wrapper for existing orchestrator calls."""
    agent = OdyaAgent()
    context = {
        "source": "group",
        "group_id": group_id,
        "role": new_message.get("role", "active"),
    }
    result = agent.process(
        new_message.get("text", ""),
        context,
    )
    return result.to_dict()


def test_odya():
    odya = OdyaAgent()
    print(f"Agent: {odya}")
    
    tests = [
        ("שלום לכולם", {"source": "group", "role": "observer"}),
        ("דבורה, מתי הפגישה?", {"source": "group", "role": "active"}),
        ("יוני, אתה מגיע?", {"source": "group", "role": "representative"}),
    ]
    
    for msg, ctx in tests:
        result = odya.can_handle(msg, ctx)
        print(f"\n'{msg}' (role: {ctx.get('role')})")
        print(f"  Can handle: {result.can_handle} (conf: {result.confidence:.2f})")
        print(f"  Tier: {result.tier.value}")


if __name__ == "__main__":
    test_odya()
