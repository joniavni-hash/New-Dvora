#!/usr/bin/env python3
"""
ContextService — Automated context loading for Dvorah's Orchestrator.
Reads domain-specific files and assembles a context block.

Usage:
    python3 context_service.py --domain group --group-id "family"
    python3 context_service.py --domain email
    python3 context_service.py --domain fitness
    python3 context_service.py --domain general
"""

import argparse
import json
import os
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

# Domain → files mapping (from core/context_loader.md)
DOMAIN_FILES = {
    "group": [
        "state/KNOWN_GROUPS.md",
        "state/GROUP_MEMBERS.md",
        "state/GROUP_MEMORY.md",
    ],
    "email": [
        "integrations/OUTLOOK.md",
        "state/OPEN_TASKS.md",
    ],
    "fitness": [
        "state/fitness_tracker.md",
    ],
    "legal": [
        # Legal docs provided per-request
    ],
    "travel": [
        # Travel preferences from memory (loaded dynamically)
    ],
    "research": [
        "state/OPEN_TASKS.md",
    ],
    "general": [
        # Scan state/ file names only
    ],
}

# Always loaded
ALWAYS_LOAD = [
    "IDENTITY.md",
]

# Token budget (rough estimate: 1 token ≈ 4 chars)
MAX_CHARS = 16000  # ~4000 tokens


def read_file(path: Path, max_chars: int = 8000) -> str | None:
    """Read a file, truncating if needed."""
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[... truncated at {max_chars} chars]"
        return content
    except Exception as e:
        return f"[error reading {path}: {e}]"


def filter_group_context(content: str, group_id: str) -> str:
    """Extract only the section for a specific group from KNOWN_GROUPS.md."""
    if not group_id or not content:
        return content
    
    lines = content.split("\n")
    result = []
    capturing = False
    
    for line in lines:
        if line.startswith("## ") or line.startswith("# "):
            if group_id.lower() in line.lower():
                capturing = True
            elif capturing:
                break  # Hit next section
        if capturing:
            result.append(line)
    
    return "\n".join(result) if result else content


def scan_state_files() -> str:
    """Return just filenames in state/ for general domain."""
    state_dir = WORKSPACE / "state"
    if not state_dir.exists():
        return "[state/ directory not found]"
    
    files = sorted(f.name for f in state_dir.iterdir() if f.is_file())
    return "Files in state/:\n" + "\n".join(f"- {f}" for f in files)


def load_context(domain: str, metadata: dict = None) -> dict:
    """Load context for a domain. Returns structured result."""
    metadata = metadata or {}
    files_loaded = []
    context_parts = []
    total_chars = 0
    
    # Always load identity (trimmed)
    for fname in ALWAYS_LOAD:
        fpath = WORKSPACE / fname
        content = read_file(fpath, max_chars=2000)
        if content:
            files_loaded.append(fname)
            context_parts.append(f"### {fname}\n{content}")
            total_chars += len(content)
    
    # Domain-specific files
    domain_files = DOMAIN_FILES.get(domain, [])
    
    for fname in domain_files:
        if total_chars >= MAX_CHARS:
            break
        
        fpath = WORKSPACE / fname
        remaining = MAX_CHARS - total_chars
        content = read_file(fpath, max_chars=min(8000, remaining))
        
        if content is None:
            continue
        
        # Special filtering for group context
        if domain == "group" and "KNOWN_GROUPS" in fname:
            group_id = metadata.get("group_id", "")
            if group_id:
                content = filter_group_context(content, group_id)
        
        files_loaded.append(fname)
        context_parts.append(f"### {fname}\n{content}")
        total_chars += len(content)
    
    # General domain: scan state/
    if domain == "general":
        scan = scan_state_files()
        context_parts.append(f"### State Overview\n{scan}")
        total_chars += len(scan)
    
    context_block = "\n\n---\n\n".join(context_parts)
    
    return {
        "domain": domain,
        "files_loaded": files_loaded,
        "context_block": context_block,
        "chars": total_chars,
        "tokens_estimate": total_chars // 4,
    }


def main():
    parser = argparse.ArgumentParser(description="ContextService — load domain context")
    parser.add_argument("--domain", required=True, choices=list(DOMAIN_FILES.keys()))
    parser.add_argument("--group-id", default="", help="Group ID for filtering (group domain)")
    parser.add_argument("--output", choices=["json", "text"], default="json")
    args = parser.parse_args()
    
    metadata = {}
    if args.group_id:
        metadata["group_id"] = args.group_id
    
    result = load_context(args.domain, metadata)
    
    if args.output == "json":
        # Don't include full context_block in JSON summary
        summary = {k: v for k, v in result.items() if k != "context_block"}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(result["context_block"])


if __name__ == "__main__":
    main()
