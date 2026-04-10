# CACHE_POLICY.md

מטרת הקובץ: לצמצם קריאות חיצוניות, זמן תגובה ועלות.

## Restaurant lookup cache
- Availability checks: cache ל-10 דקות
- Restaurant provider mapping: cache קבוע עד שינוי ידני
- Slug / venue_id / booking provider: cache קבוע

## Search cache rules
- אם אותה מסעדה נבדקה שוב בתוך 10 דקות, לא מתחילים חיפוש מחדש מהווב
- קודם בודקים registry ורק אז פונים ל-provider
- לא משתמשים בדפדפן אם כבר יש endpoint usable

## Booking cache rules
- לא שומרים cache על פעולת הזמנה עצמה
- כן שומרים cache על זמינות שנמצאה, רק לצורך מענה מהיר

## OTP flows
- אין cache ל-OTP
- שומרים רק את ההכרעה התהליכית: OTP = חיכוך גבוה
