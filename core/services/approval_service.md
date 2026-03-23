# ApprovalService — Specification
<!-- Status: Active -->

## Purpose
Route actions through appropriate approval flow based on action_type and sensitivity.

## Interface
```
Input:  { action_type: string, domain: string, target: string, sensitivity: string }
Output: { approval_flow: string, requires_yoni: bool, auto_approve: bool, reason: string }
```

## Approval Flows
Mirrors `core/approval_gate.md`:

| action_type | sensitivity | flow |
|-------------|-------------|------|
| READ | any | auto_approve |
| DRAFT | any | dvorah_review |
| SEND | low | dvorah_approve |
| SEND | high (new contact, external email) | yoni_approve |
| MUTATE | any | dvorah_only |

## Sensitivity Signals
- New recipient (never contacted) → high
- External email → high
- Group with role=observer → blocked
- SOUL.md/AGENTS.md/policies/ changes → yoni_approve
