# CAPABILITY_INDEX.md

מטרת הקובץ הזה היא גילוי מהיר של מערכות מחוברות ונתיב טעינה נכון.
לפני ששואלים את יוני אם משהו מחובר, בודקים כאן.

## Email
Keywords:
- email
- mail
- inbox
- reply
- send email
- outlook
- gmail
- מייל
- תיבה
- תשובה למייל

Load order:
1. `integrations/OUTLOOK.md`
2. runbook רלוונטי מתוך `runbooks/`
3. `HEARTBEAT.md` רק אם המשימה קשורה לדיג'סט, followup, או בדיקה יזומה

Notes:
- Outlook הוא ברירת המחדל למיילים שוטפים
- Gmail נבדק רק אם יוני ביקש במפורש

## WhatsApp / Groups
Keywords:
- whatsapp
- group
- class group
- message the group
- summarize messages
- ווטסאפ
- קבוצה
- סיכום קבוצה

Load order:
1. `integrations/WHATSAPP.md`
2. `policies/GROUP_BEHAVIOR_POLICY.md`
3. `state/KNOWN_GROUPS.md`
4. `HEARTBEAT.md` אם מדובר בסיכום יומי

## Home / Devices
Keywords:
- control4
- home
- speaker
- tv
- device
- בית חכם
- רמקול
- טלוויזיה

Load order:
1. `integrations/CONTROL4.md`
2. `TOOLS.md` אם צריך שמות מקומיים או כינויים

## Rides / Gett
Keywords:
- gett
- taxi
- cab
- ride
- airport
- order a ride
- מונית
- נסיעה
- הזמיני מונית

Load order:
1. `integrations/GETT.md`
2. `policies/EXTERNAL_ACTIONS_POLICY.md`

Notes:
- אם צריך ממש לבצע הזמנה, דרוש אישור מפורש
- אם לא ברור איזה חשבון להשתמש, שואלים רק על בחירת החשבון, לא על עצם קיום החיבור
