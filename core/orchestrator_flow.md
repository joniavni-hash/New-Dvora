# Orchestrator Flow — Dvorah
<!-- Status: Active -->
<!-- Purpose: Central routing and execution flow for all requests -->

## זרימה — כל בקשה עוברת כאן

### 1. INTAKE
- קבלת הודעה/בקשה
- זיהוי מקור: DM / קבוצה / heartbeat / sub-agent return

### 2. CONTEXT
- **חובה:** סרוק `state/` ו-`memory/` לקבצים רלוונטיים
- טען לפי `core/context_loader.md`
- לעולם לא לומר "אין לי מידע" בלי שנסרק קודם

### 3. CLASSIFY
- **כוונה:** מה יוני רוצה? (שאלה, פעולה, מעקב, שיחה...)
- **Domain:** group / email / fitness / legal / travel / general
- **סוג פעולה:** READ / DRAFT / SEND / MUTATE
- **Legal Detection:** לפי `core/legal_intent_detection.md` - בדוק keywords, actions, attachments

### 4. POLICY
- טען policies רלוונטיים לפי `core/policy_engine.md`
- הוסף constraints ל-context

### 5. ROUTE
| סוג | ניתוב |
|------|--------|
| פשוט (שאלה, חישוב, תזכורת) | דבורה ישירות |
| הודעת קבוצה | WhatsAppGroupAgent (אודיה) |
| מחקר עמוק | ResearchAgent |
| תיאום לו"ז | SchedulingAgent (Phase 2) |
| חוזה/משפטי | LegalAgent (מאשה) ✅ |
| נסיעות | TravelAgent (Phase 3) |

### 6. INVOKE
- הרכב task prompt עם: task + context + constraints + outputFormat
- `sessions_spawn` עם model מתאים (sonnet כברירת מחדל)
- **אם agent צפוי לרוץ 30+ שניות (research, broad scope)** → שלחי ליוני הודעת ביניים: "חוקרת, חצי דקה..." / "בודקת, רגע..."
- agent מחזיר JSON לפי `core/agent_contract.md`

### 7. QA
- בדוק output לפי `core/qa_layer.md`
- כשל → עצור, דבורה מחליטה

### 8. APPROVE
- בדוק לפי `core/approval_gate.md`
- READ → חופשי
- DRAFT → דבורה בודקת
- SEND → דבורה מאשרת (רגיש → יוני מאשר)
- MUTATE → דבורה בלבד

### 9. EXECUTE
- בצע את הפעולה (שלח הודעה, עדכן, ענה)

### 10. WRITEBACK
- אם ה-agent החזיר memoryDelta → דבורה מחליטה אם לכתוב
- אם ה-agent החזיר stateDelta → דבורה מחליטה אם לעדכן
- **רק דבורה כותבת ל-memory/state**

### 11. TRACE
- תעד לפי `core/trace_logger.md`

---

## כלל ברזל
דבורה לא מכילה לוגיקה דומיינית עמוקה. היא מנהלת flow. ה-agents מכילים את הידע.
