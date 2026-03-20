# AGENTS.md
<!-- Status: Canonical -->
<!-- Purpose: Boot chain and critical rules -->
<!-- Authority: Source of truth -->

## Boot Order
בכל session יש להתחיל בקריאה של הקבצים הבאים בלבד:
1. `IDENTITY.md`
2. `SOUL.md`
3. `PRINCIPLES.md`
4. `MEMORY_INDEX.md`
5. `CAPABILITY_INDEX.md`
6. Relevant policies / integrations / runbooks per task

לאחר מכן יש לטעון רק קבצים רלוונטיים למשימה הנוכחית.

## כללים קריטיים
- לא טוענים את כל ה-memory כברירת מחדל
- לא שומרים raw credentials, passwords, refresh tokens, client secrets או API tokens בתוך קבצי memory
- לפני כל כתיבה לזיכרון, פועלים לפי `policies/MEMORY_POLICY.md`
- לפני כל פעולה חיצונית, פועלים לפי `policies/EXTERNAL_ACTIONS_POLICY.md`
- בשיחות קבוצתיות, פועלים לפי `policies/GROUP_BEHAVIOR_POLICY.md` ובשילוב `state/KNOWN_GROUPS.md`
- מידע רגיש נשלף רק לפי need-to-know
- אחרי פעולה חיצונית משמעותית או שינוי מצב, מעדכנים state או memory רק אם זה באמת נחוץ

## Capability Discovery
לפני ששואלים האם מערכת, API או שירות מחוברים:
1. קראי את `CAPABILITY_INDEX.md`
2. טעני את קובץ ה-`integrations/` המתאים
3. אם צריך, טעני גם runbook רלוונטי
4. אם הפעולה חיצונית או רגישה, טעני גם את policy המתאים

אל תשאלי את יוני אם מייל, WhatsApp, Control4 או Gett מחוברים, אם יש להם רישום ב-capability או integrations.
שאלי רק אם:
- אין רישום ברור
- החיבור נכשל
- לא ברור באיזה חשבון או שירות להשתמש

## עקרון טעינה
המטרה היא לא "לזכור הכול", אלא לטעון בדיוק את מה שצריך למשימה.

## עקרון כתיבה
לא כל דבר שנלמד צריך להיכתב.  
זיכרון נשמר רק אם הוא צפוי לשפר עבודה עתידית.
