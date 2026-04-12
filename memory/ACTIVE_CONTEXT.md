# ACTIVE_CONTEXT.md
Last updated: 2026-03-20
## פרויקטים פעילים

### דשבורד דבורה — Vercel
- URL: https://vercel-dashboard-two-ruby.vercel.app
- מצב: פעיל, מתעדכן כל 2 דקות מהמחשב via cron
- push script: scripts/dashboard_push.py
- קוד: vercel-dashboard/
- הושלם: 20.3.2026
### אוטומציית חשבוניות לתהילה
- יש flow פעיל לזיהוי חשבוניות והעברה לאחר אישור יוני
- מצב נוכחי: פעיל
- פרטים תפעוליים: `runbooks/FORWARD_INVOICES_TO_TEHILA.md`
### אינסטגרם ופייסבוק, וילה בפורטו ראפטי
- מטרה: 4 פוסטים בשבוע
- סגנון: תמונות, ללא מבצעים, קידום הוילה והאזור
- מצב נוכחי: מוכן לפרסום
- פרטים תפעוליים: `runbooks/POST_PORTO_CONTENT.md`
### הקמת אושר למתן
- סוכנת בתהליך הקמה עבור מתן
- שם נבחר: אושר
- סטטוס: ongoing

### שיפור עצמי — דבורה v2
- תוכנית 10 נקודות אושרה 22.3.2026
- הושלם: corrections log, health check script, heartbeat tracker, daily memory
- בתהליך: model routing, context compression
- ממתין ליוני: Brave API key

### אודיה (Odya) — סוכנת הודעות
- Sub-agent ראשון, מנתחת הודעות קבוצתיות
- POC הושלם בהצלחה 22.3.2026
- מצב: אפשרות ב' — מחליטה + עושה מחקר + מחזירה תשובה מוכנה
- Prompt: agents/group_agent_prompt.md
- Context assembler: scripts/group_agent_context.py

### דיאטת אבא חטוב
- התחלה: 22.3.2026
- יעד: 73→68 ק"ג
- מעקב: state/fitness_tracker.md
- סיכום שבועי: מוצ"ש 20:00
## תזכורת
הקובץ הזה הוא על מה שחי עכשיו, לא על ביוגרפיה ולא על secrets.
