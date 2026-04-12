# Orchestrator Flow — Dvorah (Runtime)
<!-- Status: Active -->
<!-- Purpose: Central routing and execution flow — automated pipeline -->
<!-- Switchover: 2026-03-23T20:10 — manual flow backed up as orchestrator_flow.md.old -->

## Pipeline
כל בקשה עוברת דרך `scripts/orchestrator.py`:

```
INTAKE → CONTEXT → CLASSIFY → POLICY → ROUTE → [INVOKE → QA → APPROVE → EXECUTE → WRITEBACK] → TRACE
```

שלבים 1-5 (INTAKE→ROUTE) רצים אוטומטית ע"י ה-pipeline.
שלבים 6-10 (INVOKE→WRITEBACK) מבוצעים ע"י דבורה לפי החלטת ה-pipeline.
שלב 11 (TRACE) אוטומטי.

## Runtime Services

| Step | Service | Script |
|------|---------|--------|
| CONTEXT | ContextService | `scripts/context_service.py` |
| CLASSIFY | Classifier (inline) | orchestrator.py |
| POLICY | PolicyService | `scripts/policy_service.py` |
| QA | QAService | `scripts/qa_service.py` |
| TRACE | TraceService | `scripts/trace_service.py` |

## Routing Table

| Domain | Agent | Notes |
|--------|-------|-------|
| general, fitness, email | direct | דבורה מטפלת |
| group | WhatsAppGroupAgent | `agents/whatsapp_group_agent.py` |
| legal | LegalAgent (מאשה) | `agents/legal-agent/` |
| research | ResearchAgent | `agents/research_agent_prompt.md` |
| travel | direct (Phase 3+) | |

## Approval Flows

| Flow | Rule |
|------|------|
| auto | בצעי מיד |
| dvorah_approve | בדקי בעצמך |
| yoni_approve | בקשי אישור |
| dvorah_only | דבורה בלבד |
| blocked | אל תבצעי |

## QA Checks (pre-send)
- Anti-patterns (חנופה, ניסוחים אסורים)
- Privacy leaks (טלפונים, מיילים)
- Group role enforcement (observer → block)
- Confidence threshold
- Message length limits

## Fallback
אם ה-pipeline נכשל → ראי `core/orchestrator_flow.md.old` (הזרימה הידנית הקודמת).

## כלל ברזל
דבורה לא מכילה לוגיקה דומיינית עמוקה. היא מנהלת flow. ה-agents מכילים את הידע.
