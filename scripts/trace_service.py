#!/usr/bin/env python3
"""
TraceService — JSONL logging for Dvorah's Orchestrator.
Every significant decision gets a trace entry.

Usage:
    python3 trace_service.py --log '{"trigger":"group_message","domain":"group",...}'
    python3 trace_service.py --query --domain group --last 10
    python3 trace_service.py --stats --date 2026-03-23
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
TRACES_DIR = WORKSPACE / "state" / "traces"

# Israel timezone offset
ISR_TZ = timezone(timedelta(hours=2))


def get_trace_file(date_str: str = None) -> Path:
    """Get trace file path for a date (default: today)."""
    if not date_str:
        date_str = datetime.now(ISR_TZ).strftime("%Y-%m-%d")
    return TRACES_DIR / f"{date_str}.jsonl"


def log_trace(entry: dict) -> dict:
    """Append a trace entry to today's file."""
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ensure timestamp
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now(ISR_TZ).isoformat()
    
    # Ensure required fields have defaults
    defaults = {
        "trigger": "unknown",
        "domain": "general",
        "action_type": "READ",
        "agent": "direct",
        "model": "unknown",
        "context_loaded": [],
        "agent_decision": "",
        "qa_result": "skip",
        "qa_failures": [],
        "approval": "auto",
        "action_taken": "",
        "memory_writes": [],
        "duration_ms": 0,
        "shadow_mode": False,
    }
    
    for key, default in defaults.items():
        entry.setdefault(key, default)
    
    # Write to file
    trace_file = get_trace_file()
    with open(trace_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return {"status": "logged", "file": str(trace_file), "timestamp": entry["timestamp"]}


def query_traces(domain: str = None, last_n: int = 10, date_str: str = None) -> list:
    """Query trace entries with optional filters."""
    trace_file = get_trace_file(date_str)
    
    if not trace_file.exists():
        return []
    
    entries = []
    with open(trace_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if domain and entry.get("domain") != domain:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    
    return entries[-last_n:]


def get_stats(date_str: str = None) -> dict:
    """Get statistics for a day's traces."""
    trace_file = get_trace_file(date_str)
    
    if not trace_file.exists():
        return {"entries": 0, "message": f"No traces for {date_str or 'today'}"}
    
    entries = []
    with open(trace_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if not entries:
        return {"entries": 0}
    
    # Aggregate stats
    domains = {}
    agents = {}
    qa_failures = 0
    total_duration = 0
    shadow_count = 0
    
    for e in entries:
        d = e.get("domain", "unknown")
        domains[d] = domains.get(d, 0) + 1
        
        a = e.get("agent", "unknown")
        agents[a] = agents.get(a, 0) + 1
        
        if e.get("qa_result") == "fail":
            qa_failures += 1
        
        total_duration += e.get("duration_ms", 0)
        
        if e.get("shadow_mode"):
            shadow_count += 1
    
    return {
        "entries": len(entries),
        "domains": domains,
        "agents": agents,
        "qa_failures": qa_failures,
        "total_duration_ms": total_duration,
        "avg_duration_ms": total_duration // len(entries) if entries else 0,
        "shadow_mode_entries": shadow_count,
    }


def cleanup_old_traces(keep_days: int = 14):
    """Remove trace files older than keep_days."""
    if not TRACES_DIR.exists():
        return {"cleaned": 0}
    
    cutoff = datetime.now(ISR_TZ) - timedelta(days=keep_days)
    cleaned = 0
    
    for f in TRACES_DIR.glob("*.jsonl"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=ISR_TZ)
            if file_date < cutoff:
                f.unlink()
                cleaned += 1
        except ValueError:
            continue
    
    return {"cleaned": cleaned, "kept_days": keep_days}


def main():
    parser = argparse.ArgumentParser(description="TraceService — JSONL logging")
    parser.add_argument("--log", default="", help="JSON entry to log")
    parser.add_argument("--query", action="store_true", help="Query traces")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--cleanup", action="store_true", help="Clean old traces")
    parser.add_argument("--domain", default="", help="Filter by domain")
    parser.add_argument("--last", type=int, default=10, help="Number of entries")
    parser.add_argument("--date", default="", help="Date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    if args.log:
        entry = json.loads(args.log)
        result = log_trace(entry)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.query:
        entries = query_traces(
            domain=args.domain or None,
            last_n=args.last,
            date_str=args.date or None,
        )
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    elif args.stats:
        result = get_stats(date_str=args.date or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.cleanup:
        result = cleanup_old_traces()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
