# Orchestrator — Runtime Specification
<!-- Status: Active -->
<!-- Purpose: Executable specification for the Orchestrator runtime -->

## Overview
The Orchestrator is the **single entry point** for all incoming requests.
It replaces the 11-step manual flow in `orchestrator_flow.md` with a programmatic pipeline.

## Pipeline (matches orchestrator_flow.md)

```
INTAKE → CONTEXT → CLASSIFY → POLICY → ROUTE → INVOKE → QA → APPROVE → EXECUTE → WRITEBACK → TRACE
```

## Runtime Components

| Step | Service | File |
|------|---------|------|
| INTAKE | Orchestrator | `scripts/orchestrator.py` |
| CONTEXT | ContextService | `scripts/context_service.py` |
| CLASSIFY | Orchestrator (inline) | intent + domain + action_type |
| POLICY | PolicyService | `scripts/policy_service.py` |
| ROUTE | Orchestrator (routing table) | domain → agent mapping |
| INVOKE | Orchestrator | `sessions_spawn` with assembled prompt |
| QA | QAService | `scripts/qa_service.py` |
| APPROVE | Orchestrator (approval logic) | action_type → approval flow |
| EXECUTE | Orchestrator | tool calls |
| WRITEBACK | Orchestrator | memory/state writes |
| TRACE | TraceService | `scripts/trace_service.py` |

## Data Flow

```python
# Pseudocode
request = intake(message)
context = context_service.load(request.domain, request.metadata)
classification = classify(request, context)
constraints = policy_service.evaluate(classification.domain, classification.action_type)
agent, prompt = route(classification, context, constraints)
result = invoke(agent, prompt)  # sessions_spawn
qa_result = qa_service.check(result, constraints)
approval = approve(qa_result, classification.action_type)
if approval.approved:
    execute(result)
    writeback(result)
trace_service.log(request, classification, result, qa_result, approval)
```

## Integration with OpenClaw
The Orchestrator runs **inside Dvorah's main agent context**.
It is NOT a standalone daemon — it's a decision framework that Dvorah follows.
Services are Python modules that Dvorah can `exec` to get structured decisions.

## Shadow Mode
During migration, both paths run:
1. Dvorah's current manual flow (active)
2. Orchestrator pipeline (shadow — log only, don't execute)

Compare outputs to validate before switchover.
