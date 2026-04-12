#!/usr/bin/env python3
"""
QAService — 6-check quality gate for Dvorah's Orchestrator.
Validates agent output before any external action.

Usage:
    echo '{"decision":"reply","draft":"שלום","confidence":0.8}' | python3 qa_service.py --domain group
    python3 qa_service.py --domain group --input '{"decision":"reply","draft":"test"}'
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class CheckResult:
    name: str
    passed: bool
    severity: str  # "block" | "warn"
    detail: str


def check_factual_fit(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 1: Facts accurate, sources real, tools used when needed."""
    issues = []
    
    # Check if agent claims to have searched but no evidence
    draft = output.get("draft", output.get("draftReply", ""))
    reasoning = output.get("reasoning", "")
    
    # Flag fabricated-looking URLs
    url_pattern = r'https?://[^\s\])]+'
    urls = re.findall(url_pattern, draft)
    if urls:
        issues.append(f"Contains {len(urls)} URL(s) — verify they're real")
    
    # Check confidence vs content
    confidence = output.get("confidence", 0.5)
    if confidence > 0.9 and len(draft) > 200:
        # High confidence + long response — worth double-checking
        issues.append("High confidence with long response — verify claims")
    
    if issues:
        return CheckResult("factual_fit", True, "warn", "; ".join(issues))
    return CheckResult("factual_fit", True, "warn", "no issues detected")


def check_style_fit(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 2: Tone/length/language matches target."""
    draft = output.get("draft", output.get("draftReply", ""))
    issues = []
    
    if not draft:
        return CheckResult("style_fit", True, "warn", "no draft to check")
    
    # Check for overly formal language in group context
    if domain == "group":
        formal_markers = ["בכבוד רב", "לכבוד", "הנדון:", "Dear ", "Sincerely"]
        for marker in formal_markers:
            if marker in draft:
                issues.append(f"Formal language '{marker}' in group context")
    
    # Check for Dvorah anti-patterns (from SOUL.md)
    anti_patterns = ["אשמח לעזור", "שאלה מעניינת", "בהצלחה!", "Great question"]
    for pattern in anti_patterns:
        if pattern in draft:
            issues.append(f"Anti-pattern detected: '{pattern}'")
    
    # Length check
    if domain == "group" and len(draft) > 500:
        issues.append(f"Draft is {len(draft)} chars — too long for group message")
    
    if issues:
        return CheckResult("style_fit", False, "warn", "; ".join(issues))
    return CheckResult("style_fit", True, "warn", "style OK")


def check_policy_fit(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 3: Complies with loaded policy constraints."""
    issues = []
    
    decision = output.get("decision", output.get("shouldReply", ""))
    
    # Check observer role constraint
    for c in constraints:
        if "observer" in c.lower() and "block" in c.lower():
            if decision in [True, "reply", "send"]:
                issues.append("BLOCKED: Trying to reply in observer-role group")
                return CheckResult("policy_fit", False, "block", "; ".join(issues))
    
    # Check for direct sending (agents should only draft)
    if output.get("action_taken") in ["sent", "send"]:
        issues.append("Agent attempted direct send — must return draft only")
        return CheckResult("policy_fit", False, "block", "; ".join(issues))
    
    if issues:
        return CheckResult("policy_fit", False, "warn", "; ".join(issues))
    return CheckResult("policy_fit", True, "warn", "policy compliant")


def check_risk(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 4: Privacy/embarrassment/conflict/accuracy risks."""
    draft = output.get("draft", output.get("draftReply", ""))
    issues = []
    
    # Privacy: check for personal info patterns
    privacy_patterns = [
        (r'\b\d{9,10}\b', "phone number"),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', "email address"),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP address"),
        (r'תעודת זהות|ת\.ז\.|ID number', "ID reference"),
    ]
    
    for pattern, label in privacy_patterns:
        if re.search(pattern, draft):
            issues.append(f"Potential {label} exposure in draft")
    
    # Conflict detection
    conflict_words = ["טועה", "טיפש", "מגוחך", "stupid", "wrong", "idiot"]
    for word in conflict_words:
        if word in draft.lower():
            issues.append(f"Conflict-risk word: '{word}'")
    
    if issues:
        severity = "block" if any("exposure" in i for i in issues) else "warn"
        return CheckResult("risk_check", False, severity, "; ".join(issues))
    return CheckResult("risk_check", True, "warn", "no risks detected")


def check_missing_context(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 5: Critical info gaps, guessing vs knowing."""
    issues = []
    
    confidence = output.get("confidence", 0.5)
    
    # Low confidence flag
    if confidence < 0.4:
        issues.append(f"Low confidence ({confidence}) — likely missing context")
    
    # Check if agent flagged missing info
    reasoning = output.get("reasoning", "")
    uncertain_markers = ["לא בטוח", "אולי", "might", "not sure", "assume", "מניח"]
    for marker in uncertain_markers:
        if marker in reasoning.lower():
            issues.append(f"Uncertainty in reasoning: '{marker}'")
    
    if issues:
        return CheckResult("missing_context", False, "warn", "; ".join(issues))
    return CheckResult("missing_context", True, "warn", "context appears sufficient")


def check_wrong_action(output: dict, domain: str, constraints: list) -> CheckResult:
    """Check 6: Correct tool, answers what was asked, within role."""
    issues = []
    
    # Check if agent returned expected format
    decision = output.get("decision", output.get("shouldReply"))
    if decision is None:
        issues.append("No decision field in agent output")
    
    # Check qaResult from agent's self-QA
    qa_result = output.get("qaResult", "")
    if qa_result and "fail" in str(qa_result).lower():
        issues.append(f"Agent self-QA failed: {qa_result}")
    
    if issues:
        return CheckResult("wrong_action", False, "warn", "; ".join(issues))
    return CheckResult("wrong_action", True, "warn", "action appears correct")


def run_qa(agent_output: dict, domain: str, constraints: list = None) -> dict:
    """Run all 6 QA checks on agent output."""
    constraints = constraints or []
    
    checks = [
        check_factual_fit(agent_output, domain, constraints),
        check_style_fit(agent_output, domain, constraints),
        check_policy_fit(agent_output, domain, constraints),
        check_risk(agent_output, domain, constraints),
        check_missing_context(agent_output, domain, constraints),
        check_wrong_action(agent_output, domain, constraints),
    ]
    
    failures = [c for c in checks if not c.passed]
    blockers = [c for c in failures if c.severity == "block"]
    warnings = [c for c in failures if c.severity == "warn"]
    
    # Determine recommendation
    if blockers:
        recommendation = "cancel"
    elif len(warnings) >= 3:
        recommendation = "retry_agent"
    elif warnings:
        recommendation = "fix_and_send"
    else:
        recommendation = "approve"
    
    return {
        "passed": len(blockers) == 0,
        "checks": {c.name: asdict(c) for c in checks},
        "failures": [asdict(c) for c in failures],
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "recommendation": recommendation,
    }


def main():
    parser = argparse.ArgumentParser(description="QAService — quality gate")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--input", default="", help="Agent output JSON (or pipe via stdin)")
    parser.add_argument("--constraints", nargs="*", default=[], help="Constraint strings")
    args = parser.parse_args()
    
    # Read input
    if args.input:
        agent_output = json.loads(args.input)
    else:
        agent_output = json.loads(sys.stdin.read())
    
    result = run_qa(agent_output, args.domain, args.constraints)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
