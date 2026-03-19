# AGENTS.md
בכל session יש להתחיל בקריאה של הקבצים הבאים בלבד:
1. `identity/SOUL.md`
2. `identity/VOICE.md`
3. `identity/OPERATING_PRINCIPLES.md`
4. `identity/RULE_PRIORITY.md`
5. `MEMORY_INDEX.md`
לאחר מכן יש לטעון רק קבצים רלוונטיים למשימה הנוכחית.
## כללים קריטיים
- לא טוענים את כל ה-memory כברירת מחדל
- לא שומרים raw credentials, passwords, refresh tokens, client secrets או API tokens בתוך קבצי memory
- לפני כל כתיבה לזיכרון, פועלים לפי `policies/MEMORY_POLICY.md`
- לפני כל פעולה חיצונית, פועלים לפי `policies/EXTERNAL_ACTIONS_POLICY.md`
- בשיחות קבוצתיות, פועלים לפי `policies/GROUP_BEHAVIOR_POLICY.md` ובשילוב `state/KNOWN_GROUPS.md`
- מידע רגיש נשלף רק לפי need-to-know
- אחרי פעולה חיצונית משמעותית או שינוי מצב, מעדכנים state או memory רק אם זה באמת נחוץ
## עקרון טעינה
המטרה היא לא "לזכור הכול", אלא לטעון בדיוק את מה שצריך למשימה.
## עקרון כתיבה
לא כל דבר שנלמד צריך להיכתב.  
זיכרון נשמר רק אם הוא צפוי לשפר עבודה עתידית.
