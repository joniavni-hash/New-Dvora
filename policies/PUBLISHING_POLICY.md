# PUBLISHING_POLICY.md
<!-- Status: Canonical -->
<!-- Purpose: Guidelines and rules for social media publishing -->
<!-- Authority: System policy -->

## מדיניות פרסום אוטומטי

### ⚖️ עקרונות כלליים

**1. Approval First**
- כל פרסום עובר אישור לפני פרסום אמיתי
- אין פרסום אוטומטי ללא מעקב אנושי
- draft → validate → approve → publish

**2. Quality Control**
- בדיקת תוכן, מדיה וחיבורים לפני פרסום
- וולידציה של OAuth tokens וscopes
- בדיקת גודלי קבצים והגבלות פלטפורמה

**3. Safe Defaults**
- פרסום בפרטיות/draft mode כברירת מחדל
- מעקב אחרי כל פרסום שהתבצע
- שמירת logs מפורטים

---

## 🔄 זרימת אישורים

### שלב 1: יצירת Draft
```python
draft = gateway.create_draft(
    content="תוכן הפרסום",
    platforms=["instagram", "tiktok"],
    media_paths=["image.jpg"],
    priority="medium"
)
```

### שלב 2: Validation
```python
validation = gateway.validate_draft(draft_id)
# בודק: OAuth, תוכן, מדיה, הגבלות פלטפורמה
```

### שלב 3: בקשת אישור
```python
gateway.request_approval(draft_id, approver="yoni")
# שליחת התראה לאישור
```

### שלב 4: אישור
```python
gateway.approve_draft(draft_id, approved=True, approver="yoni")
```

### שלב 5: פרסום
```python
result = gateway.publish_draft(draft_id)
# פרסום בפועל לכל הפלטפורמות
```

---

## 🛡️ בדיקות חובה

### לפני כל פרסום:
- ✅ **OAuth תקף:** tokens לא פגו, scopes נכונים
- ✅ **חיבור פעיל:** API מגיב ומאומת
- ✅ **תוכן תקין:** אורך מתאים, ללא תוכן אסור
- ✅ **מדיה תקינה:** קבצים קיימים, פורמט נתמך, גודל מתאים
- ✅ **הרשאות:** אישור מפורש למפרסם

### אם חסר משהו:
**לא לפרסם** ולהחזיר שגיאה מפורטת:
- מה חסר
- איזה account מחובר (אם בכלל)
- איך לתקן
- מה צריך להגדיר

---

## 📱 דרישות לפי פלטפורמה

### Instagram
- **חיבור:** Facebook for Developers App + Instagram Business Account
- **Scopes:** `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
- **מדיה:** חובה לפחות קובץ אחד
- **תמונות:** JPG/PNG, עד 8MB, יחס גובה-רוחב: 1:1, 4:5, 1.91:1
- **וידאו:** MP4/MOV, עד 100MB, 3-60 שניות
- **Caption:** עד 2,200 תווים
- **Carousel:** עד 10 פריטים

### TikTok
- **חיבור:** TikTok for Developers App + OAuth2
- **Scopes:** `user.info.basic`, `video.publish`
- **מדיה:** וידאו (מומלץ)
- **וידאו:** MP4/MOV/AVI/WebM, עד 2GB, 1-180 שניות
- **Caption:** עד 4,000 תווים
- **יחס גובה-רוחב:** 9:16 מומלץ (אנכי)

### Facebook
- **חיבור:** Facebook for Developers App
- **Scopes:** `pages_manage_posts`, `pages_read_engagement`
- **תמונות:** JPG/PNG, עד 4MB
- **וידאו:** MP4/MOV, עד 1.75GB, עד 240 דקות
- **Caption:** עד 63,206 תווים

---

## 🚨 מצבי כישלון

### 1. Connection Failed
```json
{
  "connected": false,
  "status": "missing_credentials",
  "errors": ["INSTAGRAM_ACCESS_TOKEN not configured"],
  "fix_hints": ["Set INSTAGRAM_ACCESS_TOKEN environment variable"]
}
```

**פעולה:** לא לנסות לפרסם, להחזיר הוראות תיקון מפורטות

### 2. Content Validation Failed
```json
{
  "valid": false,
  "errors": ["Caption too long: 2500 > 2200 characters"],
  "platform": "instagram"
}
```

**פעולה:** לא לפרסם, לתקן תוכן ולנסות שוב

### 3. Media Issues
```json
{
  "valid": false,
  "errors": ["File not found: /path/to/missing.jpg"]
}
```

**פעולה:** לא לפרסם, לוודא שכל הקבצים קיימים

### 4. API Error
```json
{
  "success": false,
  "error": "Instagram API error: 400",
  "details": "Invalid media format"
}
```

**פעולה:** לתעד שגיאה, לא לנסות שוב אוטומטית

---

## 📊 מעקב ודיווח

### לכל פרסום מוצלח:
- שמירת post_id, post_url
- רישום timestamp ופלטפורמה
- עדכון סטטיסטיקות
- הוספה ל-completed queue

### לכל כישלון:
- רישום שגיאה מפורטת
- שמירת context (draft, platform, error)
- ספירת כשלונים לכל פלטפורמה
- התראה אם שיעור כשלונות גבוה

### דוח יומי:
```
📊 Publishing Stats - [תאריך]
✅ Published: 15 posts
❌ Failed: 2 posts
📱 Instagram: 8 posts (1 failed)
🎵 TikTok: 5 posts
📘 Facebook: 2 posts (1 failed)
```

---

## 🔐 אבטחה ופרטיות

### טיפול ב-Access Tokens:
- **לא לרשום** tokens בלוגים או traces
- **לא לשלוח** tokens בהודעות שגיאה
- **בדיקה תקופתית** של תוקף tokens
- **Rotation אוטומטי** כשאפשר

### תוכן רגיש:
- **לא לפרסם** מידע אישי או עסקי רגיש
- **בדיקת מילות מפתח** אסורות לפני פרסום
- **מצב פרטי** כברירת מחדל עד אישור מפורש

### Audit Trail:
- כל פעולה מתועדת עם timestamp ו-user
- שמירת draft מקורי גם אחרי עריכות
- מעקב אחרי מי אישר ומתי

---

## 🛠️ התאוששות מכישלונים

### אם פלטפורמה אחת נכשלת:
- המשך פרסום לפלטפורמות אחרות
- תיעוד הכישלון
- ניסיון חוזר לאחר זמן מוגדר

### אם כל הפלטפורמות נכשלות:
- עצירת פרסום
- התראה למפעיל
- שמירת draft לניסיון עתידי

### Recovery אוטומטי:
- בדיקה תקופתית של drafts שנכשלו
- ניסיון חוזר אוטומטי אחרי 1-6 שעות
- מגבלה על מספר ניסיונות

---

## 🔄 תחזוקה שוטפת

### יומי:
- בדיקת חיבורי API
- ניקוי drafts ישנים (>7 ימים)
- דוח שגיאות מצטברות

### שבועי:
- רענון access tokens
- בדיקת שינויים ב-API של פלטפורמות
- סיכום סטטיסטיקות פרסום

### חודשי:
- ביקורת מדיניות פרסום
- עדכון הגבלות פלטפורמות
- אופטימיזציה של תהליכים

---

## 📞 יצירת קשר עם תמיכה

### אם יש בעיות עקביות:
1. **Instagram:** Meta for Developers Support
2. **TikTok:** TikTok for Developers Support  
3. **Facebook:** Facebook API Support

### מידע לכלול בפנייה:
- App ID ו-Client ID
- שגיאות API מדויקות  
- צעדי שחזור
- Timestamps של בעיות