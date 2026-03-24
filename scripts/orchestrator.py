#!/usr/bin/env python3
"""
Orchestrator — Entry point that delegates to core architecture.
Now a thin wrapper that routes to core/router.py + core/execution_pipeline.py

Usage (active mode):
    python3 orchestrator.py --message "שלח מייל לדני" --source dm
    python3 orchestrator.py --message "שלום" --source group --group-id "family" --role "active"

Usage (shadow mode — legacy for compatibility):
    python3 orchestrator.py --message "מה מזג האוויר?" --source dm --shadow
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add core modules to path
WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
sys.path.insert(0, str(WORKSPACE / "core"))

try:
    from execution_pipeline import ExecutionPipeline
    pipeline = ExecutionPipeline(str(WORKSPACE))
except ImportError as e:
    print(f"❌ Failed to import core modules: {e}", file=sys.stderr)
    sys.exit(1)

# Import legacy services (for shadow mode only)
sys.path.insert(0, str(Path(__file__).parent))

def legacy_shadow_pipeline(message: str, source: str, group_id: str = None, role: str = None):
    """Legacy shadow mode - just logs without executing"""
    return {
        "mode": "shadow",
        "message": message,
        "source": source,
        "group_id": group_id,
        "role": role,
        "status": "logged_only",
        "note": "Shadow mode - use active mode for real execution"
    }

def main():
    parser = argparse.ArgumentParser(description="Orchestrator — Entry point to core execution pipeline")
    parser.add_argument("--message", required=True, help="Incoming message")
    parser.add_argument("--source", required=True, choices=["dm", "group", "heartbeat", "subagent_return"])
    parser.add_argument("--group-id", default="", help="Group ID (for group source)")
    parser.add_argument("--role", default="", help="Group role")
    parser.add_argument("--shadow", action="store_true", help="Shadow mode — log only")

    args = parser.parse_args()
    
    # Map source to channel for pipeline
    channel_map = {"dm": "direct", "group": "whatsapp"}
    channel = channel_map.get(args.source, args.source)
    
    try:
        if args.shadow:
            # Legacy shadow mode (just logs, doesn't execute)
            result = legacy_shadow_pipeline(
                message=args.message,
                source=args.source,
                group_id=args.group_id or None,
                role=args.role or None
            )
        else:
            # New active mode: Route through core architecture
            metadata = {}
            if args.role:
                metadata["role"] = args.role
            if args.source == "group":
                metadata["sender_id"] = "test_sender"  # TODO: get from real context
                
            result = pipeline.execute(
                message=args.message,
                channel=channel,
                group_id=args.group_id or None,
                metadata=metadata
            )
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        import traceback
        print(f"❌ Pipeline error: {e}", file=sys.stderr)
        print(f"❌ Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()