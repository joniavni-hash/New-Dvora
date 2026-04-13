# HEARTBEAT.md - אתי
<!-- Status: Canonical -->
<!-- Purpose: Continuous monitoring behaviors -->
<!-- Authority: Source of truth -->

## ⏰ מחזור ניטור — כל 15 דקות

**בכל heartbeat:**

### 📊 Performance Monitoring
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/performance_monitor.py
```
- בדיקת זמני ריצה של כל סקריפט שרץ ב-24 שעות אחרונות
- השוואה לממוצע שבועי
- זיהוי anomalies (>150% מהממוצע)

### 🚨 Error Detection
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/error_scanner.py
```
- סריקת logs לשגיאות חדשות
- מעקב אחר שגיאות חוזרות
- ניתוח failure patterns

### 📈 Trend Analysis
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/trend_analyzer.py
```
- גידול קבצי זיכרון
- שינויים בשימוש resources
- ביצועים לאורך זמן

**תדירות התרעות:** מקסימום התרעה אחת לשעה על אותה בעיה

---

## 🔍 בדיקות מעמיקות — כל שעה

### System Health Deep Dive
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/system_health.py
```
- בדיקת connectivity לכל ה-APIs
- מדידת latency ל-services חיצוניים
- בדיקת disk space ו-memory usage

### Automation ROI Analysis
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/roi_analyzer.py
```
- מדידת זמן חסכון מכל אוטומציה
- זיהוי אוטומציות שלא משתמשים בהן
- חיפוש משימות חדשות לאוטומציה

**רק אם יש ממצאים משמעותיים → דווחי לדבורה**

---

## 📋 דיווח יומי לדבורה — 07:30

**בכל heartbeat אחרי 07:30 (לפני 08:00):**

```
🤖 דיווח אתי יומי — [תאריך]

⚡ ביצועים
- [סקריפטים איטיים אם יש]
- [שיעורי הצלחה אם חריגים]

🚨 שגיאות
- [שגיאות חדשות או חוזרות]

📊 מגמות
- [שינויים משמעותיים]

💡 המלצות
- [פעולות מומלצות אם יש]
```

**רק אם יש מה לדווח. אם הכל תקין → NO_REPLY**

---

## 🎯 זיהוי אוטומציות חדשות — שבועי ראשון

**בכל heartbeat ביום ראשון אחרי 08:30:**
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/automation_opportunities.py
```

- ניתוח משימות חוזרות מ-memory ו-tasks
- בדיקת פעולות ידניות שחוזרות על עצמן
- חישוב ROI פוטנציאלי
- הצעת תכנית יישום

**פורמט דיווח:**
```
🚀 הזדמנויות אוטומציה שבועיות

📝 זוהו:
1. [משימה] - חוזרת X פעמים, חיסכון צפוי: Y דקות/שבוע
2. [משימה] - [פרטים]

⭐ מומלץ לפתח:
1. [עדיפות גבוה] - [נימוק]

📊 ROI מוערך:
- השקעת פיתוח: X שעות
- חיסכון: Y שעות/חודש
```

---

## 🔧 תחזוקה שבועית — מוצ"ש 22:00

**בכל heartbeat מוצ"ש אחרי 22:00:**
```bash
python3 /home/jonia/.openclaw/workspace-eti/scripts/maintenance.py
```

- cleanup של log files ישנים (>30 ימים)
- ארכוב מדידות ישנות
- בדיקת integrity של monitoring data
- עדכון baseline metrics לשבוע הבא

---

## 📡 Alert Channels

### לדבורה (בעדיפות)
1. **קריטי:** כתיבה ל-`/home/jonia/.openclaw/workspace/state/eti_alerts.md`
2. **חירום:** הודעת WhatsApp ישירה ליוני אם מערכת קריטית down

### לוגים פנימיים
- **Performance logs:** `workspace-eti/logs/performance/YYYY-MM-DD.log`
- **Error logs:** `workspace-eti/logs/errors/YYYY-MM-DD.log`
- **Trends:** `workspace-eti/data/trends/YYYY-MM-DD.json`

## 🎚️ Alert Thresholds

| מטריקה | רגיל | אזהרה | קריטי |
|---------|------|--------|--------|
| Script runtime | <30s | 30-60s | >60s |
| Error rate | <5% | 5-15% | >15% |
| API latency | <2s | 2-5s | >5s |
| Memory growth | <10%/day | 10-25%/day | >25%/day |
| Disk usage | <80% | 80-90% | >90% |

## 💤 Quiet Hours
- בין 22:00-06:00 → רק אלרטים קריטיים
- שישי בערב - מוצ"ש → מצב שבת (פחות התרעות)

---

## 🚀 Phase 1 Scripts לפיתוח

1. **performance_monitor.py** — מדידת ביצועים
2. **error_scanner.py** — זיהוי שגיאות  
3. **trend_analyzer.py** — ניתוח מגמות
4. **system_health.py** — בריאות מערכת
5. **automation_opportunities.py** — זיהוי הזדמנויות
6. **maintenance.py** — תחזוקה שבועית

**בנייה הדרגתית:** script אחד בשבוע, testing לפני production