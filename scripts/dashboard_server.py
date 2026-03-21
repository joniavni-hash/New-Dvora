#!/usr/bin/env python3
"""Dvora Dashboard Server — live dashboard at port 8899."""

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values
from flask import Flask, jsonify, render_template

BASE_DIR = Path(__file__).resolve().parent.parent
SECRETS_ENV = BASE_DIR / "secrets" / ".env"

app = Flask(__name__)


def load_secrets():
    """Load secrets from secrets/.env file."""
    if SECRETS_ENV.exists():
        return dotenv_values(SECRETS_ENV)
    return {}


def parse_tasks():
    """Parse state/OPEN_TASKS.md into structured task list."""
    path = BASE_DIR / "state" / "OPEN_TASKS.md"
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    tasks = []
    priority_map = {"🔴": "red", "🟡": "yellow", "🟢": "green"}

    # Split by ### headers
    blocks = re.split(r"^### ", content, flags=re.MULTILINE)
    for block in blocks[1:]:  # skip preamble
        lines = block.strip().split("\n")
        header = lines[0]

        # Skip completed tasks
        if header.startswith("✅"):
            continue

        # Extract priority
        priority = "yellow"
        priority_emoji = ""
        for emoji, cls in priority_map.items():
            if emoji in header:
                priority = cls
                priority_emoji = emoji
                break

        name = header
        for emoji in priority_map:
            name = name.replace(emoji, "").strip()

        # Parse fields
        fields = {}
        for line in lines[1:]:
            m = re.match(r"^- (\w+):\s*(.+)", line)
            if m:
                fields[m.group(1)] = m.group(2).strip()

        tasks.append({
            "name": name,
            "priority": priority,
            "priority_emoji": priority_emoji,
            "opened": fields.get("opened", ""),
            "status": fields.get("status", fields.get("content", "")),
            "next": fields.get("next", ""),
        })

    return tasks


def parse_integrations():
    """Parse integrations/*.md files."""
    integrations_dir = BASE_DIR / "integrations"
    if not integrations_dir.exists():
        return []

    results = []
    status_map = {
        "connected": ("ok", "מחובר"),
        "active": ("ok", "פעיל"),
        "disconnected": ("err", "מנותק"),
        "error": ("err", "שגיאה"),
        "disabled": ("off", "לא בשימוש"),
    }

    for md_file in sorted(integrations_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        name = md_file.stem.replace("_", " ").title()

        # Try to extract name from first heading, then filename
        heading = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        if heading:
            name = heading.group(1).strip()
            # Remove trailing "Integration" / ".md" noise
            name = re.sub(r"\s*(Integration|\.md)\s*$", "", name, flags=re.IGNORECASE).strip()
        integ_match = re.search(r"^Integration:\s*(.+)", content, re.MULTILINE)
        if integ_match:
            name = integ_match.group(1).strip()

        # Extract status — multiple formats:
        #   "Status: Connected"  (inline)
        #   "## Status\nConnected" (heading + next line)
        status_key = "unknown"
        # Try inline format first
        status_match = re.search(r"^[Ss]tatus:\s*(\w+)", content, re.MULTILINE)
        if status_match:
            status_key = status_match.group(1).lower()
        else:
            # Try heading format: ## Status\n<value>
            heading_match = re.search(r"^##\s+[Ss]tatus\s*\n+(.+)", content, re.MULTILINE)
            if heading_match:
                val = heading_match.group(1).strip().split("(")[0].strip().split()[0].lower()
                if val:
                    status_key = val
        badge_class, badge_text = status_map.get(status_key, ("warn", status_key))

        results.append({
            "name": name,
            "badge_class": badge_class,
            "badge_text": badge_text,
        })

    return results


def get_cron_jobs():
    """Run openclaw cron list --json and parse output."""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=10,
            cwd=str(BASE_DIR),
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        raw = json.loads(result.stdout)

        # Normalize to list
        if isinstance(raw, dict):
            for key in ("jobs", "crons", "items", "data"):
                if key in raw and isinstance(raw[key], list):
                    raw = raw[key]
                    break
            else:
                raw = [{"name": k, **(v if isinstance(v, dict) else {"schedule": str(v)})}
                       for k, v in raw.items()]

        if not isinstance(raw, list):
            return []

        # Simplify for template
        jobs = []
        for job in raw:
            name = job.get("description") or job.get("name") or job.get("id", "unknown")
            enabled = job.get("enabled", True)

            # Format next run from epoch ms
            next_run = ""
            state = job.get("state", {})
            next_ms = state.get("nextRunAtMs") if isinstance(state, dict) else None
            if next_ms:
                dt = datetime.fromtimestamp(next_ms / 1000, tz=timezone.utc)
                next_run = dt.strftime("%d.%m.%Y %H:%M UTC")

            schedule_expr = ""
            sched = job.get("schedule", {})
            if isinstance(sched, dict):
                schedule_expr = sched.get("expr", "")

            jobs.append({
                "name": name,
                "enabled": enabled,
                "next_run": next_run,
                "schedule": schedule_expr,
                "last_status": state.get("lastStatus", "") if isinstance(state, dict) else "",
            })

        return jobs
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None  # None = unavailable


def parse_groups():
    """Parse state/KNOWN_GROUPS.md."""
    path = BASE_DIR / "state" / "KNOWN_GROUPS.md"
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    groups = []

    blocks = re.split(r"^## ", content, flags=re.MULTILINE)
    for block in blocks[1:]:
        lines = block.strip().split("\n")
        name = lines[0].strip()

        behavior = ""
        for line in lines[1:]:
            m = re.match(r"^- behavior:\s*(.+)", line)
            if m:
                behavior = m.group(1).strip()
                break

        # Multi-line behavior
        if not behavior:
            in_behavior = False
            parts = []
            for line in lines[1:]:
                if line.strip().startswith("- behavior:"):
                    in_behavior = True
                    rest = line.split("behavior:", 1)[1].strip()
                    if rest:
                        parts.append(rest)
                    continue
                if in_behavior:
                    if line.strip().startswith("- ") and not line.strip().startswith("  -"):
                        break
                    stripped = line.strip().lstrip("- ").strip()
                    if stripped:
                        parts.append(stripped)
            behavior = " · ".join(parts) if parts else ""

        groups.append({"name": name, "behavior": behavior})

    return groups


def read_metrics():
    """Read state/metrics_latest.json."""
    path = BASE_DIR / "state" / "metrics_latest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def parse_heartbeat():
    """Parse HEARTBEAT.md for scheduled items."""
    path = BASE_DIR / "HEARTBEAT.md"
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    items = []

    # Extract ## headings with their schedule descriptions
    for m in re.finditer(r"^## (.+?)$", content, re.MULTILINE):
        heading = m.group(1).strip()
        # Extract the emoji and name, and schedule hint after the dash
        parts = heading.split("—", 1)
        name = parts[0].strip()
        schedule = parts[1].strip() if len(parts) > 1 else ""
        items.append({"name": name, "schedule": schedule})

    return items


def get_outlook_unread():
    """Get unread email count via Microsoft Graph API."""
    secrets = load_secrets()
    tenant = secrets.get("MS_GRAPH_TENANT")
    client_id = secrets.get("MS_GRAPH_CLIENT_ID")
    client_secret = secrets.get("MS_GRAPH_CLIENT_SECRET")
    user = secrets.get("MS_GRAPH_USER")

    if not all([tenant, client_id, client_secret, user]):
        return None

    try:
        # Get access token
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        token_resp = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }, timeout=10)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # Get unread count
        headers = {"Authorization": f"Bearer {access_token}"}
        mail_url = (
            f"https://graph.microsoft.com/v1.0/users/{user}"
            "/mailFolders/Inbox?$select=unreadItemCount"
        )
        mail_resp = requests.get(mail_url, headers=headers, timeout=10)
        mail_resp.raise_for_status()
        return mail_resp.json().get("unreadItemCount", 0)
    except Exception:
        return None


def collect_all_data():
    """Collect all dashboard data."""
    now = datetime.now(timezone.utc)

    metrics = read_metrics()

    # Compute aggregate metrics
    total_responses = 0
    total_sessions = 0
    weighted_latency = 0
    total_tool_calls = 0
    total_count = 0
    if metrics:
        total_responses = metrics.get("total_response_pairs", 0)
        total_sessions = metrics.get("total_sessions", 0)
        for model, stats in metrics.get("model_stats", {}).items():
            count = stats.get("count", 0)
            total_count += count
            weighted_latency += stats.get("median_latency", 0) * count
            total_tool_calls += stats.get("avg_tool_calls", 0) * count

    avg_latency = round(weighted_latency / total_count, 1) if total_count else 0
    avg_tools = round(total_tool_calls / total_count, 1) if total_count else 0

    cost = metrics.get("cost", {}) if metrics else {}

    return {
        "tasks": parse_tasks(),
        "integrations": parse_integrations(),
        "cron_jobs": get_cron_jobs(),
        "groups": parse_groups(),
        "heartbeat": parse_heartbeat(),
        "outlook_unread": get_outlook_unread(),
        "metrics": {
            "total_responses": total_responses,
            "total_sessions": total_sessions,
            "avg_latency": avg_latency,
            "avg_tool_calls": avg_tools,
        },
        "cost": {
            "today": round(cost.get("today", 0), 2),
            "this_week": round(cost.get("this_week", 0), 2),
            "last_30d": round(cost.get("last_30d", 0), 2),
            "daily_avg": round(cost.get("last_30d", 0) / 30, 1),
        },
        "updated_at": now.isoformat(),
    }


@app.route("/")
def index():
    data = collect_all_data()
    return render_template("dashboard.html", data=data)


@app.route("/api/data")
def api_data():
    return jsonify(collect_all_data())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8899, debug=True)
