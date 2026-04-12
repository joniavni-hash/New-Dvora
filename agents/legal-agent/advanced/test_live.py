#!/usr/bin/env python3
"""
Masha Advanced — Live Integration Test
Tests real model calls, caching, cost tracking, and all workflows.
Run: python3 test_live.py [--quick] [--workflow <type>]
"""

import json
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from masha_advanced import MashaAdvanced
from model_client import call_tier1, ModelCallError


SAMPLE_CONTRACT = """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of March 1, 2026
Between: SitiKids Ltd. ("Provider"), Company No. 51-1234567,
         of 42 Innovation Blvd, Tel Aviv, Israel
And: Chen Digital Marketing Ltd. ("Client"), Company No. 51-7654321,
     of 18 Herzl St, Ramat Gan, Israel

RECITALS:
The Client wishes to engage the Provider for digital marketing services.
The Provider has the expertise and resources to provide such services.

1. DEFINITIONS
"Confidential Information" means any non-public information.
"Deliverables" means content, reports, and materials created under this Agreement.
"Services" means the digital marketing services described in Schedule A.

2. SERVICES
Provider shall provide:
(a) Social media management for 3 platforms (Instagram, Facebook, TikTok)
(b) Monthly content creation (20 posts minimum)
(c) Quarterly performance reports
(d) Campaign management and optimization

3. TERM AND TERMINATION
3.1 Initial term: 12 months from Effective Date
3.2 Auto-renewal for successive 6-month periods unless terminated with 60 days notice
3.3 Either party may terminate for material breach with 30 days written notice
3.4 Client may terminate for convenience with 60 days notice, paying fees through notice period

4. FEES AND PAYMENT
4.1 Monthly fee: NIS 15,000 + VAT
4.2 Payment: Net 30 from invoice date
4.3 Annual increase: Linked to CPI, max 5%
4.4 Late payment: 1.5% monthly interest after 15-day grace period

5. INTELLECTUAL PROPERTY
5.1 All Deliverables created under this Agreement shall be owned by Client upon full payment.
5.2 Provider retains right to use work in portfolio (non-commercial display only).
5.3 Provider's pre-existing IP remains with Provider; Client gets non-exclusive license.

6. CONFIDENTIALITY
6.1 Both parties shall maintain confidentiality for 3 years after termination.
6.2 Exceptions: public information, independently developed, legally required disclosure.

7. LIMITATION OF LIABILITY
7.1 Neither party liable for indirect, consequential, incidental or punitive damages.
7.2 Total liability capped at total fees paid in the 12 months preceding the claim.
7.3 This limitation does not apply to breaches of confidentiality or IP infringement.

8. REPRESENTATIONS AND WARRANTIES
8.1 Provider warrants it has the expertise and licenses to perform the Services.
8.2 Client warrants it has authority to enter this Agreement.
8.3 No warranties are given as to specific business results.

9. INDEMNIFICATION
9.1 Each party indemnifies the other against third-party claims arising from its breach.
9.2 Indemnification subject to the liability cap in Section 7.

10. FORCE MAJEURE
Neither party liable for delays due to events beyond reasonable control.

11. GOVERNING LAW AND JURISDICTION
11.1 This Agreement is governed by Israeli law.
11.2 Disputes: Tel Aviv Magistrate/District Courts have exclusive jurisdiction.
11.3 Before litigation, parties shall attempt good-faith negotiation for 30 days.

12. GENERAL
12.1 Amendment: Written agreement of both parties required.
12.2 Assignment: Requires prior written consent.
12.3 Entire Agreement: This constitutes the entire agreement between the parties.
12.4 Notices: Written, to addresses above, effective upon receipt.

IN WITNESS WHEREOF, the parties have executed this Agreement.

SitiKids Ltd.                    Chen Digital Marketing Ltd.
_________________               _________________
Name:                            Name:
Title:                           Title:
Date:                            Date:
"""


def test_connectivity():
    """Test basic API connectivity."""
    print("🔌 Testing API connectivity...")
    try:
        resp = call_tier1(
            system="You are a test assistant. Respond in JSON only.",
            user='Return: {"status": "ok", "model": "sonnet"}',
            max_tokens=50,
        )
        print(f"   ✅ Connected: {resp.model} ({resp.input_tokens}+{resp.output_tokens} tokens)")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_workflow(masha, task_type, message, doc_text=None, expected_tier="tier1"):
    """Test a single workflow."""
    print(f"\n📋 Testing: {task_type}")
    print(f"   Message: {message[:60]}...")

    start = time.time()
    try:
        result = masha.analyze(
            task=message,
            document_text=doc_text or SAMPLE_CONTRACT,
            context={"sender": "yoni"},
        )
        duration = time.time() - start

        content = result.get("draft", {}).get("content", "")
        cost = result.get("costUsd", 0)
        tier = result.get("modelTier", "unknown")
        qa = result.get("qaResult", "unknown")
        risk = result.get("legalRisk", "unknown")

        print(f"   ✅ Complete in {duration:.1f}s")
        print(f"   Tier: {tier} | Cost: ${cost:.4f} | QA: {qa} | Risk: {risk}")
        print(f"   Content: {len(content)} chars")
        if content:
            # Show first 200 chars
            preview = content[:200].replace('\n', ' ')
            print(f"   Preview: {preview}...")

        return {
            "task_type": task_type,
            "success": True,
            "duration_s": round(duration, 1),
            "cost_usd": cost,
            "tier": tier,
            "qa": qa,
            "risk": risk,
            "content_length": len(content),
        }
    except Exception as e:
        duration = time.time() - start
        print(f"   ❌ Failed in {duration:.1f}s: {e}")
        return {
            "task_type": task_type,
            "success": False,
            "duration_s": round(duration, 1),
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Only test 2 workflows")
    parser.add_argument("--workflow", type=str, help="Test specific workflow type")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 מאשה Advanced — Live Integration Test")
    print("=" * 60)

    # Step 1: Connectivity
    if not test_connectivity():
        print("\n❌ Cannot connect to API. Aborting.")
        sys.exit(1)

    masha = MashaAdvanced()

    # Step 2: Workflow tests
    workflows = [
        ("clause_extraction", "תמצאי סעיפי תשלום בחוזה", "tier1"),
        ("legal_summary", "תסכמי את החוזה בבקשה", "tier1"),
        ("contract_review", "תבדקי את החוזה הזה — מה הנקודות העיקריות?", "tier1"),
        ("risk_analysis", "מה הסיכונים בחוזה הזה?", "tier2"),
        ("draft_response", "תכיני תגובה לעורך הדין של הצד השני — נקודות שרוצים לשנות", "tier2"),
        ("negotiation_prep", "הכיני לי תכנית משא ומתן — רוצה להוריד את התשלום ולקצר נעילה", "tier2"),
        ("compare_versions", "השוואי את החוזה הזה מול גרסה ישנה", "tier1"),
    ]

    if args.workflow:
        workflows = [(w, m, t) for w, m, t in workflows if w == args.workflow]

    if args.quick:
        workflows = workflows[:2]

    results = []
    for task_type, message, expected in workflows:
        r = test_workflow(masha, task_type, message, SAMPLE_CONTRACT, expected)
        results.append(r)

    # Step 3: Cache test
    print("\n💾 Testing cache...")
    cache_result = masha.analyze(
        task="תמצאי סעיפי תשלום בחוזה",
        document_text=SAMPLE_CONTRACT,
    )
    if cache_result.get("costUsd", 1) == 0:
        print("   ✅ Cache hit — $0 cost")
    else:
        print(f"   ⚠️ Cache miss — ${cache_result.get('costUsd', 0):.4f}")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    total_cost = sum(r.get("cost_usd", 0) for r in results)
    total_time = sum(r.get("duration_s", 0) for r in results)
    successes = sum(1 for r in results if r.get("success"))

    print(f"\nResults: {successes}/{len(results)} passed")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Total time: {total_time:.0f}s")

    print("\nPer workflow:")
    for r in results:
        status = "✅" if r.get("success") else "❌"
        print(f"  {status} {r['task_type']}: ${r.get('cost_usd', 0):.4f} in {r.get('duration_s', 0):.0f}s")

    # Cost report
    print("\n" + masha.get_daily_report())

    # Cache stats
    print(f"\nCache stats: {json.dumps(masha.get_cache_stats(), indent=2)}")

    print("\n" + "=" * 60)
    if successes == len(results):
        print("✅ ALL TESTS PASSED — Masha Advanced is LIVE!")
    else:
        print(f"⚠️ {len(results) - successes} test(s) failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
