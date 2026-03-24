#!/usr/bin/env python3
"""
Agent Registry — Central registry of all domain agents.
Used by the orchestrator to discover and route to agents.

Agent lineup (7 total):
1. 🏋️ דנה (Dana) — Fitness & Nutrition
2. 🏖️ טלי (Tali) — Villa Marketing
3. 🔍 צופית (Tzofit) — Research
4. 🤖 אתי (Eti) — Automation & Monitoring
5. 📱 אודיה (Odya) — WhatsApp Groups
6. ⚖️ מאשה (Masha) — Legal (existing, via masha_advanced.py)
7. 👑 דבורה (Dvorah) — Direct/General (orchestrator itself)
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent paths
AGENTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENTS_DIR / "_shared"))
sys.path.insert(0, str(AGENTS_DIR / "dana-fitness"))
sys.path.insert(0, str(AGENTS_DIR / "tali-marketing"))
sys.path.insert(0, str(AGENTS_DIR / "tzofit-research"))
sys.path.insert(0, str(AGENTS_DIR / "eti-automation"))
sys.path.insert(0, str(AGENTS_DIR / "odya-whatsapp"))

from domain_agent_base import DomainAgent, RoutingResult


def _lazy_load_agents() -> List[DomainAgent]:
    """Lazy-load all domain agents."""
    agents = []
    
    try:
        from dana_agent import DanaAgent
        agents.append(DanaAgent())
    except ImportError as e:
        print(f"Warning: Could not load DanaAgent: {e}", file=sys.stderr)
    
    try:
        from tali_agent import TaliAgent
        agents.append(TaliAgent())
    except ImportError as e:
        print(f"Warning: Could not load TaliAgent: {e}", file=sys.stderr)
    
    try:
        from tzofit_agent import TzofitAgent
        agents.append(TzofitAgent())
    except ImportError as e:
        print(f"Warning: Could not load TzofitAgent: {e}", file=sys.stderr)
    
    try:
        from eti_agent import EtiAgent
        agents.append(EtiAgent())
    except ImportError as e:
        print(f"Warning: Could not load EtiAgent: {e}", file=sys.stderr)
    
    try:
        from odya_agent import OdyaAgent
        agents.append(OdyaAgent())
    except ImportError as e:
        print(f"Warning: Could not load OdyaAgent: {e}", file=sys.stderr)
    
    return agents


# Cached agents
_agents: Optional[List[DomainAgent]] = None


def get_agents() -> List[DomainAgent]:
    """Get all registered domain agents."""
    global _agents
    if _agents is None:
        _agents = _lazy_load_agents()
    return _agents


def find_best_agent(message: str, context: Dict, attachments: List[str] = None) -> Tuple[Optional[DomainAgent], Optional[RoutingResult]]:
    """
    Find the best agent for a given message.
    Returns (agent, routing_result) or (None, None) for direct handling.
    """
    best_agent = None
    best_result = None
    best_confidence = 0.0
    
    for agent in get_agents():
        result = agent.can_handle(message, context, attachments)
        if result.can_handle and result.confidence > best_confidence:
            best_agent = agent
            best_result = result
            best_confidence = result.confidence
    
    return best_agent, best_result


def route_message(message: str, source: str, metadata: Dict = None) -> Dict:
    """
    Route a message to the appropriate agent.
    Returns routing decision compatible with orchestrator.py format.
    """
    metadata = metadata or {}
    context = {
        "source": source,
        **metadata,
    }
    
    # Group messages always go to Odya
    if source == "group":
        context["source"] = "group"
        agents = get_agents()
        for agent in agents:
            if agent.DOMAIN == "group":
                result = agent.can_handle(message, context)
                return {
                    "agent": agent.AGENT_NAME,
                    "agent_class": agent.__class__.__name__,
                    "domain": agent.DOMAIN,
                    "prompt_file": f"agents/odya-whatsapp/odya_prompt.md",
                    "model": result.tier.value,
                    "confidence": result.confidence,
                    "estimated_cost": result.estimated_cost_usd,
                }
    
    # Find best agent
    agent, result = find_best_agent(message, context)
    
    if agent and result:
        # Map agent to prompt file
        prompt_files = {
            "fitness": "agents/dana-fitness/dana_prompt.md",
            "marketing": "agents/tali-marketing/tali_prompt.md",
            "research": "agents/tzofit-research/tzofit_prompt.md",
            "automation": "agents/eti-automation/eti_prompt.md",
            "group": "agents/odya-whatsapp/odya_prompt.md",
        }
        
        return {
            "agent": agent.AGENT_NAME,
            "agent_class": agent.__class__.__name__,
            "domain": agent.DOMAIN,
            "prompt_file": prompt_files.get(agent.DOMAIN, None),
            "model": result.tier.value,
            "confidence": result.confidence,
            "estimated_cost": result.estimated_cost_usd,
        }
    
    # Default: direct handling by Dvorah
    return {
        "agent": "direct",
        "agent_class": None,
        "domain": "general",
        "prompt_file": None,
        "model": None,
        "confidence": 0.5,
        "estimated_cost": 0.0,
    }


# ============================================================
# AGENT INVENTORY (for documentation and status)
# ============================================================

AGENT_INVENTORY = {
    "דנה": {
        "emoji": "🏋️",
        "domain": "fitness",
        "class": "DanaAgent",
        "dir": "agents/dana-fitness/",
        "prompt": "agents/dana-fitness/dana_prompt.md",
        "tier_split": "T1:80% T2:15% T3:5%",
        "integrations": ["state/fitness_tracker.md", "HEARTBEAT.md"],
    },
    "טלי": {
        "emoji": "🏖️",
        "domain": "marketing",
        "class": "TaliAgent",
        "dir": "agents/tali-marketing/",
        "prompt": "agents/tali-marketing/tali_prompt.md",
        "tier_split": "T1:70% T2:20% T3:10%",
        "integrations": ["villa-lithos-tiktok/larry-system/", "Postiz API"],
    },
    "צופית": {
        "emoji": "🔍",
        "domain": "research",
        "class": "TzofitAgent",
        "dir": "agents/tzofit-research/",
        "prompt": "agents/tzofit-research/tzofit_prompt.md",
        "tier_split": "T1:70% T2:20% T3:10%",
        "integrations": ["web_search", "web_fetch", "pdf"],
    },
    "אתי": {
        "emoji": "🤖",
        "domain": "automation",
        "class": "EtiAgent",
        "dir": "agents/eti-automation/",
        "prompt": "agents/eti-automation/eti_prompt.md",
        "tier_split": "T1:75% T2:20% T3:5%",
        "integrations": ["workspace-eti/", "scripts/health_check.py", "HEARTBEAT.md"],
    },
    "אודיה": {
        "emoji": "📱",
        "domain": "group",
        "class": "OdyaAgent",
        "dir": "agents/odya-whatsapp/",
        "prompt": "agents/odya-whatsapp/odya_prompt.md",
        "tier_split": "T1:85% T2:10% T3:5%",
        "integrations": ["state/KNOWN_GROUPS.md", "scripts/group_messages.py"],
    },
    "מאשה": {
        "emoji": "⚖️",
        "domain": "legal",
        "class": "MashaAdvanced",
        "dir": "agents/legal-agent/",
        "prompt": "agents/legal-agent/legal_agent_prompt.md",
        "tier_split": "T1:70% T2:20% T3:10%",
        "integrations": ["scripts/masha_mvp.py", "legal_intent_classifier.py"],
    },
    "דבורה": {
        "emoji": "👑",
        "domain": "general",
        "class": "direct",
        "dir": "(orchestrator)",
        "prompt": "SOUL.md + IDENTITY.md",
        "tier_split": "N/A (uses session model)",
        "integrations": ["All services", "state/", "memory/"],
    },
}


def print_inventory():
    """Print agent inventory."""
    print("\n" + "=" * 60)
    print("🎭 DOMAIN AGENTS — Complete Inventory")
    print("=" * 60)
    for name, info in AGENT_INVENTORY.items():
        print(f"\n{info['emoji']} {name}")
        print(f"   Domain: {info['domain']}")
        print(f"   Class:  {info['class']}")
        print(f"   Tiers:  {info['tier_split']}")
        print(f"   Dir:    {info['dir']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_inventory()
    
    print("\n\n--- Routing Tests ---")
    test_messages = [
        ("אכלתי סלט עם ביצים", "dm"),
        ("מה הסטטוס של Villa Lithos?", "dm"),
        ("תחקרי טיסות ליוון", "dm"),
        ("מה מצב בריאות המערכת?", "dm"),
        ("שלום דבורה, מתי הפגישה?", "group"),
        ("מה השעה?", "dm"),
    ]
    
    for msg, source in test_messages:
        result = route_message(msg, source)
        print(f"\n'{msg}' ({source})")
        print(f"  → {result['agent']} ({result['domain']}) "
              f"[conf: {result['confidence']:.2f}, model: {result['model']}]")
