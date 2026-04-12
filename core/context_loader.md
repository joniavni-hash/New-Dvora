# ContextLoader
<!-- Status: Active -->
<!-- Purpose: Assemble relevant context for each agent invocation -->

## תפקיד
לפני כל הפעלת agent, ContextLoader מרכיב את ה-context הרלוונטי בלבד. לא הכל — רק מה שצריך.

## מיפוי Domain → Context Files

| Domain | קבצים לטעון |
|--------|-------------|
| **group** | state/KNOWN_GROUPS.md (פרופיל הקבוצה), state/GROUP_MEMORY.md, state/GROUP_MEMBERS.md, 10 הודעות אחרונות |
| **email** | integrations/OUTLOOK.md, state/OPEN_TASKS.md (אם רלוונטי) |
| **fitness** | state/fitness_tracker.md |
| **legal** | מסמך רלוונטי (יוני מספק) |
| **travel** | memory/ (העדפות נסיעות), הזמנות פעילות |
| **research** | memory/ (הקשר רלוונטי), שאלת המחקר, state/OPEN_TASKS.md (אם קשור) |
| **general** | state/ (סריקה מהירה של שמות קבצים) |

## תמיד נטען (כל domain)
- IDENTITY.md — מי אנחנו
- הקשר השיחה הנוכחי (אם רלוונטי)

## זרימה
```
1. דבורה מזהה domain
2. ContextLoader טוען קבצים לפי הטבלה
3. מסנן רק מידע רלוונטי (לא כל הקובץ אם מיותר)
4. מרכיב context block ל-task prompt
```

## עקרון
- טוען מעט אבל מדויק
- עדיף context חסר מ-context מוצף (agent מבקש אם חסר)
- קבצים גדולים → רק חלקים רלוונטיים

## הרחבה
כשנוסף domain חדש → שורה חדשה בטבלה. לא צריך קוד.
