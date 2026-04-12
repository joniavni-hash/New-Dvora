# Core Services
<!-- Status: Active -->
<!-- Purpose: Index of all runtime services -->

## Services

| Service | Purpose | Script | Status |
|---------|---------|--------|--------|
| ContextService | Load relevant files per domain | `scripts/context_service.py` | ✅ Built |
| PolicyService | Evaluate constraints per domain/action | `scripts/policy_service.py` | ✅ Built |
| QAService | 6-check quality gate before actions | `scripts/qa_service.py` | ✅ Built |
| TraceService | JSONL logging of all decisions | `scripts/trace_service.py` | ✅ Built |
| ClassifierService | Intent + domain + action_type | Inline in Orchestrator | ✅ Built |
| ApprovalService | Action-level approval routing | Inline in Orchestrator | ✅ Built |

## Usage
All services are Python modules. Run via `exec` from Dvorah's context:

```bash
# Example: Get context for a group message
python3 scripts/context_service.py --domain group --group-id "family"

# Example: Check policy constraints
python3 scripts/policy_service.py --domain group --action-type SEND

# Example: Run QA on agent output
echo '{"decision":"reply","draft":"..."}' | python3 scripts/qa_service.py --domain group

# Example: Log a trace
python3 scripts/trace_service.py --log '{"trigger":"group_message","domain":"group",...}'
```
