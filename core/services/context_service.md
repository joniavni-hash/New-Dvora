# ContextService — Specification
<!-- Status: Active -->

## Purpose
Automated context assembly. Given a domain and metadata, returns exactly the files/sections needed.

## Interface
```
Input:  { domain: string, metadata: dict }
Output: { files_loaded: list, context_block: string, tokens_estimate: int }
```

## Domain Mappings
Mirrors `core/context_loader.md` but executable:
- group → KNOWN_GROUPS.md (filtered by group_id), GROUP_MEMBERS.md, GROUP_MEMORY.md, recent messages
- email → OUTLOOK.md, OPEN_TASKS.md
- fitness → fitness_tracker.md
- legal → user-provided doc + legal agent context
- research → relevant memory files + query
- general → state/ file listing scan

## Always Loaded
- IDENTITY.md (trimmed to essentials)
- Current conversation context

## Token Budget
Target: <4000 tokens per context block. Truncate large files to relevant sections.
