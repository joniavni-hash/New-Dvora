#!/usr/bin/env python3
"""
PolicyService — Structured constraint checking for Dvorah's Orchestrator.
Maps domains to policies and extracts actionable constraints.

Usage:
    python3 policy_service.py --domain group --action-type SEND
    python3 policy_service.py --domain email --action-type DRAFT
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
POLICIES_DIR = WORKSPACE / "policies"

# Domain → policy files mapping (from core/policy_engine.md)
DOMAIN_POLICIES = {
    "group": [
        "GROUP_BEHAVIOR_POLICY.md",
        "GROUP_INTELLIGENCE.md",
        "GROUP_QA.md",
        "PRIVACY_POLICY.md",
    ],
    "email": [
        "EXTERNAL_ACTIONS_POLICY.md",
        "PRIVACY_POLICY.md",
        "RESPONSE_STRATEGY_POLICY.md",
    ],
    "fitness": [],
    "legal": [
        "EXTERNAL_ACTIONS_POLICY.md",
        "PRIVACY_POLICY.md",
    ],
    "travel": [
        "EXTERNAL_ACTIONS_POLICY.md",
    ],
    "code": [
        "EXTERNAL_ACTIONS_POLICY.md",
    ],
    "research": [
        "RESEARCH_ESCALATION_POLICY.md",
        "EXTERNAL_ACTIONS_POLICY.md",
    ],
    "general": [
        "RESPONSE_STRATEGY_POLICY.md",
    ],
}

# Always loaded
ALWAYS_POLICIES = [
    "ACTION_LEVELS.md",
    "PRIVACY_POLICY.md",
]

# Approval routing (from core/approval_gate.md)
APPROVAL_MAP = {
    "READ": {"flow": "auto", "requires_yoni": False, "auto_approve": True},
    "DRAFT": {"flow": "dvorah_review", "requires_yoni": False, "auto_approve": False},
    "SEND": {"flow": "dvorah_approve", "requires_yoni": False, "auto_approve": False},
    "MUTATE": {"flow": "dvorah_only", "requires_yoni": False, "auto_approve": False},
}

# High-sensitivity signals that escalate to Yoni
HIGH_SENSITIVITY_SIGNALS = [
    "new_recipient",
    "external_email",
    "soul_change",
    "agents_change",
    "policy_change",
]


def extract_constraints(filepath: Path) -> list[str]:
    """Extract actionable constraints from a policy file.
    
    Looks for:
    - Bullet points with imperatives (לא, אסור, חובה, must, never, always)
    - Table rows with rules
    - Sections labeled "כללים" or "Rules"
    """
    if not filepath.exists():
        return [f"[policy not found: {filepath.name}]"]
    
    content = filepath.read_text(encoding="utf-8")
    constraints = []
    
    # Extract bullet-point rules
    rule_patterns = [
        r"^[-*]\s+(.+(?:לא|אסור|חובה|חייב|must|never|always|don't|do not).+)$",
        r"^[-*]\s+(.+→.+)$",  # Arrow patterns like "role=observer → no reply"
    ]
    
    for line in content.split("\n"):
        line = line.strip()
        for pattern in rule_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                constraints.append(match.group(1).strip())
                break
    
    # Extract from tables (lines with |)
    for line in content.split("\n"):
        line = line.strip()
        if "|" in line and ("→" in line or "חסום" in line or "block" in line.lower()):
            # Clean table formatting
            cells = [c.strip() for c in line.split("|") if c.strip() and c.strip() != "---"]
            if len(cells) >= 2:
                constraints.append(" | ".join(cells))
    
    # If no specific constraints found, extract section headers as general rules
    if not constraints:
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## ") and any(kw in line for kw in ["כלל", "Rule", "חובה", "אסור"]):
                constraints.append(line.lstrip("# ").strip())
    
    return constraints


def evaluate(domain: str, action_type: str, metadata: dict = None) -> dict:
    """Evaluate policies for a domain and action type."""
    metadata = metadata or {}
    
    # Collect policy files
    policy_files = list(ALWAYS_POLICIES)
    domain_policies = DOMAIN_POLICIES.get(domain, [])
    for p in domain_policies:
        if p not in policy_files:
            policy_files.append(p)
    
    # Memory write special case
    if action_type == "MUTATE" or metadata.get("is_memory_write"):
        if "MEMORY_POLICY.md" not in policy_files:
            policy_files.append("MEMORY_POLICY.md")
    
    # Extract constraints from each policy
    all_constraints = []
    loaded = []
    
    for pname in policy_files:
        ppath = POLICIES_DIR / pname
        if ppath.exists():
            loaded.append(pname)
            constraints = extract_constraints(ppath)
            all_constraints.extend(constraints)
    
    # Determine approval
    approval = APPROVAL_MAP.get(action_type, APPROVAL_MAP["READ"]).copy()
    
    # Check for high sensitivity
    sensitivity_signals = metadata.get("sensitivity_signals", [])
    if any(s in HIGH_SENSITIVITY_SIGNALS for s in sensitivity_signals):
        approval["requires_yoni"] = True
        approval["flow"] = "yoni_approve"
    
    # Group observer block
    if domain == "group" and metadata.get("role") == "observer":
        approval["flow"] = "blocked"
        approval["auto_approve"] = False
        all_constraints.insert(0, "BLOCKED: role=observer — no external actions allowed")
    
    return {
        "domain": domain,
        "action_type": action_type,
        "policies_loaded": loaded,
        "constraints": all_constraints,
        "constraint_count": len(all_constraints),
        "approval": approval,
    }


def main():
    parser = argparse.ArgumentParser(description="PolicyService — constraint checking")
    parser.add_argument("--domain", required=True, choices=list(DOMAIN_POLICIES.keys()))
    parser.add_argument("--action-type", required=True, choices=["READ", "DRAFT", "SEND", "MUTATE"])
    parser.add_argument("--role", default="", help="Group role (observer/responder/active)")
    parser.add_argument("--sensitivity", nargs="*", default=[], help="Sensitivity signals")
    args = parser.parse_args()
    
    metadata = {}
    if args.role:
        metadata["role"] = args.role
    if args.sensitivity:
        metadata["sensitivity_signals"] = args.sensitivity
    
    result = evaluate(args.domain, args.action_type, metadata)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
