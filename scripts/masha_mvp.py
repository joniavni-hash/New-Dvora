#!/usr/bin/env python3
"""
מאשה — Legal Agent Entry Point
Routes through Masha Advanced multi-model pipeline.
Backward-compatible wrapper: same interface as original masha_mvp.py.

Migration: 2026-03-23
Original backed up as: masha_mvp.py.old
"""

import sys
import os
from pathlib import Path

# Add advanced module path
ADVANCED_DIR = str(Path(__file__).parent.parent / "agents" / "legal-agent" / "advanced")
sys.path.insert(0, ADVANCED_DIR)

# Also keep scripts/ on path for legal_intent_classifier
SCRIPTS_DIR = str(Path(__file__).parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from masha_advanced import MashaAdvanced

# Re-export as MashaMVP for backward compatibility
MashaMVP = MashaAdvanced


def test_masha_mvp():
    """Backward-compatible test function."""
    masha = MashaAdvanced()

    test_requests = [
        {
            "task": "תסכמי את החוזה המצורף",
            "attachments": ["contract.pdf"],
            "context": {"sender": "yoni"}
        },
        {
            "task": "מה הסיכונים בחוזה הזה?",
            "attachments": [],
            "context": {"sender": "yoni"}
        },
        {
            "task": "תמצאי סעיפי אחריות",
            "attachments": ["agreement.pdf"],
            "context": {"sender": "yoni"}
        }
    ]

    for i, request in enumerate(test_requests, 1):
        print(f"\n=== Test Case {i} ===")
        print(f"Task: {request['task']}")

        can_handle_result = masha.can_handle(
            request['task'],
            request['context'],
            request['attachments']
        )
        print(f"Can Handle: {can_handle_result['canHandle']} (confidence: {can_handle_result['confidence']:.2f})")

        if can_handle_result.get('routingPreview'):
            rp = can_handle_result['routingPreview']
            print(f"Routing: {rp['tier']} (complexity: {rp['complexity_score']}, risk: {rp['risk_level']})")

        if can_handle_result.get('estimatedCost'):
            ec = can_handle_result['estimatedCost']
            print(f"Est. Cost: ${ec['total_cost_usd']:.4f} (saves {ec['savings_vs_opus_pct']}% vs Opus)")

        if can_handle_result['canHandle']:
            result = masha.analyze(
                request['task'],
                request['context'],
                request['attachments']
            )
            print(f"Decision: {result['decision']}")
            print(f"Task Type: {result['draft']['type']}")
            print(f"Legal Risk: {result['legalRisk']}")
            print(f"Model Tier: {result.get('modelTier', 'unknown')}")
            print(f"Cost: ${result.get('costUsd', 0):.4f}")


if __name__ == "__main__":
    test_masha_mvp()
