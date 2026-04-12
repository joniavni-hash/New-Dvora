# ApprovalGate
<!-- Status: Active -->
<!-- Purpose: Classify actions and enforce approval requirements -->

## סיווג פעולות

| סוג | הגדרה | אישור נדרש |
|------|--------|------------|
| **READ** | קריאת קבצים, חיפוש, שליפת מידע | ❌ חופשי |
| **DRAFT** | הכנת טיוטה (מייל, הודעה, סיכום) | דבורה בודקת |
| **SEND** | שליחת הודעה, מייל, API call | ✅ דבורה מאשרת |
| **MUTATE** | כתיבה ל-memory, state, שינוי הגדרות | ✅ דבורה בלבד |

## כללים

### SEND
- כל הודעה שיוצאת — דבורה רואה ומאשרת לפני שליחה
- הודעה לאדם שלא דיברנו איתו → דורש אישור יוני
- מייל חיצוני → דורש אישור יוני
- הודעה בקבוצה עם role=representative → דבורה מאשרת
- הודעה בקבוצה עם role=observer → חסום

### MUTATE
- רק דבורה כותבת ל-memory/ ו-state/
- Sub-agent מחזיר `memoryDelta`/`stateDelta` — דבורה מחליטה
- שינוי ב-SOUL.md, AGENTS.md, policies/ → דיווח ליוני

### DRAFT
- Agent מחזיר draft → דבורה בודקת QA → מאשרת או עורכת
- Draft לא יוצא אוטומטית

### כלל ברזל
**אף agent לא שולח ישירות. כל פעולה חיצונית עוברת דרך דבורה.**

## Pending Approvals
פעולות שממתינות לאישור יוני נשמרות ב-`state/approvals/`:
```
filename: YYYY-MM-DD_HH-MM_<type>_<target>.md
content: מה הפעולה, למה, draft, סטטוס
```

## אכיפה
1. **Prompt-level:** כל agent מקבל "אתה מחזיר DRAFT בלבד. לא שולח, לא כותב קבצים."
2. **Review-level:** דבורה בודקת כל output לפני ביצוע
3. **Trace-level:** כל פעולה מתועדת ב-TraceLogger
