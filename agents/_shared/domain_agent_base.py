#!/usr/bin/env python3
"""
Domain Agent Base — PR2: Agent-First Execution

Adds FinalPayload: unified contract every agent must return.
Dvorah receives FinalPayload and only does: QA, approval, delivery, fallback.
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


# ── Model tiers ───────────────────────────────────────────────────────────────

class ModelTier(Enum):
    TIER1_CHEAP   = "tier1"
    TIER2_MID     = "tier2"
    TIER3_PREMIUM = "tier3"

TIER_TO_MODEL = {
    ModelTier.TIER1_CHEAP:   "anthropic/claude-sonnet-4-20250514",
    ModelTier.TIER2_MID:     "anthropic/claude-sonnet-4-20250514",
    ModelTier.TIER3_PREMIUM: "anthropic/claude-opus-4-20250514",
}

TIER_COSTS = {
    ModelTier.TIER1_CHEAP:   (3.0,  15.0),
    ModelTier.TIER2_MID:     (3.0,  15.0),
    ModelTier.TIER3_PREMIUM: (15.0, 75.0),
}


# ── Routing result (can_handle output) ───────────────────────────────────────

@dataclass
class RoutingResult:
    can_handle: bool
    confidence: float
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


# ── PR2: FinalPayload — unified agent output contract ─────────────────────────

@dataclass
class FinalPayload:
    """
    Every agent execute() call returns exactly this.
    Dvorah does NOT rewrite final_text. It approves, delivers, or blocks.

    status values:
      "ok"               — ready to send, no approval needed
      "needs_approval"   — draft ready, must be approved before sending
      "no_reply"         — silent (group noise, irrelevant, etc.)
      "error"            — agent failed, Dvorah falls back
    """
    status: str                              # ok | needs_approval | no_reply | error
    agent: str                               # human-readable agent name (e.g. "מאשה")
    final_text: str                          # actual text to send (or "" for no_reply/error)
    should_send: bool                        # True = ready for delivery
    requires_approval: bool                  # True = needs human/Dvorah approval gate
    write_actions: List[Dict] = field(default_factory=list)
    # ^ list of {"type": "append_file", "path": "...", "content": "..."}
    metadata: Dict = field(default_factory=dict)
    # ^ must include: model_used, model_reason, output_mode

    def to_dict(self) -> Dict:
        return {
            "status":           self.status,
            "agent":            self.agent,
            "final_text":       self.final_text,
            "should_send":      self.should_send,
            "requires_approval": self.requires_approval,
            "write_actions":    self.write_actions,
            "metadata":         self.metadata,
        }


# ── AgentOutput (legacy — kept for backward compat, not used in PR2 pipeline) ─

@dataclass
class AgentOutput:
    decision: str
    confidence: float
    domain: str
    agent_name: str
    model_tier: str
    cost_usd: float
    summary: str
    details: str = ""
    draft: Dict = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    duration_ms: int = 0
    qa_result: str = "pending"
    memory_delta: str = ""
    state_delta: str = ""

    def to_dict(self) -> Dict:
        return {
            "decision": self.decision, "confidence": self.confidence,
            "domain": self.domain, "agentName": self.agent_name,
            "modelTier": self.model_tier, "costUsd": round(self.cost_usd, 4),
            "summary": self.summary, "details": self.details,
            "draft": self.draft, "toolsUsed": self.tools_used,
            "durationMs": self.duration_ms, "qaResult": self.qa_result,
        }


# ── DomainAgent base class ────────────────────────────────────────────────────

class DomainAgent(ABC):
    """
    All domain agents inherit from this.

    PR2 requirement: implement execute() → FinalPayload
    Legacy: process() still accepted but not used by PR2 pipeline.
    """

    AGENT_NAME: str = "BaseAgent"
    AGENT_EMOJI: str = "🤖"
    DOMAIN: str = "general"
    KEYWORDS: List[str] = []

    TIER2_THRESHOLD: int = 45
    TIER3_THRESHOLD: int = 75

    def __init__(self):
        self._start_time = 0

    def _start_timer(self):
        self._start_time = time.time()

    def _elapsed_ms(self) -> int:
        return int((time.time() - self._start_time) * 1000)

    def keyword_match(self, message: str) -> float:
        msg_lower = message.lower()
        matches = sum(1 for kw in self.KEYWORDS if kw in msg_lower)
        if not self.KEYWORDS or matches == 0:
            return 0.0
        if matches == 1: return 0.4
        if matches == 2: return 0.65
        if matches == 3: return 0.8
        return min(0.9 + (matches - 4) * 0.02, 1.0)

    def estimate_cost(self, tier: ModelTier, input_tokens: int = 2000,
                      output_tokens: int = 1500) -> float:
        ic, oc = TIER_COSTS[tier]
        return (input_tokens * ic + output_tokens * oc) / 1_000_000

    def select_tier(self, complexity_score: int,
                    risk_level: str = "low") -> ModelTier:
        if complexity_score >= self.TIER3_THRESHOLD or risk_level in ("critical", "high"):
            return ModelTier.TIER3_PREMIUM
        if complexity_score >= self.TIER2_THRESHOLD or risk_level == "medium":
            return ModelTier.TIER2_MID
        return ModelTier.TIER1_CHEAP

    @abstractmethod
    def can_handle(self, message: str, context: Dict,
                   attachments: List[str] = None) -> RoutingResult:
        pass

    @abstractmethod
    def execute(self, message: str, context: Dict,
                attachments: List[str] = None) -> FinalPayload:
        """
        PR2: replaces process().
        Must return FinalPayload — no scaffold statuses.
        """
        pass

    # Legacy shim — subclasses that haven't migrated yet fall back here
    def process(self, message: str, context: Dict,
                attachments: List[str] = None) -> AgentOutput:
        raise NotImplementedError(
            f"{self.__class__.__name__}.process() not implemented — use execute()"
        )

    def __repr__(self):
        return f"{self.AGENT_EMOJI} {self.AGENT_NAME} ({self.DOMAIN})"
