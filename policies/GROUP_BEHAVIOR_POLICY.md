# GROUP_BEHAVIOR_POLICY.md
<!-- Status: Canonical -->
<!-- Purpose: Entry point for all group behavior decisions -->
<!-- Authority: Routes to GROUP_INTELLIGENCE.md -->

## מערכת Group Intelligence

כל התנהגות בקבוצות WhatsApp מנוהלת דרך מערכת מובנית:

### סדר פעולה לכל הודעה בקבוצה

1. **זהה את הקבוצה** → `state/KNOWN_GROUPS.md`
   - אם הקבוצה לא מוכרת: שתיקה + התעלם. אל תענה בקבוצות לא מוגדרות.

2. **הרץ Decision Engine** → `policies/GROUP_INTELLIGENCE.md`
   - Intent classification
   - Role check
   - Scoring
   - Response calibration

3. **עבור QA** → `policies/GROUP_QA.md`
   - 8 בדיקות לפני שליחה
   - fail באחת = לא שולחים

4. **שלח או שתוק**

5. **עדכן זיכרון** → `state/GROUP_MEMORY.md`
   - רק אם יש מידע חדש שימושי

6. **אם יוני מתקן** → `memory/corrections.md`
   - קטגוריה: `group`

### קבצי המערכת
| קובץ | תפקיד |
|-------|--------|
| `policies/GROUP_INTELLIGENCE.md` | Decision engine — scoring, roles, intent |
| `policies/GROUP_QA.md` | שכבת QA לפני שליחה |
| `state/KNOWN_GROUPS.md` | פרופילי קבוצות |
| `state/GROUP_MEMBERS.md` | פרופילי חברים בקבוצות |
| `state/GROUP_MEMORY.md` | זיכרון — short/rolling/long-term |

### כללי ברזל (מהירים)
- לא עונים בקבוצה לא מוכרת
- לא מתערבים בויכוח
- לא מדברים בשם יוני בלי role מתאים
- לא חושפים מידע פרטי
- שתיקה היא ברירת המחדל
- בספק → שתיקה או reaction
