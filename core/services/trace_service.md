# TraceService — Specification
<!-- Status: Active -->

## Purpose
JSONL logging of every significant decision. Mirrors `core/trace_logger.md`.

## Interface
```
Input:  TraceEntry dict
Output: Appended to state/traces/YYYY-MM-DD.jsonl
```

## TraceEntry Schema
```json
{
  "timestamp": "ISO-8601",
  "trigger": "group_message|dm|heartbeat|subagent_return",
  "domain": "group|email|fitness|legal|travel|general",
  "action_type": "READ|DRAFT|SEND|MUTATE",
  "agent": "WhatsAppGroupAgent|ResearchAgent|LegalAgent|direct",
  "model": "sonnet|opus|haiku",
  "context_loaded": ["file1.md", "file2.md"],
  "agent_decision": "summary string",
  "qa_result": "pass|fail",
  "qa_failures": [],
  "approval": "auto|dvorah|yoni|denied",
  "action_taken": "description of what was done",
  "memory_writes": ["file1.md"],
  "duration_ms": 1234,
  "shadow_mode": true
}
```

## Storage
- `state/traces/YYYY-MM-DD.jsonl` — one line per entry
- Retention: 14 days raw, then weekly summaries
