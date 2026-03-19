#!/usr/bin/env python3
"""OpenClaw Session Metrics Analyzer

Analyzes JSONL session files to compute response latency, tool usage,
cost breakdown, and activity patterns.
"""

import json
import os
import sys
import glob
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from statistics import mean, median
from pathlib import Path

SESSIONS_DIR = "/home/jonia/.openclaw/agents/main/sessions/"
OUTPUT_JSON = "/home/jonia/.openclaw/workspace/state/metrics_latest.json"
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
        # Handle Z suffix and various ISO formats
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

    # Walk through messages, pairing user → first assistant
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

        # Extract user message text for context
        user_text = ""
        for c in (msg.get("content") or []):
            if isinstance(c, dict) and c.get("type") == "text":
                user_text = c.get("text", "")[:120]
                break
            elif isinstance(c, str):
                user_text = c[:120]
                break

        # Find first assistant message after this user message
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
                # Next user message - stop searching
                break

            if role == "assistant":
                ts = parse_timestamp(messages[j].get("timestamp") or next_msg.get("timestamp"))
                if not found_assistant and ts:
                    assistant_ts = ts
                    found_assistant = True
                    if not model:
                        model = next_msg.get("model")

                # Count tool calls in content
                for c in (next_msg.get("content") or []):
                    if isinstance(c, dict) and c.get("type") == "toolCall":
                        total_tool_calls += 1

                # Accumulate usage
                usage = next_msg.get("usage", {})
                cost_info = usage.get("cost", {})
                total_cost += cost_info.get("total", 0) or 0
                total_output_tokens += usage.get("output", 0) or 0
                if not model:
                    model = next_msg.get("model")

            elif role == "toolResult":
                pass  # skip, just part of the chain

            j += 1

        if found_assistant and assistant_ts:
            latency = (assistant_ts - user_ts).total_seconds()
            # Sanity check: skip negative or absurdly large latencies
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


def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)

    # Find all JSONL files (including reset/deleted ones for historical data)
    patterns = [
        os.path.join(SESSIONS_DIR, "*.jsonl"),
        os.path.join(SESSIONS_DIR, "*.jsonl.reset.*"),
        os.path.join(SESSIONS_DIR, "*.jsonl.deleted.*"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))

    # Filter by modification time
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
        return

    # Sort by timestamp
    all_pairs.sort(key=lambda p: p["user_ts"])

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    # === Group by model ===
    by_model = defaultdict(list)
    for p in all_pairs:
        by_model[p["model"]].append(p)

    # === Group by hour ===
    by_hour = defaultdict(int)
    for p in all_pairs:
        by_hour[p["hour"]] += 1

    # === Group by weekday ===
    by_weekday = defaultdict(int)
    for p in all_pairs:
        by_weekday[p["weekday"]] += 1

    # === Cost calculations ===
    cost_today = sum(p["cost"] for p in all_pairs if p["user_ts"] >= today_start)
    cost_week = sum(p["cost"] for p in all_pairs if p["user_ts"] >= week_start)
    cost_total = sum(p["cost"] for p in all_pairs)

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

    # Slowest responses
    print("\n🐢 Slowest 5 Responses")
    print("-" * 50)
    slowest = sorted(all_pairs, key=lambda p: p["latency_s"], reverse=True)[:5]
    for i, p in enumerate(slowest, 1):
        ts_local = p["user_ts"].strftime("%b %d %H:%M")
        text = p["user_text"][:80].replace("\n", " ")
        print(f"  {i}. {p['latency_s']:6.1f}s | {p['model']:>8s} | {ts_local} | {text}")

    # Busiest hours
    print("\n⏰ Busiest Hours (UTC)")
    print("-" * 50)
    top_hours = sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:8]
    for hour, count in top_hours:
        bar = "█" * min(count, 40)
        print(f"  {hour:02d}:00  {count:>4d} {bar}")

    # Busiest days
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
        "total_output_tokens": total_tokens,
        "busiest_hours_utc": {str(h): c for h, c in top_hours},
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
    print(f"Summary saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
