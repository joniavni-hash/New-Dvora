#!/usr/bin/env python3
"""X/Twitter Feed Aggregator — fetches public timelines and produces a summary.

Uses Twitter syndication API (no auth needed for public profiles).
Output: state/x_feed_latest.md
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "state" / "x_feed_latest.md"

# Accounts to track, grouped by category
FEEDS = {
    "🏢 Labs": [
        "AnthropicAI",
        "OpenAI",
        "GoogleDeepMind",
        "xaboratory",  # xAI
        "MetaAI",
    ],
    "🧠 Researchers & Leaders": [
        "karpathy",      # Andrej Karpathy
        "ylecun",        # Yann LeCun
        "sama",          # Sam Altman
        "DarioAmodei",   # Dario Amodei
        "jimfan",        # Jim Fan (NVIDIA)
        "AmandaAskell",  # Amanda Askell (Anthropic)
    ],
    "🛠️ Builders & Tools": [
        "swyx",          # AI engineering
        "LangChainAI",
        "llama_index",
        "HuggingFace",
        "e2b_dev",
        "levelsio",
    ],
    "📰 News": [
        "TheRundownAI",
        "AravSrinivas",  # Perplexity CEO
    ],
}


def fetch_timeline(username, max_tweets=5):
    """Fetch recent tweets from a public profile via syndication API."""
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []

        html = result.stdout

        # Extract tweet texts
        texts = re.findall(r'"text":"((?:[^"\\]|\\.)*)"', html)

        tweets = []
        seen = set()
        for text in texts[:max_tweets * 2]:  # grab more, dedup later
            # Unescape JSON strings
            text = text.encode().decode('unicode_escape', errors='replace')
            # Clean up t.co links — keep them for reference
            clean = text.strip()
            if clean and clean not in seen:
                seen.add(clean)
                tweets.append(clean)
            if len(tweets) >= max_tweets:
                break

        return tweets
    except (subprocess.TimeoutExpired, Exception) as e:
        return [f"(fetch error: {e})"]


def main():
    now = datetime.now(timezone.utc)
    lines = []
    lines.append(f"# X/Twitter Feed Summary")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"")

    total_tweets = 0
    errors = 0

    for category, accounts in FEEDS.items():
        lines.append(f"## {category}")
        lines.append("")

        for username in accounts:
            tweets = fetch_timeline(username, max_tweets=3)
            if not tweets:
                errors += 1
                lines.append(f"### @{username}")
                lines.append(f"_(no tweets fetched)_")
                lines.append("")
                continue

            lines.append(f"### @{username}")
            for i, tweet in enumerate(tweets, 1):
                # Truncate very long tweets
                if len(tweet) > 280:
                    tweet = tweet[:277] + "..."
                lines.append(f"- {tweet}")
                total_tweets += 1
            lines.append("")

    lines.append("---")
    lines.append(f"Total: {total_tweets} tweets from {sum(len(v) for v in FEEDS.values())} accounts | {errors} errors")

    content = "\n".join(lines)

    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"OK: {total_tweets} tweets saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
