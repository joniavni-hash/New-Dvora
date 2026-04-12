# PolicyService — Specification
<!-- Status: Active -->

## Purpose
Structured constraint checking. Given a domain and action type, returns applicable policies and constraints.

## Interface
```
Input:  { domain: string, action_type: string, metadata: dict }
Output: { policies_loaded: list, constraints: list[string], approval_required: string }
```

## Constraint Extraction
Reads policy files and extracts actionable constraints as a flat list of rules.
Example: ["role=observer → no reply", "max 3 consecutive replies", "no private info disclosure"]

## Approval Routing
Based on action_type from `core/approval_gate.md`:
- READ → "none"
- DRAFT → "dvorah_review"
- SEND → "dvorah_approve" (sensitive → "yoni_approve")
- MUTATE → "dvorah_only"
