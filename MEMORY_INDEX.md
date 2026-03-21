# MEMORY_INDEX.md
<!-- Status: Canonical -->
<!-- Purpose: Memory routing -->
<!-- Authority: Source of truth -->
לא טוענים את כל הקבצים. בוחרים לפי סוג המשימה.
## אם המשימה על יוני אישית
קראי:
- `memory/PROFILE.md`
- `memory/PREFERENCES.md`
## אם המשימה על אנשים, קשרים או משפחה
קראי:
- `memory/RELATIONSHIPS.md`
- `memory/PRIVATE_FACTS.md` רק אם הכרחי
## אם המשימה על פרויקט פעיל או מה קורה עכשיו
קראי:
- `memory/ACTIVE_CONTEXT.md`
- `state/OPEN_TASKS.md`
- `state/RECENT_DECISIONS.md`
## אם המשימה על קבוצות, WhatsApp או התנהגות בשיחה
קראי (בסדר הזה):
1. `policies/GROUP_BEHAVIOR_POLICY.md` — entry point
2. `policies/GROUP_INTELLIGENCE.md` — decision engine
3. `state/KNOWN_GROUPS.md` — פרופילי קבוצות
4. `state/GROUP_MEMBERS.md` — פרופילי חברים (אם רלוונטי)
5. `state/GROUP_MEMORY.md` — זיכרון קבוצתי (אם צריך הקשר)
6. `policies/GROUP_QA.md` — QA לפני שליחה
## אם המשימה רגישה
קראי:
- `policies/PRIVACY_POLICY.md`
- `policies/EXTERNAL_ACTIONS_POLICY.md`
## אם המשימה על מערכת מחוברת
קראי:
- `CAPABILITY_INDEX.md`
- הקובץ המתאים ב-`integrations/`
- ואם צריך, גם את ה-runbook המתאים ב-`runbooks/`
- אם המשימה רגישה או כרוכה בפעולה חיצונית, גם `policies/EXTERNAL_ACTIONS_POLICY.md`
## אם יש שאלה האם לשמור משהו לזיכרון
קראי:
- `policies/MEMORY_POLICY.md`

## אם יוני מתקן אותי או אני צריכה לבדוק דפוסי טעויות
קראי:
- `memory/corrections.md`
- `policies/CORRECTION_POLICY.md`

## אם צריך לבדוק ביצועים או מדדים
הריצי:
- `python3 scripts/metrics.py`
- או קראי `state/metrics_latest.json`
## כלל ברזל
לא טוענים secrets כברירת מחדל.
