#!/usr/bin/env python3
"""
Extract WhatsApp group messages from OpenClaw session files.

Usage:
    python3 scripts/group_messages.py <group_id> [--days N] [--limit N]
    
Returns messages as simple "sender: text" format, one per line.
"""

import json
import re
import os
import sys
import glob
from datetime import datetime, timedelta
from pathlib import Path

SESSIONS_DIR = Path(os.path.expanduser('~/.openclaw/agents/main/sessions'))


def extract_group_messages(group_id, days=1, limit=50):
    """Extract messages from a specific group across all recent sessions."""
    messages = []
    cutoff = datetime.now() - timedelta(days=days)
    
    # Get recent session files sorted by modification time
    session_files = sorted(
        glob.glob(str(SESSIONS_DIR / '*.jsonl')),
        key=os.path.getmtime,
        reverse=True
    )
    
    for f in session_files[:20]:  # Check last 20 sessions
        # Quick check if group_id is in the file at all
        try:
            with open(f, 'r') as fh:
                content = fh.read()
                if group_id not in content:
                    continue
                
                # Parse line by line
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    try:
                        d = json.loads(line)
                        msg = d.get('message', {})
                        msg_content = msg.get('content', '')
                        timestamp = d.get('timestamp', '')
                        
                        # Check timestamp if available
                        if timestamp:
                            try:
                                msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                if msg_time.replace(tzinfo=None) < cutoff:
                                    continue
                            except:
                                pass
                        
                        # Process content
                        if isinstance(msg_content, list):
                            for c in msg_content:
                                if isinstance(c, dict) and c.get('type') == 'text':
                                    text = c['text']
                                    if group_id in text and 'sender' in text.lower():
                                        parsed = parse_whatsapp_message(text)
                                        if parsed:
                                            messages.append(parsed)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            continue
    
    # Deduplicate by content
    seen = set()
    unique = []
    for m in messages:
        key = f"{m['sender']}:{m['body'][:50]}"
        if key not in seen:
            seen.add(key)
            unique.append(m)
    
    return unique[:limit]


def parse_whatsapp_message(text):
    """Parse a WhatsApp message from session metadata."""
    # Extract sender label
    sender_match = re.search(r'"label":\s*"([^"]+)"', text)
    if not sender_match:
        return None
    
    sender_full = sender_match.group(1)
    # Clean up sender — take just the name part
    sender = sender_full.split('(')[0].strip() if '(' in sender_full else sender_full
    
    # Extract message body — it's the text after all metadata blocks
    # Split on double newlines and take non-metadata parts
    parts = text.split('\n\n')
    body_parts = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Skip metadata blocks
        if any(p.startswith(prefix) for prefix in [
            '{', '```', 'Conversation info', 'Sender', 'System', 
            'Replied message', 'Read HEARTBEAT'
        ]):
            continue
        # Skip if it looks like JSON
        if p.startswith('[') and p.endswith(']'):
            continue
        body_parts.append(p)
    
    if not body_parts:
        return None
    
    body = body_parts[-1]  # Last non-metadata part is usually the message
    
    # Skip if body is too short or looks like metadata
    if len(body) < 1 or body.startswith('"') or body.startswith('NO_REPLY'):
        return None
    
    return {
        'sender': sender,
        'body': body
    }


def format_messages(messages):
    """Format messages as simple text."""
    lines = []
    for m in messages:
        lines.append(f"{m['sender']}: {m['body']}")
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: group_messages.py <group_id> [--days N] [--limit N]", file=sys.stderr)
        sys.exit(1)
    
    group_id = sys.argv[1]
    days = 1
    limit = 50
    
    # Parse optional args
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--days' and i + 1 < len(args):
            days = int(args[i + 1])
        elif arg == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
    
    messages = extract_group_messages(group_id, days=days, limit=limit)
    
    if not messages:
        print("NO_MESSAGES_FOUND")
    else:
        print(format_messages(messages))
        print(f"\n--- {len(messages)} messages ---", file=sys.stderr)


if __name__ == '__main__':
    main()
