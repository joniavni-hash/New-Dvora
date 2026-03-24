#!/usr/bin/env python3
"""
Domain Agent Base — Unified interface for all Dvorah domain agents.

Every domain agent inherits from DomainAgent and implements:
- can_handle(message, context, attachments) → routing decision
- process(message, context, attachments) → structured output

Architecture:
- Multi-tier cost optimization (Tier 1/2/3)
- Unified JSON output format
- Trace logging integration
- QA gate support
- Backward-compatible with existing orchestrator
"""

import json
import os
import re
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

# ============================================================
# MODEL TIERS (shared across all domain agents)
# ============================================================

class ModelTier(Enum):
    TIER1_CHEAP = "tier1"      # claude-sonnet-4-20250514 — 70-85% of work
    TIER2_MID = "tier2"        # claude-sonnet-4-20250514 (enhanced) — 10-25%
    TIER3_PREMIUM = "tier3"    # claude-opus-4-20250514 — 5-10%

TIER_TO_MODEL = {
    ModelTier.TIER1_CHEAP: "anthropic/claude-sonnet-4-20250514",
    ModelTier.TIER2_MID: "anthropic/claude-sonnet-4-20250514",
    ModelTier.TIER3_PREMIUM: "anthropic/claude-opus-4-20250514",
}

# Cost per 1M tokens (input, output) in USD
TIER_COSTS = {
    ModelTier.TIER1_CHEAP: (3.0, 15.0),
    ModelTier.TIER2_MID: (3.0, 15.0),
    ModelTier.TIER3_PREMIUM: (15.0, 75.0),
}


@dataclass
class RoutingResult:
    """Result of can_handle() — tells orchestrator whether this agent should handle."""
    can_handle: bool
    confidence: float  # 0-1
    domain: str
    tier: ModelTier = ModelTier.TIER1_CHEAP
    estimated_cost_usd: float = 0.0
    reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "canHandle": self.can_handle,
            "confidence": self.confidence,
            "domain": self.domain,
            "tier": self.tier.value,
            "estimatedCostUsd": round(self.estimated_cost_usd, 4),
            "reason": self.reason,
        }


@dataclass
class AgentOutput:
    """Standardized output from any domain agent."""
    decision: str        # "complete" | "partial" | "needs_approval" | "failed"
    confidence: float    # 0-1
    domain: str
    agent_name: str
    model_tier: str      # tier1/tier2/tier3
    cost_usd: float
    
    # Core output
    summary: str         # Human-readable summary
    details: str = ""    # Extended details if needed
    draft: Dict = field(default_factory=dict)  # Structured draft (for actions)
    
    # Metadata
    tools_used: List[str] = field(default_factory=list)
    duration_ms: int = 0
    qa_result: str = "pending"
    
    # State updates
    memory_delta: str = ""
    state_delta: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "domain": self.domain,
            "agentName": self.agent_name,
            "modelTier": self.model_tier,
            "costUsd": round(self.cost_usd, 4),
            "summary": self.summary,
            "details": self.details,
            "draft": self.draft,
            "toolsUsed": self.tools_used,
            "durationMs": self.duration_ms,
            "qaResult": self.qa_result,
            "memoryDelta": self.memory_delta,
            "stateDelta": self.state_delta,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class DomainAgent(ABC):
    """
    Base class for all domain agents.
    
    Subclasses must implement:
    - AGENT_NAME: str
    - AGENT_EMOJI: str
    - DOMAIN: str
    - KEYWORDS: list of detection keywords
    - can_handle(message, context, attachments) → RoutingResult
    - process(message, context, attachments) → AgentOutput
    """
    
    AGENT_NAME: str = "BaseAgent"
    AGENT_EMOJI: str = "🤖"
    DOMAIN: str = "general"
    KEYWORDS: List[str] = []
    
    # Complexity thresholds for tier routing
    TIER2_THRESHOLD: int = 45
    TIER3_THRESHOLD: int = 75
    
    def __init__(self):
        self._start_time = 0
    
    def _start_timer(self):
        self._start_time = time.time()
    
    def _elapsed_ms(self) -> int:
        return int((time.time() - self._start_time) * 1000)
    
    def keyword_match(self, message: str) -> float:
        """Score keyword match (0-1) for routing.
        1 match → 0.4, 2 matches → 0.65, 3+ → 0.8+
        """
        msg_lower = message.lower()
        matches = sum(1 for kw in self.KEYWORDS if kw in msg_lower)
        if not self.KEYWORDS or matches == 0:
            return 0.0
        # Scoring: 1 match = 0.4, 2 = 0.65, 3 = 0.8, 4+ = 0.9+
        if matches == 1:
            return 0.4
        elif matches == 2:
            return 0.65
        elif matches == 3:
            return 0.8
        return min(0.9 + (matches - 4) * 0.02, 1.0)
    
    def estimate_cost(self, tier: ModelTier, input_tokens: int = 2000, output_tokens: int = 1500) -> float:
        """Estimate cost in USD for a given tier."""
        input_cost, output_cost = TIER_COSTS[tier]
        return (input_tokens * input_cost + output_tokens * output_cost) / 1_000_000
    
    def select_tier(self, complexity_score: int, risk_level: str = "low") -> ModelTier:
        """Select model tier based on complexity and risk."""
        if complexity_score >= self.TIER3_THRESHOLD or risk_level in ("critical", "high"):
            return ModelTier.TIER3_PREMIUM
        elif complexity_score >= self.TIER2_THRESHOLD or risk_level == "medium":
            return ModelTier.TIER2_MID
        return ModelTier.TIER1_CHEAP
    
    @abstractmethod
    def can_handle(self, message: str, context: Dict, attachments: List[str] = None) -> RoutingResult:
        """Determine if this agent should handle the request."""
        pass
    
    @abstractmethod
    def process(self, message: str, context: Dict, attachments: List[str] = None) -> AgentOutput:
        """Process the request and return structured output."""
        pass
    
    def __repr__(self):
        return f"{self.AGENT_EMOJI} {self.AGENT_NAME} ({self.DOMAIN})"
