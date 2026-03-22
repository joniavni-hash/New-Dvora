#!/usr/bin/env python3
"""
Group Agent Context Assembler
Reads the prompt template and fills in context for a specific group message.
Used by Dvorah to prepare sub-agent tasks.

Usage:
    python3 scripts/group_agent_context.py <group_id> <message_json>
    
Returns the assembled prompt to stdout.
"""

import json
import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def read_file(path):
    """Read a file, return empty string if not found."""
    full = BASE_DIR / path
    if full.exists():
        return full.read_text(encoding='utf-8')
    return ''


def extract_group_profile(known_groups_content, group_id):
    """Extract a specific group's profile from KNOWN_GROUPS.md."""
    blocks = re.split(r'^## ', known_groups_content, flags=re.MULTILINE)
    for block in blocks[1:]:
        if group_id in block:
            return block.strip()
    return f"Unknown group: {group_id}"


def extract_group_members(members_content, group_name):
    """Extract members for a specific group from GROUP_MEMBERS.md."""
    # Find the section for this group
    blocks = re.split(r'^## ', members_content, flags=re.MULTILINE)
    result = []
    for block in blocks[1:]:
        if group_name.lower() in block.lower():
            result.append(block.strip())
    return '\n\n'.join(result) if result else "No member profiles for this group."


def extract_group_memory(memory_content, group_name):
    """Extract recent memory for a specific group."""
    # Simple extraction — look for group name in memory
    lines = memory_content.split('\n')
    relevant = []
    in_section = False
    for line in lines:
        if group_name.lower() in line.lower():
            in_section = True
        elif line.startswith('## ') and in_section:
            in_section = False
        if in_section:
            relevant.append(line)
    return '\n'.join(relevant[-30:]) if relevant else "No recent memory for this group."


def assemble_prompt(group_id, new_message, recent_messages=None):
    """Assemble the full prompt for the group agent."""
    template = read_file('agents/group_agent_prompt.md')
    known_groups = read_file('state/KNOWN_GROUPS.md')
    members = read_file('state/GROUP_MEMBERS.md')
    memory = read_file('state/GROUP_MEMORY.md')
    
    # Extract group profile
    group_profile = extract_group_profile(known_groups, group_id)
    
    # Get group name from profile (first line)
    group_name = group_profile.split('\n')[0] if group_profile else "Unknown"
    
    # Extract relevant members
    group_members = extract_group_members(members, group_name)
    
    # Extract relevant memory
    group_memory = extract_group_memory(memory, group_name)
    
    # Recent messages
    recent = recent_messages or "No recent messages available."
    if isinstance(recent, list):
        recent = '\n'.join(recent)
    
    # Fill template
    prompt = template
    prompt = prompt.replace('{{GROUP_PROFILE}}', group_profile)
    prompt = prompt.replace('{{GROUP_MEMBERS}}', group_members)
    prompt = prompt.replace('{{GROUP_MEMORY}}', group_memory)
    prompt = prompt.replace('{{RECENT_MESSAGES}}', recent)
    prompt = prompt.replace('{{NEW_MESSAGE}}', new_message)
    
    return prompt


def main():
    if len(sys.argv) < 3:
        print("Usage: group_agent_context.py <group_id> <message_json>", file=sys.stderr)
        sys.exit(1)
    
    group_id = sys.argv[1]
    message = sys.argv[2]
    
    prompt = assemble_prompt(group_id, message)
    print(prompt)


if __name__ == '__main__':
    main()
