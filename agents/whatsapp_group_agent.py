#!/usr/bin/env python3
"""
WhatsAppGroupAgent (אודיה) — Runtime wrapper.
Converts the prompt-based agent into a callable service.

This module:
1. Loads the group agent prompt template
2. Fills in context variables (group profile, members, memory, messages)
3. Returns a ready-to-spawn prompt + expected output format
4. Can validate agent output against the contract

Usage:
    # Prepare a prompt for spawning
    python3 whatsapp_group_agent.py --prepare \\
        --group-id "family" \\
        --new-message '{"sender":"דני","text":"מישהו יודע מה השעה?"}'
    
    # Validate agent output
    echo '{"shouldReply":true,...}' | python3 whatsapp_group_agent.py --validate --group-id "family"
"""

import argparse
import json
import os
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get("DVORAH_WORKSPACE", Path.home() / ".openclaw" / "workspace"))

# Add scripts to path for service imports
sys.path.insert(0, str(WORKSPACE / "scripts"))
from context_service import load_context
from policy_service import evaluate as evaluate_policy
from qa_service import run_qa


def load_prompt_template() -> str:
    """Load the group agent prompt template."""
    prompt_path = WORKSPACE / "agents" / "group_agent_prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Group agent prompt not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def load_group_profile(group_id: str) -> str:
    """Load specific group profile from KNOWN_GROUPS.md."""
    groups_path = WORKSPACE / "state" / "KNOWN_GROUPS.md"
    if not groups_path.exists():
        return f"[Group profile not found for {group_id}]"
    
    content = groups_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    result = []
    capturing = False
    
    for line in lines:
        if line.startswith("## ") or line.startswith("# "):
            if group_id.lower() in line.lower():
                capturing = True
            elif capturing:
                break
        if capturing:
            result.append(line)
    
    return "\n".join(result) if result else f"[No profile found for group: {group_id}]"


def load_group_members(group_id: str = "") -> str:
    """Load group members."""
    members_path = WORKSPACE / "state" / "GROUP_MEMBERS.md"
    if not members_path.exists():
        return "[No group members file]"
    content = members_path.read_text(encoding="utf-8")
    # TODO: Filter by group_id when members file supports it
    return content[:4000]  # Truncate


def load_group_memory(group_id: str = "") -> str:
    """Load recent group memory."""
    memory_path = WORKSPACE / "state" / "GROUP_MEMORY.md"
    if not memory_path.exists():
        return "[No group memory]"
    content = memory_path.read_text(encoding="utf-8")
    # Return last ~2000 chars (most recent)
    return content[-2000:] if len(content) > 2000 else content


def prepare_prompt(
    group_id: str,
    new_message: dict,
    recent_messages: list = None,
) -> dict:
    """Prepare a complete prompt for spawning the group agent.
    
    Returns:
        {
            "prompt": str,          # Ready-to-use prompt
            "context_files": list,  # Files that were loaded
            "constraints": list,    # Policy constraints
            "group_role": str,      # Role for this group
        }
    """
    recent_messages = recent_messages or []
    
    # Load template
    template = load_prompt_template()
    
    # Load context pieces
    group_profile = load_group_profile(group_id)
    group_members = load_group_members(group_id)
    group_memory = load_group_memory(group_id)
    
    # Format recent messages
    if recent_messages:
        recent_text = "\n".join(
            f"[{m.get('time', '?')}] {m.get('sender', '?')}: {m.get('text', '')}"
            for m in recent_messages
        )
    else:
        recent_text = "[No recent messages provided]"
    
    # Format new message
    new_msg_text = f"[{new_message.get('time', 'now')}] {new_message.get('sender', '?')}: {new_message.get('text', '')}"
    
    # Fill template variables
    prompt = template
    prompt = prompt.replace("{{GROUP_PROFILE}}", group_profile)
    prompt = prompt.replace("{{GROUP_MEMBERS}}", group_members)
    prompt = prompt.replace("{{GROUP_MEMORY}}", group_memory)
    prompt = prompt.replace("{{RECENT_MESSAGES}}", recent_text)
    prompt = prompt.replace("{{NEW_MESSAGE}}", new_msg_text)
    
    # Get policy constraints
    # Extract role from group profile
    role = "active"  # default
    if "role" in group_profile.lower():
        for line in group_profile.split("\n"):
            if "role" in line.lower():
                if "observer" in line.lower():
                    role = "observer"
                elif "responder" in line.lower():
                    role = "responder"
                elif "representative" in line.lower():
                    role = "representative"
                break
    
    policy = evaluate_policy("group", "SEND", {"role": role})
    
    context_files = [
        "agents/group_agent_prompt.md",
        "state/KNOWN_GROUPS.md",
        "state/GROUP_MEMBERS.md",
        "state/GROUP_MEMORY.md",
    ]
    
    return {
        "prompt": prompt,
        "context_files": context_files,
        "constraints": policy["constraints"],
        "group_role": role,
        "policy_summary": {
            "policies_loaded": policy["policies_loaded"],
            "approval": policy["approval"],
        },
    }


def validate_output(agent_output: dict, group_id: str = "") -> dict:
    """Validate agent output against QA checks and contract."""
    
    # Check contract compliance
    required_fields = ["shouldReply", "confidence", "intent", "score", "reasoning", "draftReply"]
    missing = [f for f in required_fields if f not in agent_output]
    
    contract_ok = len(missing) == 0
    
    # Run QA service
    # Get role for constraints
    group_profile = load_group_profile(group_id) if group_id else ""
    constraints = []
    if "observer" in group_profile.lower():
        constraints.append("BLOCKED: role=observer — no external actions allowed")
    
    qa_result = run_qa(agent_output, "group", constraints)
    
    return {
        "contract_valid": contract_ok,
        "missing_fields": missing,
        "qa": qa_result,
        "overall": contract_ok and qa_result["passed"],
    }


def main():
    parser = argparse.ArgumentParser(description="WhatsAppGroupAgent runtime")
    parser.add_argument("--prepare", action="store_true", help="Prepare prompt for spawning")
    parser.add_argument("--validate", action="store_true", help="Validate agent output")
    parser.add_argument("--group-id", required=True, help="Group ID")
    parser.add_argument("--new-message", default="", help="New message JSON")
    parser.add_argument("--recent-messages", default="", help="Recent messages JSON array")
    args = parser.parse_args()
    
    if args.prepare:
        new_message = json.loads(args.new_message) if args.new_message else {"sender": "unknown", "text": "test"}
        recent = json.loads(args.recent_messages) if args.recent_messages else []
        
        result = prepare_prompt(args.group_id, new_message, recent)
        # Output summary (not full prompt — too large)
        summary = {
            "ready": True,
            "prompt_length": len(result["prompt"]),
            "context_files": result["context_files"],
            "constraints_count": len(result["constraints"]),
            "group_role": result["group_role"],
            "policy_summary": result["policy_summary"],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    elif args.validate:
        agent_output = json.loads(sys.stdin.read())
        result = validate_output(agent_output, args.group_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
