#!/usr/bin/env python3
"""
מאשה Advanced — Cost-Efficient Multi-Model Legal Agent
Main entry point. Replaces masha_mvp.py with multi-model pipeline.

Usage:
    from masha_advanced import MashaAdvanced
    
    masha = MashaAdvanced()
    result = masha.analyze("תסכמי את החוזה", context={"sender": "yoni"}, document_text="...")
    
    # Or via CLI:
    python3 masha_advanced.py --task "תסכמי את החוזה" --document contract.txt [--force-tier opus]
"""

import json
import sys
import os
import argparse
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))

from model_router import ModelRouter, RoutingDecision
from pipeline_engine import PipelineEngine, PipelineResult
from legal_cache import LegalCache
from cost_tracker import CostTracker
from legal_checklists import get_checklist_for_workflow
from model_client import ModelCallError

# Import the original classifier for backward compatibility
try:
    from legal_intent_classifier import LegalIntentClassifier
except ImportError:
    LegalIntentClassifier = None


class MashaAdvanced:
    """
    מאשה Advanced — Multi-model legal agent with cost optimization.
    
    Drop-in replacement for MashaMVP with the same interface,
    plus new capabilities:
    - Multi-model routing (3-tier system)
    - Pipeline-based processing
    - Smart caching and retrieval
    - Cost tracking and reporting
    - Structured checklist analysis
    """

    def __init__(self):
        self.pipeline = PipelineEngine()
        self.router = ModelRouter()
        self.cache = LegalCache()
        self.cost_tracker = CostTracker()
        self.classifier = LegalIntentClassifier() if LegalIntentClassifier else None

    # ============================================================
    # PUBLIC API — Backward compatible with MashaMVP
    # ============================================================

    def can_handle(self, task: str, context: Dict = None, attachments: List[str] = None) -> Dict:
        """
        Check if מאשה can handle this task.
        Backward compatible with MashaMVP.can_handle().
        """
        context = context or {}
        attachments = attachments or []

        if self.classifier:
            classification = self.classifier.classify_legal_intent(task, attachments, context)
            should_route, action = self.classifier.should_route_to_masha(classification)
        else:
            # Fallback: basic keyword check
            legal_keywords = ['חוזה', 'הסכם', 'contract', 'agreement', 'סעיף', 'clause', 'סיכון', 'risk']
            found = any(kw in task.lower() for kw in legal_keywords)
            classification = {"is_legal": found, "confidence": 0.7 if found else 0.2, "task_type": "unknown"}
            should_route = found
            action = "direct" if found else "decline"

        # Enhanced: add routing preview
        if should_route:
            routing_preview = self.router.route(
                task_type=classification.get("task_type", "legal_summary"),
                message=task,
            )
            estimated_cost = self.cost_tracker.estimate_pipeline_cost(
                classification.get("task_type", "legal_summary"),
                None,
                routing_preview.tier.value,
            )
        else:
            routing_preview = None
            estimated_cost = None

        return {
            "canHandle": should_route and action == 'direct',
            "confidence": classification['confidence'],
            "taskType": classification.get('task_type', 'unknown'),
            "reasoning": classification.get('reasoning', ''),
            "requiresConfirmation": action == 'confirm',
            # New fields
            "routingPreview": routing_preview.to_dict() if routing_preview else None,
            "estimatedCost": estimated_cost,
        }

    def analyze(
        self,
        task: str,
        context: Dict = None,
        attachments: List = None,
        document_text: Optional[str] = None,
        force_tier: Optional[str] = None,
    ) -> Dict:
        """
        Main analysis function — routes through multi-model pipeline.
        Backward compatible with MashaMVP.analyze().
        
        New parameters:
            document_text: Full text of the document (if available)
            force_tier: Override model tier ("opus", "mid", "cheap")
        """
        context = context or {}
        attachments = attachments or []

        # Classify intent
        if self.classifier:
            classification = self.classifier.classify_legal_intent(task, attachments, context)
            task_type = classification.get("task_type", "legal_summary")
        else:
            task_type = self._guess_task_type(task)

        # Check for force-tier in message
        if not force_tier:
            force_tier = self._detect_force_tier(task)

        # Execute pipeline
        result = self.pipeline.execute(
            task_type=task_type,
            message=task,
            document_text=document_text,
            context=context,
            attachments=attachments,
            force_tier=force_tier,
        )

        # Return in standard Masha format (backward compatible)
        return result.final_output

    def get_cost_report(self) -> Dict:
        """Get current session cost report."""
        return self.cost_tracker.session_summary()

    def get_daily_report(self, date_str: Optional[str] = None) -> str:
        """Get formatted daily cost report."""
        report = self.cost_tracker.daily_report(date_str)
        return self.cost_tracker.format_cost_report(report)

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return self.cache.stats()

    def get_pipeline_design(self, task_type: str) -> Dict:
        """Get pipeline design for a specific workflow."""
        return self.pipeline.get_pipeline_design(task_type)

    def estimate_cost(self, task: str, document_text: Optional[str] = None) -> Dict:
        """
        Estimate cost before execution.
        Useful for cost-aware decision making.
        """
        if self.classifier:
            classification = self.classifier.classify_legal_intent(task)
            task_type = classification.get("task_type", "legal_summary")
        else:
            task_type = self._guess_task_type(task)

        routing = self.router.route(
            task_type=task_type,
            message=task,
            document_text=document_text,
        )

        estimate = self.cost_tracker.estimate_pipeline_cost(
            task_type=task_type,
            document_text=document_text,
            tier=routing.tier.value,
        )

        return {
            "task_type": task_type,
            "routing": routing.to_dict(),
            "cost_estimate": estimate,
        }

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _guess_task_type(task: str) -> str:
        """Simple task type guessing without classifier."""
        task_lower = task.lower()
        if 'סיכונ' in task_lower or 'risk' in task_lower:
            return "risk_analysis"
        if 'סעיפ' in task_lower or 'clause' in task_lower:
            return "clause_extraction"
        if 'השוו' in task_lower or 'compare' in task_lower:
            return "compare_versions"
        if 'תגובה' in task_lower or 'draft' in task_lower or 'תכיני' in task_lower:
            return "draft_response"
        if 'משא ומתן' in task_lower or 'negotiat' in task_lower:
            return "negotiation_prep"
        if 'סכמ' in task_lower or 'summar' in task_lower:
            return "legal_summary"
        return "contract_review"  # Default

    @staticmethod
    def _detect_force_tier(task: str) -> Optional[str]:
        """Detect if user explicitly requested a specific tier."""
        task_lower = task.lower()
        if 'use opus' in task_lower or 'תשתמשי באופוס' in task_lower:
            return "opus"
        if 'cheap' in task_lower or 'זול' in task_lower or 'מהיר' in task_lower:
            return "cheap"
        return None


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="מאשה Advanced — Multi-Model Legal Agent")
    parser.add_argument("--task", type=str, help="Legal task description")
    parser.add_argument("--document", type=str, help="Path to document file")
    parser.add_argument("--force-tier", type=str, choices=["cheap", "mid", "opus"], help="Force a specific model tier")
    parser.add_argument("--estimate-only", action="store_true", help="Only estimate cost, don't execute")
    parser.add_argument("--cost-report", action="store_true", help="Show daily cost report")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--pipeline-design", type=str, help="Show pipeline design for a workflow type")
    parser.add_argument("--test", action="store_true", help="Run test suite")

    args = parser.parse_args()
    masha = MashaAdvanced()

    if args.cost_report:
        print(masha.get_daily_report())
        return

    if args.cache_stats:
        print(json.dumps(masha.get_cache_stats(), indent=2, ensure_ascii=False))
        return

    if args.pipeline_design:
        design = masha.get_pipeline_design(args.pipeline_design)
        print(json.dumps(design, indent=2, ensure_ascii=False))
        return

    if args.test:
        run_tests(masha)
        return

    if not args.task:
        parser.print_help()
        return

    # Read document if provided
    document_text = None
    if args.document:
        doc_path = Path(args.document)
        if doc_path.exists():
            document_text = doc_path.read_text()
        else:
            print(f"Error: Document not found: {args.document}", file=sys.stderr)
            return

    if args.estimate_only:
        estimate = masha.estimate_cost(args.task, document_text)
        print(json.dumps(estimate, indent=2, ensure_ascii=False))
    else:
        result = masha.analyze(
            task=args.task,
            document_text=document_text,
            force_tier=args.force_tier,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


def run_tests(masha: MashaAdvanced):
    """Run comprehensive tests."""
    print("=" * 60)
    print("מאשה Advanced — Test Suite")
    print("=" * 60)

    # Test 1: can_handle
    print("\n--- Test 1: can_handle ---")
    test_cases = [
        ("תסכמי את החוזה המצורף", True),
        ("מה הסיכונים בהסכם?", True),
        ("מה מזג האוויר?", False),
        ("תכיני תגובה לעורך הדין", True),
    ]
    for task, expected in test_cases:
        result = masha.can_handle(task)
        status = "✅" if result["canHandle"] == expected else "❌"
        tier_info = f" → {result['routingPreview']['tier']}" if result.get('routingPreview') else ""
        print(f"  {status} '{task}' → canHandle={result['canHandle']}{tier_info}")

    # Test 2: Routing
    print("\n--- Test 2: Model Routing ---")
    routing_tests = [
        ("clause_extraction", "תמצאי סעיפי תשלום", None, "tier1"),
        ("risk_analysis", "מה הסיכונים?", "unlimited liability and personal guarantee" * 50, "tier3"),
        ("legal_summary", "תסכמי בבקשה", "Short document", "tier1"),
        ("contract_review", "תבדקי חוזה בינלאומי", "cross-border multi-party " * 500, "tier2"),
    ]
    for task_type, message, doc, expected_tier in routing_tests:
        routing = masha.router.route(task_type, message, doc)
        status = "✅" if routing.tier.value == expected_tier else f"⚠️ (got {routing.tier.value})"
        print(f"  {status} {task_type}: {routing.tier.value} — {routing.reason[:60]}...")

    # Test 3: Cost estimation
    print("\n--- Test 3: Cost Estimation ---")
    estimate = masha.estimate_cost("תסכמי את החוזה", "Contract text " * 1000)
    print(f"  Task: {estimate['task_type']}")
    print(f"  Tier: {estimate['routing']['tier']}")
    print(f"  Est. cost: ${estimate['cost_estimate']['total_cost_usd']:.4f}")
    print(f"  Opus equivalent: ${estimate['cost_estimate']['opus_equivalent_cost']:.4f}")
    print(f"  Savings: {estimate['cost_estimate']['savings_vs_opus_pct']}%")

    # Test 4: Pipeline execution
    print("\n--- Test 4: Pipeline Execution ---")
    result = masha.analyze(
        task="תסכמי את החוזה",
        document_text="This is a standard service agreement between Party A and Party B. " * 100,
        context={"sender": "yoni"},
    )
    print(f"  Decision: {result['decision']}")
    print(f"  Task type: {result['draft']['type']}")
    print(f"  Risk level: {result['legalRisk']}")
    print(f"  Model tier: {result.get('modelTier', 'unknown')}")
    print(f"  Cost: ${result.get('costUsd', 0):.4f}")
    print(f"  QA: {result['qaResult']}")

    # Test 5: Cache
    print("\n--- Test 5: Cache ---")
    stats = masha.get_cache_stats()
    print(f"  Cache entries: {stats['total_entries']}")
    print(f"  Total hits: {stats['total_hits']}")

    # Test 6: Pipeline designs
    print("\n--- Test 6: Pipeline Designs ---")
    for workflow in ["contract_review", "risk_analysis", "clause_extraction", "legal_summary",
                     "draft_response", "compare_versions", "negotiation_prep"]:
        design = masha.get_pipeline_design(workflow)
        print(f"  {workflow}: {len(design['stages'])} stages, split: {design['typical_tier_split']}")

    # Test 7: Session cost report
    print("\n--- Test 7: Session Cost Report ---")
    report = masha.get_cost_report()
    print(f"  Total cost: ${report['total_cost_usd']:.4f}")
    print(f"  Total calls: {report['total_calls']}")
    print(f"  By tier: {report['by_tier']}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
