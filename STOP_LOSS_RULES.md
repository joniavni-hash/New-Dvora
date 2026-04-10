# STOP_LOSS_RULES.md

מטרת הקובץ: למנוע בזבוז זמן, retries מיותרים ועלויות.

## Global rules
- לא יותר מ-2 ניסיונות לאותו flow שנכשל מאותה סיבה
- לא יותר מ-browser fallback אחד לכל משימה
- אם יש endpoint usable, לא עוברים לדפדפן

## OTP rules
- מקסימום 2 ניסיונות
- אם OTP לא עובד, עוצרים ומבקשים ידני או session קבוע
- לא שורפים turn שלם על retries של קוד

## Restaurant search rules
- קודם registry
- אחר כך provider direct call
- אם provider אחד נכשל, מנסים provider שני לכל היותר
- לא עושים exploratory browsing אם כבר ברור שה-provider הוא Ontopo/Tabit

## Reservation outcome rules
- `seat` → להחזיר מייד שיש מקום
- `callback` → להחזיר שזה בקשה לצוות האירוח
- `disabled` → להחזיר שאין מקום
- לא לחפור מעבר לזה בלי שביקשו

## Escalation
אם flow נתקע:
1. לציין בקצרה מה נתקע
2. להציע חלופה אחת טובה
3. לעצור
