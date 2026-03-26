#!/usr/bin/env python3
"""
Agent Registry — PR2: Real runtime dispatch.

PR2 changes:
- dispatch(agent_name, message, context) → FinalPayload
  This is the single dispatch point. agent_executor.py calls this; nothing else.
- Registry loads agents lazily; dispatch finds by name and calls execute().
- If agent not found or fails: returns error FinalPayload (Dvorah falls back).
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

AGENTS_DIR = Path(__file__).parent.parent
WORKSPACE   = AGENTS_DIR.parent

sys.path.insert(0, str(AGENTS_DIR / "_shared"))
sys.path.insert(0, str(AGENTS_DIR / "dana-fitness"))
sys.path.insert(0, str(AGENTS_DIR / "tali-marketing"))
sys.path.insert(0, str(AGENTS_DIR / "tzofit-research"))
sys.path.insert(0, str(AGENTS_DIR / "eti-automation"))
sys.path.insert(0, str(AGENTS_DIR / "odya-whatsapp"))

from domain_agent_base import DomainAgent, FinalPayload, RoutingResult


# ── Lazy agent loader ─────────────────────────────────────────────────────────

def _load_agents() -> List[DomainAgent]:
    agents = []

    for cls_name, mod_name in [
        ("DanaAgent",   "dana_agent"),
        ("OdyaAgent",   "odya_agent"),
        ("TzofitAgent", "tzofit_agent"),
        ("EtiAgent",    "eti_agent"),
        ("TaliAgent",   "tali_agent"),
    ]:
        try:
            mod = __import__(mod_name)
            cls = getattr(mod, cls_name)
            agents.append(cls())
        except Exception as e:
            print(f"[registry] warning: could not load {cls_name}: {e}",
                  file=sys.stderr)

    # Masha has a different module path
    try:
        sys.path.insert(0, str(AGENTS_DIR / "masha"))
        from masha_agent import MashaAgent
        agents.append(MashaAgent())
    except Exception as e:
        print(f"[registry] warning: could not load MashaAgent: {e}",
              file=sys.stderr)

    return agents


_agents: Optional[List[DomainAgent]] = None


def get_agents() -> List[DomainAgent]:
    global _agents
    if _agents is None:
        _agents = _load_agents()
    return _agents


def _find_agent(agent_name: str) -> Optional[DomainAgent]:
    """Find agent by AGENT_NAME (Hebrew or English, case-insensitive)."""
    name_lower = agent_name.lower().strip()
    for a in get_agents():
        if (a.AGENT_NAME.lower() == name_lower
                or a.DOMAIN.lower() == name_lower
                or a.__class__.__name__.lower() == name_lower + "agent"):
            return a
    return None


# ── PR2: Single dispatch entry point ─────────────────────────────────────────

def dispatch(agent_name: str, message: str, context: Dict,
             metadata: Dict = None) -> FinalPayload:
    """
    Route execution to the named agent and return its FinalPayload.

    Dvorah calls this; it never reaches inside agent internals directly.
    On failure, returns error FinalPayload so pipeline can fall back.
    """
    metadata = metadata or {}
    agent = _find_agent(agent_name)

    if agent is None:
        return FinalPayload(
            status="error",
            agent=agent_name,
            final_text="",
            should_send=False,
            requires_approval=False,
            metadata={
                "model_used":   "none",
                "model_reason": f"agent '{agent_name}' not found in registry",
                "output_mode":  "error",
            },
        )

    try:
        payload = agent.execute(message, {**context, **(metadata or {})})
        # Validate contract — must be FinalPayload
        if not isinstance(payload, FinalPayload):
            raise TypeError(
                f"{agent.__class__.__name__}.execute() returned "
                f"{type(payload).__name__}, expected FinalPayload"
            )
        return payload

    except Exception as e:
        return FinalPayload(
            status="error",
            agent=agent_name,
            final_text="",
            should_send=False,
            requires_approval=False,
            metadata={
                "model_used":   "none",
                "model_reason": f"execute() raised: {e}",
                "output_mode":  "error",
            },
        )


# ── Legacy routing (kept for agent_registry.route_message compat) ────────────

def find_best_agent(message: str, context: Dict,
                    attachments: List[str] = None) -> Tuple[Optional[DomainAgent],
                                                            Optional[RoutingResult]]:
    best_agent, best_result, best_conf = None, None, 0.0
    for agent in get_agents():
        result = agent.can_handle(message, context, attachments)
        if result.can_handle and result.confidence > best_conf:
            best_agent, best_result, best_conf = agent, result, result.confidence
    return best_agent, best_result


def route_message(message: str, source: str, metadata: Dict = None) -> Dict:
    metadata = metadata or {}
    context = {"source": source, **metadata}

    if source == "group":
        for agent in get_agents():
            if agent.DOMAIN == "group":
                result = agent.can_handle(message, context)
                return {"agent": agent.AGENT_NAME, "domain": agent.DOMAIN,
                        "model": result.tier.value, "confidence": result.confidence}

    agent, result = find_best_agent(message, context)
    if agent and result:
        return {"agent": agent.AGENT_NAME, "domain": agent.DOMAIN,
                "model": result.tier.value, "confidence": result.confidence}

    return {"agent": "direct", "domain": "general", "model": None, "confidence": 0.5}


# ── Inventory (unchanged) ─────────────────────────────────────────────────────

AGENT_INVENTORY = {
    "דנה":   {"emoji": "🏋️", "domain": "fitness",    "class": "DanaAgent"},
    "טלי":   {"emoji": "🏖️", "domain": "marketing",  "class": "TaliAgent"},
    "צופית": {"emoji": "🔍", "domain": "research",   "class": "TzofitAgent"},
    "אתי":   {"emoji": "🤖", "domain": "automation", "class": "EtiAgent"},
    "אודיה": {"emoji": "📱", "domain": "group",      "class": "OdyaAgent"},
    "מאשה":  {"emoji": "⚖️", "domain": "legal",      "class": "MashaAgent"},
    "דבורה": {"emoji": "👑", "domain": "general",    "class": "direct"},
}
