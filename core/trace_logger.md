# TraceLogger
<!-- Status: Active -->
<!-- Purpose: Log every agent invocation and significant action for debugging -->

## תפקיד
תיעוד כל החלטה ופעולה משמעותית. בלי trace — אין דרך לדעת למה משהו נשלח או לא.

## מתי מתעדים
- כל הפעלת sub-agent
- כל שליחת הודעה חיצונית (WhatsApp, email, API)
- כל כתיבה ל-memory/state
- כל ApprovalGate decision
- כל QA failure

## פורמט Trace

```markdown
### [timestamp]
- **trigger:** מה הפעיל (הודעת קבוצה, בקשת יוני, heartbeat...)
- **domain:** group / email / fitness / legal / travel / general
- **action_type:** READ / DRAFT / SEND / MUTATE
- **agent:** WhatsAppGroupAgent / ResearchAgent / direct (דבורה)
- **model:** sonnet / opus
- **context_loaded:** [רשימת קבצים שנטענו]
- **agent_decision:** [summary של מה ה-agent החליט]
- **qa_result:** pass / fail (+ פירוט אם fail)
- **approval:** auto / dvorah / yoni / denied
- **action_taken:** [מה בוצע בפועל]
- **memory_writes:** [מה נכתב ל-memory/state, או none]
- **cost:** [tokens / estimated $]
- **duration:** [seconds]
```

## אחסון
- `state/traces/YYYY-MM-DD.md` — קובץ יומי
- Traces נשמרים 14 ימים, אחרי זה נדחסים לסיכום שבועי

## שימוש
- **דיבאג:** כשמשהו נשלח בטעות → בדוק trace
- **שיפור:** דפוסי QA failures → כלל חדש
- **עלויות:** מעקב יומי על שימוש ב-tokens

## כלל
**אם אין trace — כאילו לא קרה.** כל פעולה שעוברת ApprovalGate חייבת trace.
