#!/usr/bin/env python3
"""
Orchestrator — Central routing and execution pipeline for Dvorah.
Replaces the 11-step manual flow with a programmatic pipeline.

This is the main entry point. It coordinates all services:
- ContextService: load relevant files
- PolicyService: check constraints
- QAService: validate agent output
- TraceService: log everything

Usage (active mode — default, produces routing decision):
    python3 orchestrator.py --message "שלח מייל לדני" --source dm
    python3 orchestrator.py --message "שלום" --source group --group-id "family" --role "active"

Usage (shadow mode — log only, compare with current flow):
    python3 orchestrator.py --message "מה מזג האוויר?" --source dm --shadow
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Import services
sys.path.insert(0, str(Path(__file__).parent))
from context_service import load_context
from policy_service import evaluate as evaluate_policy
from qa_service import run_qa
from trace_service import log_trace

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))


# ============================================================
# STEP 1: INTAKE
# ============================================================
def intake(message: str, source: str, metadata: dict = None) -> dict:
    """Parse incoming request into structured format."""
    metadata = metadata or {}
    return {
        "message": message,
        "source": source,  # dm | group | heartbeat | subagent_return
        "metadata": metadata,
        "timestamp": time.time(),
    }


# ============================================================
# STEP 3: CLASSIFY (intent + domain + action_type)
# ============================================================

# Domain detection keywords
DOMAIN_KEYWORDS = {
    "fitness": ["דיאטה", "משקל", "קלוריות", "אימון", "diet", "weight", "workout", "שקילה", "שקלתי", "אכלתי", "חלבון"],
    "email": ["מייל", "אימייל", "email", "outlook", "inbox", "דוא\"ל"],
    "legal": ["חוזה", "הסכם", "משפטי", "עו\"ד", "legal", "contract", "סעיף"],
    "travel": ["טיסה", "מלון", "flight", "hotel", "booking", "הזמנה", "נסיעה"],
    "marketing": ["villa", "וילה", "lithos", "ליתוס", "tiktok", "טיקטוק", "instagram", "postiz", "hook", "שיווק"],
    "automation": ["אוטומציה", "automation", "health check", "בריאות מערכת", "בריאות המערכת", "monitor", "סטטוס מערכת", "סטטוס המערכת"],
    "research": ["חקרי", "תחקרי", "research", "השוואה", "מחקר", "ניתוח שוק", "סקירה", "survey"],
}

# Intent detection patterns
INTENT_PATTERNS = {
    "action": [
        r"^(שלח|תשלחי|תדליקי|תכבי|send|turn|open|close|create|delete)",
        r"(תעשי|תבדקי|תריצי|תכתבי|תמחקי|תחפשי|הכיני|נסחי)",
    ],
    "question": [
        r"\?$",
        r"^(מה|מי|איפה|מתי|למה|איך|כמה|האם|what|who|where|when|why|how)",
    ],
    "tracking": [
        r"(סטטוס|מצב|status|update|עדכון|מה קורה עם)",
        r"(שקלתי|אכלתי|רצתי|הלכתי|התאמנתי)",  # Self-reporting → tracking/command
    ],
    "command": [
        r"^(עדכני|שמרי|זכרי|update|save|remember)",
    ],
}

# Action type inference
ACTION_TYPE_MAP = {
    "question": "READ",
    "tracking": "READ",
    "conversation": "READ",
    "action": "SEND",  # Default, may be overridden
    "command": "MUTATE",
}


def classify(request: dict) -> dict:
    """Classify request into intent, domain, action_type."""
    message = request["message"].lower()
    source = request["source"]
    metadata = request["metadata"]
    
    # Domain detection
    domain = "general"
    if source == "group":
        domain = "group"
    else:
        # Priority domains: research intent overrides content domains (travel, etc.)
        # Check high-priority domains first
        priority_order = ["research", "fitness", "legal", "marketing", "automation", "email", "travel"]
        for d in priority_order:
            keywords = DOMAIN_KEYWORDS.get(d, [])
            if any(kw in message for kw in keywords):
                domain = d
                break
    
    # Intent detection
    intent = "conversation"  # default
    for intent_type, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, request["message"], re.IGNORECASE):
                intent = intent_type
                break
        if intent != "conversation":
            break
    
    # Action type
    action_type = ACTION_TYPE_MAP.get(intent, "READ")
    
    # Override: sending messages is SEND
    if intent == "action" and any(kw in message for kw in ["שלח", "send", "תשלחי"]):
        action_type = "SEND"
    
    # Override: drafting is DRAFT
    if any(kw in message for kw in ["טיוטה", "draft", "הכיני", "נסחי"]):
        action_type = "DRAFT"
    
    # Confidence based on match strength
    confidence = 0.5
    if intent != "conversation":
        confidence = 0.7
    if domain != "general":
        confidence += 0.15
    
    return {
        "intent": intent,
        "domain": domain,
        "action_type": action_type,
        "confidence": min(confidence, 1.0),
    }


# ============================================================
# STEP 5: ROUTE (domain → agent)
# ============================================================

ROUTING_TABLE = {
    "group": {
        "agent": "אודיה",
        "prompt_file": "agents/odya-whatsapp/odya_prompt.md",
        "model": "multi-tier",  # Tier 1/2/3 via domain agent
    },
    "legal": {
        "agent": "מאשה",
        "prompt_file": "agents/legal-agent/advanced/",
        "model": "multi-tier",  # Tier 1/2/3 via model_router
    },
    "research": {
        "agent": "צופית",
        "prompt_file": "agents/tzofit-research/tzofit_prompt.md",
        "model": "multi-tier",
    },
    "fitness": {
        "agent": "דנה",
        "prompt_file": "agents/dana-fitness/dana_prompt.md",
        "model": "multi-tier",
    },
    "marketing": {
        "agent": "טלי",
        "prompt_file": "agents/tali-marketing/tali_prompt.md",
        "model": "multi-tier",
    },
    "automation": {
        "agent": "אתי",
        "prompt_file": "agents/eti-automation/eti_prompt.md",
        "model": "multi-tier",
    },
    "general": {
        "agent": "direct",
        "prompt_file": None,
        "model": None,
    },
    "email": {
        "agent": "direct",
        "prompt_file": None,
        "model": None,
    },
    "travel": {
        "agent": "direct",  # Phase 3
        "prompt_file": None,
        "model": None,
    },
}


def route(classification: dict) -> dict:
    """Determine which agent handles this request."""
    domain = classification["domain"]
    routing = ROUTING_TABLE.get(domain, ROUTING_TABLE["general"])
    
    # Simple conversation with no specific domain → direct (Dvorah handles)
    if classification["intent"] == "conversation" and domain == "general":
        return {"agent": "direct", "prompt_file": None, "model": None}
    
    # Domain agents handle their domains (fitness, marketing, etc.)
    # Even for questions — the domain agent provides context-aware answers
    return routing


# ============================================================
# FULL PIPELINE
# ============================================================

def run_pipeline(message: str, source: str, metadata: dict = None, shadow: bool = False) -> dict:
    """Run the full orchestrator pipeline."""
    start_time = time.time()
    metadata = metadata or {}
    
    # 1. INTAKE
    request = intake(message, source, metadata)
    
    # 2. CONTEXT
    domain_hint = "group" if source == "group" else "general"
    context = load_context(domain_hint, metadata)
    
    # 3. CLASSIFY
    classification = classify(request)
    
    # Update context with actual domain
    if classification["domain"] != domain_hint:
        context = load_context(classification["domain"], metadata)
    
    # 4. POLICY
    policy = evaluate_policy(
        classification["domain"],
        classification["action_type"],
        metadata,
    )
    
    # 5. ROUTE
    routing = route(classification)
    
    # 6-9: INVOKE → QA → APPROVE → EXECUTE
    # In active mode, Dvorah executes these steps using the pipeline decision.
    # In shadow mode, we stop here and just produce the decision.
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    pipeline_result = {
        "mode": "shadow" if shadow else "active",
        "classification": classification,
        "context_summary": {
            "files_loaded": context["files_loaded"],
            "tokens_estimate": context["tokens_estimate"],
        },
        "policy_summary": {
            "policies_loaded": policy["policies_loaded"],
            "constraint_count": policy["constraint_count"],
            "approval": policy["approval"],
        },
        "routing": routing,
        "duration_ms": duration_ms,
    }
    
    # 11. TRACE
    trace_entry = {
        "trigger": source,
        "domain": classification["domain"],
        "action_type": classification["action_type"],
        "agent": routing["agent"],
        "model": routing.get("model", "direct"),
        "context_loaded": context["files_loaded"],
        "agent_decision": f"classified as {classification['intent']} → {routing['agent']}",
        "qa_result": "skip" if shadow else "pending",
        "approval": policy["approval"]["flow"],
        "action_taken": "shadow_only" if shadow else "routed",
        "memory_writes": [],
        "duration_ms": duration_ms,
        "shadow_mode": shadow,
    }
    log_trace(trace_entry)
    
    return pipeline_result


def main():
    parser = argparse.ArgumentParser(description="Orchestrator — Dvorah's routing pipeline")
    parser.add_argument("--message", required=True, help="Incoming message")
    parser.add_argument("--source", required=True, choices=["dm", "group", "heartbeat", "subagent_return"])
    parser.add_argument("--group-id", default="", help="Group ID (for group source)")
    parser.add_argument("--role", default="", help="Group role")
    parser.add_argument("--shadow", action="store_true", help="Shadow mode (log only)")
    args = parser.parse_args()
    
    metadata = {}
    if args.group_id:
        metadata["group_id"] = args.group_id
    if args.role:
        metadata["role"] = args.role
    
    result = run_pipeline(args.message, args.source, metadata, shadow=args.shadow)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
