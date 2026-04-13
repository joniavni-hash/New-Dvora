#!/usr/bin/env python3
"""Push dashboard data to Vercel Blob via the /api/push endpoint.

Run from cron every 2 minutes:
  */2 * * * * cd /home/ubuntu/.openclaw/workspace && /usr/bin/python3 scripts/dashboard_push.py

Required env vars:
  DASHBOARD_VERCEL_URL  — e.g. https://dvorah-dashboard.vercel.app
  DASHBOARD_PUSH_TOKEN  — Bearer token (must match DASHBOARD_PUSH_TOKEN on Vercel)

Generated push token (set this in both places):
  dvr_push_a7f3e9c1b24d5068fe91ca3b7d4820e6
"""

import json
import os
import sys

import requests

# Import collect_all_data from the existing dashboard server
sys.path.insert(0, os.path.dirname(__file__))
from dashboard_server import collect_all_data


def main():
    vercel_url = os.environ.get("DASHBOARD_VERCEL_URL", "").rstrip("/")
    push_token = os.environ.get("DASHBOARD_PUSH_TOKEN", "")

    if not vercel_url:
        print("ERROR: DASHBOARD_VERCEL_URL not set", file=sys.stderr)
        sys.exit(1)
    if not push_token:
        print("ERROR: DASHBOARD_PUSH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    # Collect data
    data = collect_all_data()

    # Push to Vercel
    url = f"{vercel_url}/api/push"
    headers = {
        "Authorization": f"Bearer {push_token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=data, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        print(f"OK: pushed {len(json.dumps(data))} bytes — {result}")
    except requests.RequestException as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
