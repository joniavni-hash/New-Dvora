# CRON_SAFETY_POLICY.md
<!-- Status: Canonical -->
<!-- Purpose: Prevent cron jobs.json corruption and edit failures -->
<!-- Authority: System policy -->

## מדיניות עבודה עם Cron Jobs

### ⚠️ אסור לעשות
1. **אסור להשתמש ב-edit tool על cron/jobs.json** - תמיד נכשל על whitespace
2. **אסור לכתוב ישירות לקובץ** - יוצר race conditions
3. **אסור להתעלם מכשלונות כתיבה** - זה מעיד על בעיה מערכתית

### ✅ חובה לעשות

#### לכל פעולה על cron jobs:
```python
from core.cron_manager import cron_manager

# קריאה
jobs = cron_manager.read_jobs()

# הוספת job
success = cron_manager.add_job(job_data)

# עדכון job
success = cron_manager.update_job(job_id, updates)

# מחיקת job
success = cron_manager.delete_job(job_id)
```

#### בדיקת תקינות לפני פעולה:
```python
health = cron_manager.health_check()
if health["status"] != "healthy":
    return f"Cron system unhealthy: {health['error']}"
```

### 🔄 Flow לטיפול בכשלונות

#### אם edit tool נכשל על cron files:
1. **לא לנסות שוב** עם edit tool
2. **השתמש ב-cron_manager** במקום
3. **דווח על התיקון** למשתמש

#### אם cron_manager נכשל:
1. בדוק health_check()
2. בדוק הרשאות קובץ
3. בדוק שאין תהליכים אחרים שכותבים
4. דווח למשתמש עם פרטים מלאים

### 🛡️ Race Condition Prevention

#### Locking מובנה:
- כל פעולה משתמשת ב-file locking
- Timeout של 5 שניות למניעת deadlock
- Atomic writes עם temp files

#### בדיקת תקינות:
```bash
python3 core/cron_manager.py health
```

### 📊 Monitoring

#### יומי ב-7:00:
בדיקה אוטומטית של תקינות cron system

#### בכל פעולה:
לוג של פעולות שנכשלו

### 🔧 Recovery Procedures

#### אם jobs.json פגום:
1. cron_manager יוצר backup אוטומטי
2. משחזר מבנה ברירת מחדל
3. משמר jobs קיימים אם אפשר

#### אם הרשאות לא נכונות:
```bash
chmod 700 ~/.openclaw/cron/
chmod 600 ~/.openclaw/cron/jobs.json
```

#### אם יש lock שנתקע:
```bash
rm ~/.openclaw/cron/.jobs.lock
```

## עקרון ברזל

**לעולם לא להשתמש ב-edit tool על cron/jobs.json**  
**תמיד דרך cron_manager בלבד**