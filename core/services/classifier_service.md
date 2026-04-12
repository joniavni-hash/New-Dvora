# ClassifierService — Specification
<!-- Status: Active -->

## Purpose
Classify incoming requests into intent, domain, and action_type.

## Interface
```
Input:  { message: string, source: string, metadata: dict }
Output: { intent: string, domain: string, action_type: string, confidence: float }
```

## Intent Types
- question — asking for information
- action — requesting an action be performed
- tracking — status check or follow-up
- conversation — casual chat
- command — direct instruction

## Domain Detection
Keywords and context signals → domain mapping:
- group message source → "group"
- email/outlook keywords → "email"
- diet/weight/exercise → "fitness"
- contract/legal/law → "legal"
- flight/hotel/travel → "travel"
- default → "general"

## Action Type
- Information retrieval → READ
- Prepare something → DRAFT
- Send/publish/execute → SEND
- Update settings/memory → MUTATE
