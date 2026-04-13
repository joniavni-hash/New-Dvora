#!/usr/bin/env python3
"""OpenClaw Session Metrics Analyzer

Analyzes JSONL session files to compute response latency, tool usage,
cost breakdown, activity patterns, and correction tracking.
"""

import json
import os
import sys
import re
import glob
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from statistics import mean, median
from pathlib import Path

SESSIONS_DIR = "/home/ubuntu/.openclaw/agents/main/sessions/"
OUTPUT_JSON = "/home/ubuntu/.openclaw/workspace/state/metrics_latest.json"
CORRECTIONS_FILE = "/home/ubuntu/.openclaw/workspace/memory/corrections.md"
HEARTBEAT_LOG = "/home/ubuntu/.openclaw/workspace/state/heartbeat_log.md"
OPEN_TASKS = "/home/ubuntu/.openclaw/workspace/state/OPEN_TASKS.md"
CUTOFF_DAYS = 30


def percentile(data, p):
    """Calculate p-th percentile."""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def parse_timestamp(ts):
    """Parse ISO8601 or epoch-ms timestamp."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    if isinstance(ts, str):
        ts = ts.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
    return None


def model_short(model_str):
    """Shorten model name."""
    if not model_str:
        return "unknown"
    if "opus" in model_str:
        return "opus"
    if "sonnet" in model_str:
        return "sonnet"
    return model_str


def analyze_session(filepath):
    """Parse a single session JSONL file and extract response pairs."""
    pairs = []
    messages = []

    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "message":
                    messages.append(entry)
    except (IOError, OSError):
        return []

    i = 0
    while i < len(messages):
        msg = messages[i].get("message", {})
        if msg.get("role") != "user":
            i += 1
            continue

        user_ts = parse_timestamp(messages[i].get("timestamp") or msg.get("timestamp"))
        if not user_ts:
            i += 1
            continue

        user_text = ""
        for c in (msg.get("content") or []):
            if isinstance(c, dict) and c.get("type") == "text":
                user_text = c.get("text", "")[:120]
                break
            elif isinstance(c, str):
                user_text = c[:120]
                break

        j = i + 1
        total_tool_calls = 0
        total_cost = 0.0
        total_output_tokens = 0
        model = None
        assistant_ts = None
        found_assistant = False

        while j < len(messages):
            next_msg = messages[j].get("message", {})
            role = next_msg.get("role")

            if role == "user":
                break

            if role == "assistant":
                ts = parse_timestamp(messages[j].get("timestamp") or next_msg.get("timestamp"))
                if not found_assistant and ts:
                    assistant_ts = ts
                    found_assistant = True
                    if not model:
                        model = next_msg.get("model")

                for c in (next_msg.get("content") or []):
                    if isinstance(c, dict) and c.get("type") == "toolCall":
                        total_tool_calls += 1

                usage = next_msg.get("usage", {})
                cost_info = usage.get("cost", {})
                total_cost += cost_info.get("total", 0) or 0
                total_output_tokens += usage.get("output", 0) or 0
                if not model:
                    model = next_msg.get("model")

            j += 1

        if found_assistant and assistant_ts:
            latency = (assistant_ts - user_ts).total_seconds()
            if 0 <= latency <= 600:
                pairs.append({
                    "user_ts": user_ts,
                    "latency_s": latency,
                    "tool_calls": total_tool_calls,
                    "model": model_short(model),
                    "cost": total_cost,
                    "output_tokens": total_output_tokens,
                    "user_text": user_text,
                    "session": os.path.basename(filepath)[:8],
                    "hour": user_ts.hour,
                    "weekday": user_ts.strftime("%A"),
                })

        i = j if j > i + 1 else i + 1

    return pairs


# ─── Corrections Analysis ───

def parse_corrections():
    """Parse corrections.md and return structured correction entries."""
    if not os.path.exists(CORRECTIONS_FILE):
        return [], {}

    corrections = []
    categories = defaultdict(int)
    current = None

    try:
        with open(CORRECTIONS_FILE, "r") as f:
            content = f.read()
    except (IOError, OSError):
        return [], {}

    # Parse correction entries by ### headers
    blocks = re.split(r'^### ', content, flags=re.MULTILINE)
    for block in blocks[1:]:  # skip preamble
        lines = block.strip().split('\n')
        if not lines:
            continue

        header = lines[0].strip()
        entry = {"header": header, "category": None, "status": "new"}

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("- **למה טעיתי:**"):
                # Extract category
                match = re.search(r'`(\w+)`', line)
                if match:
                    entry["category"] = match.group(1)
                    categories[match.group(1)] += 1
            if line.startswith("- **סטטוס:**"):
                entry["status"] = line.split(":")[-1].strip()

        corrections.append(entry)

    return corrections, dict(categories)


# ─── Task Analysis ───

def parse_open_tasks():
    """Parse OPEN_TASKS.md for stuck task metrics."""
    if not os.path.exists(OPEN_TASKS):
        return {"red": 0, "yellow": 0, "green": 0, "stuck_3d": 0, "stuck_7d": 0}

    try:
        with open(OPEN_TASKS, "r") as f:
            content = f.read()
    except (IOError, OSError):
        return {"red": 0, "yellow": 0, "green": 0, "stuck_3d": 0, "stuck_7d": 0}

    red = content.count("🔴")
    yellow = content.count("🟡")
    green = content.count("🟢")

    # Check for stuck tasks by parsing opened dates
    stuck_3d = 0
    stuck_7d = 0
    today = datetime.now().date()

    for match in re.finditer(r'opened:\s*(\d{1,2}\.\d{1,2}\.\d{4})', content):
        try:
            parts = match.group(1).split('.')
            opened = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
            days = (today - opened).days
            if days >= 7:
                stuck_7d += 1
            elif days >= 3:
                stuck_3d += 1
        except (ValueError, IndexError):
            continue

    return {
        "red": red,
        "yellow": yellow,
        "green": green,
        "stuck_3d": stuck_3d,
        "stuck_7d": stuck_7d,
    }


# ─── Main ───

def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)

    patterns = [
        os.path.join(SESSIONS_DIR, "*.jsonl"),
        os.path.join(SESSIONS_DIR, "*.jsonl.reset.*"),
        os.path.join(SESSIONS_DIR, "*.jsonl.deleted.*"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))

    recent_files = []
    for f in files:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc)
            if mtime >= cutoff:
                recent_files.append(f)
        except OSError:
            continue

    all_pairs = []
    for f in sorted(recent_files):
        pairs = analyze_session(f)
        all_pairs.extend(pairs)

    if not all_pairs:
        print("No response pairs found in the last 30 days.")

    all_pairs.sort(key=lambda p: p["user_ts"])

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    # === Model grouping ===
    by_model = defaultdict(list)
    for p in all_pairs:
        by_model[p["model"]].append(p)

    by_hour = defaultdict(int)
    for p in all_pairs:
        by_hour[p["hour"]] += 1

    by_weekday = defaultdict(int)
    for p in all_pairs:
        by_weekday[p["weekday"]] += 1

    cost_today = sum(p["cost"] for p in all_pairs if p["user_ts"] >= today_start)
    cost_week = sum(p["cost"] for p in all_pairs if p["user_ts"] >= week_start)
    cost_total = sum(p["cost"] for p in all_pairs)

    # === Corrections ===
    corrections, correction_categories = parse_corrections()
    total_corrections = len(corrections)
    new_corrections = sum(1 for c in corrections if c.get("status") == "new")
    resolved_corrections = sum(1 for c in corrections if c.get("status") == "resolved")
    pattern_corrections = sum(1 for c in corrections if c.get("status") == "pattern")

    # Find repeating categories (3+)
    repeating_categories = {k: v for k, v in correction_categories.items() if v >= 3}

    # === Tasks ===
    task_stats = parse_open_tasks()

    # === Print Report ===
    print("=" * 65)
    print("  OpenClaw Session Metrics Report")
    print(f"  Period: last {CUTOFF_DAYS} days | {len(recent_files)} session files | {len(all_pairs)} response pairs")
    print("=" * 65)

    # Latency by model
    print("\n📊 Response Latency by Model")
    print("-" * 50)
    model_stats = {}
    for model_name in sorted(by_model.keys()):
        pairs = by_model[model_name]
        latencies = [p["latency_s"] for p in pairs]
        avg = mean(latencies)
        med = median(latencies)
        p90 = percentile(latencies, 90)
        p99 = percentile(latencies, 99)
        model_stats[model_name] = {
            "count": len(pairs),
            "avg_latency": round(avg, 2),
            "median_latency": round(med, 2),
            "p90_latency": round(p90, 2),
            "p99_latency": round(p99, 2),
        }
        print(f"  {model_name:>8s}  ({len(pairs):>4d} responses)")
        print(f"    avg: {avg:6.1f}s | median: {med:5.1f}s | p90: {p90:5.1f}s | p99: {p99:5.1f}s")

    # Tool calls
    print("\n🔧 Tool Calls per Response")
    print("-" * 50)
    for model_name in sorted(by_model.keys()):
        pairs = by_model[model_name]
        tc = [p["tool_calls"] for p in pairs]
        avg_tc = mean(tc)
        zero_pct = sum(1 for t in tc if t == 0) / len(tc) * 100
        model_stats[model_name]["avg_tool_calls"] = round(avg_tc, 2)
        print(f"  {model_name:>8s}  avg: {avg_tc:5.1f} tool calls | {zero_pct:.0f}% zero-tool responses")

    # Cost
    print("\n💰 Cost Summary")
    print("-" * 50)
    print(f"  Today:     ${cost_today:.4f}")
    print(f"  This week: ${cost_week:.4f}")
    print(f"  Last 30d:  ${cost_total:.4f}")
    for model_name in sorted(by_model.keys()):
        mc = sum(p["cost"] for p in by_model[model_name])
        print(f"    {model_name:>8s}: ${mc:.4f}")

    # Output tokens
    print("\n📝 Output Tokens")
    print("-" * 50)
    total_tokens = sum(p["output_tokens"] for p in all_pairs)
    print(f"  Total output tokens (30d): {total_tokens:,}")
    for model_name in sorted(by_model.keys()):
        mt = sum(p["output_tokens"] for p in by_model[model_name])
        print(f"    {model_name:>8s}: {mt:,}")

    # === NEW: Corrections Section ===
    print("\n🎯 Correction Tracking")
    print("-" * 50)
    print(f"  Total corrections logged:  {total_corrections}")
    print(f"    New (unresolved):        {new_corrections}")
    print(f"    Pattern identified:      {pattern_corrections}")
    print(f"    Resolved (rule created): {resolved_corrections}")
    if correction_categories:
        print(f"  By category:")
        for cat, count in sorted(correction_categories.items(), key=lambda x: x[1], reverse=True):
            flag = " ⚠️ PATTERN" if count >= 3 else ""
            print(f"    {cat:>10s}: {count}{flag}")
    if repeating_categories:
        print(f"  ⚠️  Repeating patterns ({', '.join(repeating_categories.keys())}) — rules needed!")
    if total_corrections == 0:
        print(f"  (no corrections logged yet)")

    # Correction rate (corrections per week estimate)
    if all_pairs and total_corrections > 0:
        first_ts = all_pairs[0]["user_ts"]
        last_ts = all_pairs[-1]["user_ts"]
        span_days = max((last_ts - first_ts).days, 1)
        correction_rate = total_corrections / (span_days / 7)
        print(f"  Rate: ~{correction_rate:.1f} corrections/week")

    # === NEW: Task Health ===
    print("\n📋 Task Health")
    print("-" * 50)
    print(f"  🔴 Urgent:  {task_stats['red']}")
    print(f"  🟡 Normal:  {task_stats['yellow']}")
    print(f"  🟢 Passive: {task_stats['green']}")
    print(f"  Stuck 3+ days: {task_stats['stuck_3d']}")
    print(f"  Stuck 7+ days: {task_stats['stuck_7d']}")
    if task_stats['stuck_7d'] > 0:
        print(f"  ⚠️  {task_stats['stuck_7d']} task(s) stuck over a week!")

    # Slowest responses
    if all_pairs:
        print("\n🐢 Slowest 5 Responses")
        print("-" * 50)
        slowest = sorted(all_pairs, key=lambda p: p["latency_s"], reverse=True)[:5]
        for i, p in enumerate(slowest, 1):
            ts_local = p["user_ts"].strftime("%b %d %H:%M")
            text = p["user_text"][:80].replace("\n", " ")
            print(f"  {i}. {p['latency_s']:6.1f}s | {p['model']:>8s} | {ts_local} | {text}")
    else:
        slowest = []

    # Busiest hours
    if by_hour:
        print("\n⏰ Busiest Hours (UTC)")
        print("-" * 50)
        top_hours = sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:8]
        for hour, count in top_hours:
            bar = "█" * min(count, 40)
            print(f"  {hour:02d}:00  {count:>4d} {bar}")
    else:
        top_hours = []

    # Busiest days
    if by_weekday:
        print("\n📅 Activity by Day of Week")
        print("-" * 50)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in day_order:
            count = by_weekday.get(day, 0)
            bar = "█" * min(count, 40)
            print(f"  {day:>9s}  {count:>4d} {bar}")

    print("\n" + "=" * 65)

    # === Save JSON ===
    summary = {
        "generated_at": now.isoformat(),
        "period_days": CUTOFF_DAYS,
        "total_sessions": len(recent_files),
        "total_response_pairs": len(all_pairs),
        "model_stats": model_stats,
        "cost": {
            "today": round(cost_today, 6),
            "this_week": round(cost_week, 6),
            "last_30d": round(cost_total, 6),
        },
        "total_output_tokens": sum(p["output_tokens"] for p in all_pairs),
        "corrections": {
            "total": total_corrections,
            "new": new_corrections,
            "pattern": pattern_corrections,
            "resolved": resolved_corrections,
            "categories": correction_categories,
            "repeating_patterns": list(repeating_categories.keys()),
        },
        "tasks": task_stats,
        "busiest_hours_utc": {str(h): c for h, c in (top_hours if by_hour else [])},
        "activity_by_weekday": dict(by_weekday),
        "slowest_responses": [
            {
                "latency_s": p["latency_s"],
                "model": p["model"],
                "timestamp": p["user_ts"].isoformat(),
                "user_text": p["user_text"][:120],
            }
            for p in slowest
        ],
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
