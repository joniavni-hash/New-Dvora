#!/usr/bin/env python3
"""
Shadow Integration Test — Phase 2
Compares orchestrator decisions against expected manual-flow decisions.
Tests all services end-to-end with real workspace data.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import run_pipeline, classify, intake, route
from context_service import load_context
from policy_service import evaluate as evaluate_policy
from qa_service import run_qa
from trace_service import log_trace, query_traces, get_stats

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

# ============================================================
# TEST CASES: Real-world messages with expected manual decisions
# ============================================================

TEST_CASES = [
    # --- DM: Simple questions (Dvorah handles directly) ---
    {
        "id": "dm_question_weather",
        "message": "מה מזג האוויר בתל אביב?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "general",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    {
        "id": "dm_question_tasks",
        "message": "מה המשימות הפתוחות שלי?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "general",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    # --- DM: Fitness tracking ---
    {
        "id": "dm_fitness_weight",
        "message": "שקלתי היום 72.1",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": ["command", "tracking"],  # self-reporting
            "domain": "fitness",
            "action_type": ["MUTATE", "READ"],  # either acceptable
            "agent": "direct",
            "approval_flow": ["auto", "dvorah_only"],
        },
    },
    {
        "id": "dm_fitness_question",
        "message": "כמה קלוריות אכלתי היום?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "fitness",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    # --- DM: Email actions ---
    {
        "id": "dm_email_check",
        "message": "מה יש במייל?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "email",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    {
        "id": "dm_email_send",
        "message": "שלחי מייל לדני עם סיכום הפגישה",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "action",
            "domain": "email",
            "action_type": "SEND",
            "agent": "direct",
            "approval_flow": "dvorah_approve",
        },
    },
    {
        "id": "dm_email_draft",
        "message": "הכיני טיוטה למייל תשובה לעו\"ד",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "action",
            "domain": "email",  # or "legal"
            "action_type": "DRAFT",
            "agent": "direct",
            "approval_flow": "dvorah_review",
        },
    },
    # --- DM: Legal routing ---
    {
        "id": "dm_legal_contract",
        "message": "תבדקי את החוזה הזה",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "action",
            "domain": "legal",
            "action_type": ["READ", "SEND"],
            "agent": "LegalAgent",
            "approval_flow": ["auto", "dvorah_approve"],
        },
    },
    {
        "id": "dm_legal_clause",
        "message": "מה אומר סעיף 5 בהסכם?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "legal",
            "action_type": "READ",
            "agent": ["direct", "LegalAgent"],
            "approval_flow": "auto",
        },
    },
    # --- Group messages ---
    {
        "id": "group_family_hello",
        "message": "שלום לכולם",
        "source": "group",
        "metadata": {"group_id": "family", "role": "observer"},
        "expected": {
            "intent": "conversation",
            "domain": "group",
            "action_type": "READ",
            "agent": "WhatsAppGroupAgent",
            "approval_flow": ["auto", "blocked"],
        },
    },
    {
        "id": "group_active_question",
        "message": "דבורה, מה השעה?",
        "source": "group",
        "metadata": {"group_id": "test-group", "role": "active"},
        "expected": {
            "intent": "question",
            "domain": "group",
            "action_type": "READ",
            "agent": "WhatsAppGroupAgent",
            "approval_flow": "auto",
        },
    },
    {
        "id": "group_observer_no_reply",
        "message": "מישהו יודע מתי הפגישה?",
        "source": "group",
        "metadata": {"group_id": "work", "role": "observer"},
        "expected": {
            "intent": "question",
            "domain": "group",
            "action_type": "READ",
            "agent": "WhatsAppGroupAgent",
            "approval_flow": "blocked",
        },
    },
    # --- Action commands ---
    {
        "id": "dm_command_remember",
        "message": "זכרי שדני אוהב קפה שחור",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "command",
            "domain": "general",
            "action_type": "MUTATE",
            "agent": "direct",
            "approval_flow": "dvorah_only",
        },
    },
    {
        "id": "dm_action_light",
        "message": "תדליקי אור בסלון",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "action",
            "domain": "general",
            "action_type": "SEND",
            "agent": "direct",
            "approval_flow": "dvorah_approve",
        },
    },
    # --- Travel ---
    {
        "id": "dm_travel_flight",
        "message": "תחפשי טיסה לברלין בחודש הבא",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "action",
            "domain": "travel",
            "action_type": "SEND",
            "agent": "direct",  # Phase 3
            "approval_flow": "dvorah_approve",
        },
    },
    # --- Conversation / chitchat ---
    {
        "id": "dm_conversation_thanks",
        "message": "תודה",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "conversation",
            "domain": "general",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    {
        "id": "dm_conversation_complex",
        "message": "מה דעתך על ביטקוין?",
        "source": "dm",
        "metadata": {},
        "expected": {
            "intent": "question",
            "domain": "general",
            "action_type": "READ",
            "agent": "direct",
            "approval_flow": "auto",
        },
    },
    # --- High sensitivity ---
    {
        "id": "dm_sensitive_new_recipient",
        "message": "שלחי מייל לכתובת חדשה info@example.com",
        "source": "dm",
        "metadata": {"sensitivity_signals": ["new_recipient", "external_email"]},
        "expected": {
            "intent": "action",
            "domain": "email",
            "action_type": "SEND",
            "agent": "direct",
            "approval_flow": "yoni_approve",
        },
    },
]


def match_expected(actual, expected):
    """Check if actual matches expected (supports lists = any-of)."""
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def run_test(tc: dict) -> dict:
    """Run a single test case and compare."""
    start = time.time()
    result = run_pipeline(
        message=tc["message"],
        source=tc["source"],
        metadata=tc.get("metadata", {}),
        shadow=True,
    )
    elapsed = time.time() - start

    expected = tc["expected"]
    classification = result["classification"]
    routing = result["routing"]
    approval = result["policy_summary"]["approval"]

    checks = {
        "intent": match_expected(classification["intent"], expected.get("intent", classification["intent"])),
        "domain": match_expected(classification["domain"], expected.get("domain", classification["domain"])),
        "action_type": match_expected(classification["action_type"], expected.get("action_type", classification["action_type"])),
        "agent": match_expected(routing["agent"], expected.get("agent", routing["agent"])),
        "approval_flow": match_expected(approval["flow"], expected.get("approval_flow", approval["flow"])),
    }

    passed = all(checks.values())
    
    return {
        "id": tc["id"],
        "passed": passed,
        "checks": checks,
        "actual": {
            "intent": classification["intent"],
            "domain": classification["domain"],
            "action_type": classification["action_type"],
            "agent": routing["agent"],
            "approval_flow": approval["flow"],
            "confidence": classification["confidence"],
        },
        "expected": expected,
        "duration_ms": round(elapsed * 1000, 1),
        "context_files": result["context_summary"]["files_loaded"],
        "policies_loaded": result["policy_summary"]["policies_loaded"],
    }


# ============================================================
# QA SERVICE TESTS
# ============================================================

QA_TEST_CASES = [
    {
        "id": "qa_good_reply",
        "output": {
            "decision": "reply",
            "draft": "כן, הפגישה ביום שלישי ב-10.",
            "confidence": 0.85,
            "reasoning": "Calendar check confirmed",
        },
        "domain": "group",
        "constraints": [],
        "expected_recommendation": "approve",
    },
    {
        "id": "qa_anti_pattern",
        "output": {
            "decision": "reply",
            "draft": "שאלה מעניינת! אשמח לעזור לך עם זה. בהצלחה!",
            "confidence": 0.9,
        },
        "domain": "general",
        "constraints": [],
        "expected_recommendation": "fix_and_send",  # style warnings
    },
    {
        "id": "qa_observer_block",
        "output": {
            "decision": "reply",
            "draft": "The meeting is tomorrow",
            "confidence": 0.7,
        },
        "domain": "group",
        "constraints": ["BLOCKED: role=observer — no external actions allowed"],
        "expected_recommendation": "cancel",  # policy block
    },
    {
        "id": "qa_privacy_leak",
        "output": {
            "decision": "reply",
            "draft": "הטלפון של דני הוא 0541234567",
            "confidence": 0.9,
        },
        "domain": "group",
        "constraints": [],
        "expected_recommendation": "cancel",  # privacy block
    },
    {
        "id": "qa_low_confidence",
        "output": {
            "decision": "reply",
            "draft": "אני חושבת שכן",
            "confidence": 0.3,
            "reasoning": "לא בטוח, אולי כדאי לבדוק",
        },
        "domain": "general",
        "constraints": [],
        "expected_recommendation": "fix_and_send",  # low confidence + uncertain reasoning → 1-2 warnings
    },
    {
        "id": "qa_long_group_message",
        "output": {
            "decision": "reply",
            "draft": "א" * 600,
            "confidence": 0.8,
        },
        "domain": "group",
        "constraints": [],
        "expected_recommendation": "fix_and_send",  # too long
    },
]


def run_qa_test(tc: dict) -> dict:
    """Run a QA test case."""
    start = time.time()
    result = run_qa(tc["output"], tc["domain"], tc.get("constraints", []))
    elapsed = time.time() - start

    passed = result["recommendation"] == tc["expected_recommendation"]
    
    return {
        "id": tc["id"],
        "passed": passed,
        "actual_recommendation": result["recommendation"],
        "expected_recommendation": tc["expected_recommendation"],
        "blocker_count": result["blocker_count"],
        "warning_count": result["warning_count"],
        "duration_ms": round(elapsed * 1000, 1),
        "check_details": {
            name: {"passed": c["passed"], "detail": c["detail"][:80]}
            for name, c in result["checks"].items()
        },
    }


# ============================================================
# CONTEXT SERVICE TESTS
# ============================================================

def test_context_service() -> list:
    """Test context loading for each domain."""
    results = []
    
    domains_to_test = [
        ("general", {}, ["IDENTITY.md"]),
        ("group", {"group_id": "family"}, ["IDENTITY.md", "state/KNOWN_GROUPS.md"]),
        ("fitness", {}, ["IDENTITY.md", "state/fitness_tracker.md"]),
        ("email", {}, ["IDENTITY.md"]),
    ]
    
    for domain, metadata, expected_files in domains_to_test:
        start = time.time()
        ctx = load_context(domain, metadata)
        elapsed = time.time() - start
        
        # Check expected files are loaded
        files_ok = all(f in ctx["files_loaded"] for f in expected_files if (WORKSPACE / f).exists())
        
        # Check token budget
        within_budget = ctx["tokens_estimate"] <= 4000
        
        results.append({
            "domain": domain,
            "passed": files_ok and within_budget,
            "files_loaded": ctx["files_loaded"],
            "expected_files": expected_files,
            "tokens": ctx["tokens_estimate"],
            "within_budget": within_budget,
            "duration_ms": round(elapsed * 1000, 1),
        })
    
    return results


# ============================================================
# POLICY SERVICE TESTS
# ============================================================

def test_policy_service() -> list:
    """Test policy evaluation for key scenarios."""
    results = []
    
    scenarios = [
        {
            "domain": "group",
            "action_type": "READ",
            "metadata": {"role": "observer"},
            "expect_blocked": True,
        },
        {
            "domain": "group",
            "action_type": "SEND",
            "metadata": {"role": "active"},
            "expect_blocked": False,
        },
        {
            "domain": "email",
            "action_type": "SEND",
            "metadata": {"sensitivity_signals": ["new_recipient"]},
            "expect_yoni_approve": True,
        },
        {
            "domain": "general",
            "action_type": "READ",
            "metadata": {},
            "expect_auto": True,
        },
        {
            "domain": "general",
            "action_type": "MUTATE",
            "metadata": {},
            "expect_auto": False,
        },
    ]
    
    for s in scenarios:
        start = time.time()
        result = evaluate_policy(s["domain"], s["action_type"], s.get("metadata", {}))
        elapsed = time.time() - start
        
        passed = True
        details = []
        
        if s.get("expect_blocked"):
            if result["approval"]["flow"] != "blocked":
                passed = False
                details.append(f"Expected blocked, got {result['approval']['flow']}")
        
        if s.get("expect_yoni_approve"):
            if not result["approval"]["requires_yoni"]:
                passed = False
                details.append("Expected yoni_approve, not flagged")
        
        if s.get("expect_auto"):
            if not result["approval"]["auto_approve"]:
                passed = False
                details.append("Expected auto_approve")
        
        if "expect_auto" in s and not s["expect_auto"]:
            if result["approval"]["auto_approve"]:
                passed = False
                details.append("Expected NOT auto_approve")
        
        results.append({
            "scenario": f"{s['domain']}/{s['action_type']}/{s.get('metadata', {}).get('role', '-')}",
            "passed": passed,
            "approval_flow": result["approval"]["flow"],
            "policies_loaded": len(result["policies_loaded"]),
            "constraints": result["constraint_count"],
            "details": details,
            "duration_ms": round(elapsed * 1000, 1),
        })
    
    return results


# ============================================================
# TRACE SERVICE TESTS
# ============================================================

def test_trace_service() -> dict:
    """Test trace logging and querying."""
    # Log a test entry
    test_entry = {
        "trigger": "integration_test",
        "domain": "test",
        "action_type": "READ",
        "agent": "direct",
        "model": "test",
        "context_loaded": ["IDENTITY.md"],
        "agent_decision": "test_classification",
        "qa_result": "pass",
        "approval": "auto",
        "action_taken": "test_response",
        "memory_writes": [],
        "duration_ms": 5,
        "shadow_mode": True,
    }
    
    log_result = log_trace(test_entry)
    
    # Query it back
    entries = query_traces(domain="test", last_n=1)
    
    # Stats
    stats = get_stats()
    
    return {
        "log_ok": log_result.get("status") == "logged",
        "query_ok": len(entries) > 0,
        "stats_ok": stats.get("entries", 0) > 0,
        "today_entries": stats.get("entries", 0),
    }


# ============================================================
# PERFORMANCE BENCHMARK
# ============================================================

def benchmark_pipeline(iterations: int = 50) -> dict:
    """Benchmark orchestrator pipeline performance."""
    messages = [
        ("מה השעה?", "dm", {}),
        ("שלחי מייל", "dm", {}),
        ("שלום לכולם", "group", {"group_id": "family", "role": "observer"}),
        ("מה המשקל שלי?", "dm", {}),
        ("תבדקי חוזה", "dm", {}),
    ]
    
    durations = []
    
    for i in range(iterations):
        msg, src, meta = messages[i % len(messages)]
        start = time.time()
        run_pipeline(msg, src, meta, shadow=True)
        durations.append((time.time() - start) * 1000)
    
    durations.sort()
    
    return {
        "iterations": iterations,
        "min_ms": round(durations[0], 1),
        "max_ms": round(durations[-1], 1),
        "avg_ms": round(sum(durations) / len(durations), 1),
        "p50_ms": round(durations[len(durations) // 2], 1),
        "p95_ms": round(durations[int(len(durations) * 0.95)], 1),
        "p99_ms": round(durations[int(len(durations) * 0.99)], 1),
        "total_ms": round(sum(durations), 1),
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("🔬 SHADOW INTEGRATION TEST — Phase 2")
    print("=" * 70)
    
    all_pass = True
    
    # --- 1. Classification & Routing Tests ---
    print("\n📊 1. CLASSIFICATION & ROUTING TESTS")
    print("-" * 50)
    
    routing_results = []
    routing_passed = 0
    for tc in TEST_CASES:
        r = run_test(tc)
        routing_results.append(r)
        status = "✅" if r["passed"] else "❌"
        if r["passed"]:
            routing_passed += 1
        else:
            all_pass = False
        
        failed_checks = [k for k, v in r["checks"].items() if not v]
        extra = ""
        if failed_checks:
            extra = f"  FAILED: {failed_checks}"
            extra += f"  actual: {json.dumps({k: r['actual'][k] for k in failed_checks}, ensure_ascii=False)}"
        
        print(f"  {status} {r['id']:35s} {r['duration_ms']:6.1f}ms{extra}")
    
    routing_rate = routing_passed / len(TEST_CASES) * 100
    print(f"\n  Score: {routing_passed}/{len(TEST_CASES)} ({routing_rate:.0f}%)")
    
    # --- 2. QA Service Tests ---
    print("\n🔍 2. QA SERVICE TESTS")
    print("-" * 50)
    
    qa_passed = 0
    for tc in QA_TEST_CASES:
        r = run_qa_test(tc)
        status = "✅" if r["passed"] else "❌"
        if r["passed"]:
            qa_passed += 1
        else:
            all_pass = False
        
        extra = "" if r["passed"] else f"  got={r['actual_recommendation']}"
        print(f"  {status} {r['id']:35s} {r['duration_ms']:6.1f}ms{extra}")
    
    qa_rate = qa_passed / len(QA_TEST_CASES) * 100
    print(f"\n  Score: {qa_passed}/{len(QA_TEST_CASES)} ({qa_rate:.0f}%)")
    
    # --- 3. Context Service Tests ---
    print("\n📁 3. CONTEXT SERVICE TESTS")
    print("-" * 50)
    
    ctx_results = test_context_service()
    ctx_passed = 0
    for r in ctx_results:
        status = "✅" if r["passed"] else "❌"
        if r["passed"]:
            ctx_passed += 1
        else:
            all_pass = False
        print(f"  {status} domain={r['domain']:10s} files={r['files_loaded']}  tokens≈{r['tokens']}  {r['duration_ms']:.1f}ms")
    
    # --- 4. Policy Service Tests ---
    print("\n📜 4. POLICY SERVICE TESTS")
    print("-" * 50)
    
    pol_results = test_policy_service()
    pol_passed = 0
    for r in pol_results:
        status = "✅" if r["passed"] else "❌"
        if r["passed"]:
            pol_passed += 1
        else:
            all_pass = False
        extra = f"  {r['details']}" if r.get("details") else ""
        print(f"  {status} {r['scenario']:30s} flow={r['approval_flow']:15s} constraints={r['constraints']}  {r['duration_ms']:.1f}ms{extra}")
    
    # --- 5. Trace Service Tests ---
    print("\n📝 5. TRACE SERVICE TESTS")
    print("-" * 50)
    
    trace_result = test_trace_service()
    for k, v in trace_result.items():
        status = "✅" if v else "❌"
        if not v:
            all_pass = False
        print(f"  {status} {k}: {v}")
    
    # --- 6. Performance Benchmark ---
    print("\n⚡ 6. PERFORMANCE BENCHMARK (50 iterations)")
    print("-" * 50)
    
    perf = benchmark_pipeline(50)
    print(f"  avg:  {perf['avg_ms']:.1f}ms")
    print(f"  p50:  {perf['p50_ms']:.1f}ms")
    print(f"  p95:  {perf['p95_ms']:.1f}ms")
    print(f"  p99:  {perf['p99_ms']:.1f}ms")
    print(f"  min:  {perf['min_ms']:.1f}ms")
    print(f"  max:  {perf['max_ms']:.1f}ms")
    print(f"  total: {perf['total_ms']:.1f}ms for {perf['iterations']} runs")
    
    # --- SUMMARY ---
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    total_tests = len(TEST_CASES) + len(QA_TEST_CASES) + len(ctx_results) + len(pol_results) + len(trace_result)
    total_passed = routing_passed + qa_passed + ctx_passed + pol_passed
    total_passed += sum(1 for v in trace_result.values() if v)
    
    overall_rate = total_passed / total_tests * 100
    
    print(f"  Routing:     {routing_passed}/{len(TEST_CASES)} ({routing_rate:.0f}%)")
    print(f"  QA:          {qa_passed}/{len(QA_TEST_CASES)} ({qa_rate:.0f}%)")
    print(f"  Context:     {ctx_passed}/{len(ctx_results)}")
    print(f"  Policy:      {pol_passed}/{len(pol_results)}")
    print(f"  Trace:       {sum(1 for v in trace_result.values() if v)}/{len(trace_result)}")
    print(f"  Performance: avg={perf['avg_ms']:.1f}ms p95={perf['p95_ms']:.1f}ms")
    print(f"\n  OVERALL:     {total_passed}/{total_tests} ({overall_rate:.0f}%)")
    
    # Decision
    print("\n" + "=" * 70)
    if overall_rate >= 90 and perf["p95_ms"] < 100:
        print("✅ DECISION: READY FOR SWITCHOVER")
        print("   All criteria met: >90% match, sub-100ms p95 latency")
    elif overall_rate >= 80:
        print("⚠️  DECISION: NEEDS MINOR FIXES")
        print(f"   Match rate {overall_rate:.0f}% — close but not 90%+ target")
    else:
        print("❌ DECISION: NOT READY — NEEDS SIGNIFICANT FIXES")
        print(f"   Match rate {overall_rate:.0f}% — below 80% threshold")
    print("=" * 70)
    
    # Output JSON for programmatic use
    report = {
        "routing": {"passed": routing_passed, "total": len(TEST_CASES), "rate": routing_rate},
        "qa": {"passed": qa_passed, "total": len(QA_TEST_CASES), "rate": qa_rate},
        "context": {"passed": ctx_passed, "total": len(ctx_results)},
        "policy": {"passed": pol_passed, "total": len(pol_results)},
        "trace": trace_result,
        "performance": perf,
        "overall": {"passed": total_passed, "total": total_tests, "rate": overall_rate},
        "decision": "ready" if overall_rate >= 90 and perf["p95_ms"] < 100 else "needs_fixes",
    }
    
    report_path = WORKSPACE / "state" / "shadow_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Full report saved to: {report_path}")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
