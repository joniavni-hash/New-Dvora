# תוכנית בדיקות תפעולית — Dvorah Operational Test Plan
<!-- Status: Canonical -->
<!-- Purpose: Three-layer testing strategy -->
<!-- Authority: Source of truth for test execution -->

## עקרון

שלוש שכבות בדיקה, כל אחת ברזולוציה אחרת. ביחד הן מכסות: שינויים מכוונים (benchmark), מקרי קצה (stress), וביצוע יומיומי (live).

---

## שכבה A — Benchmark (תרחישים קבועים)

### מתי מריצים
- **אחרי כל שינוי מהותי**: policy חדש, שינוי ב-SOUL.md, שדרוג מודל, שינוי architecture
- **אחרי כל שינוי ב-evaluation framework עצמו** (כדי לוודא שהמדידה לא נשברה)
- **לפי דרישה**: כשיוני מבקש validation

### מה מריצים
- כל 20 התרחישים מ-`BENCHMARK_SCENARIOS.md` (BM-001 עד BM-020)
- כל תרחיש מורץ כ-interaction מלא עם trace logging פעיל

### איך מריצים
**שלב נוכחי — ידני:**
1. מריצים כל תרחיש כ-prompt לדבורה דרך WhatsApp או CLI
2. מוודאים ש-trace נוצר ב-`traces/YYYY-MM-DD.jsonl`
3. בודק אנושי סוקר כל trace מול expected behaviors ו-success criteria
4. מסמנים pass/fail לפי `PASS_FAIL_POLICY.md`
5. תוצאות נרשמות ב-`traces/benchmark_results_YYYY-MM-DD.json`

**שלב עתידי — חצי-אוטומטי:**
- סקריפט `benchmark_runner.py` שמריץ תרחישים ברצף
- `benchmark_scorer.py` שמשווה trace output מול expected behaviors
- ⚠️ Scoring אוטומטי מוגבל: behavior matching ≠ string matching. חלק מהקריטריונים דורשים שיפוט אנושי

### Pass/Fail
- **Pass**: כל gating metrics (שכבה 1 ב-PASS_FAIL_POLICY) עוברים סף
- **Warning**: metric אחד או יותר מ-שכבה 2 באזהרה
- **Fail**: gating metric אחד נכשל → חוסם deployment/שינוי

### זיהוי רגרסיה
- השוואת תוצאות בין run נוכחי ל-run הקודם
- כל metric שירד ≥5% → flag
- כל תרחיש שעבר fail אחרי שעבר pass → regression alert
- תוצאות נשמרות היסטורית לאפשר trend analysis

### מי סוקר
- **עכשיו**: יוני (human review)
- **עתיד**: סקריפט אוטומטי + human review על failures בלבד

---

## שכבה B — Stress & Edge Cases (מקרי קצה)

### מתי מריצים
- **שבועי**: ימי ראשון, באותו slot של הרצת metrics.py
- **ad-hoc**: כשמזהים failure mode חדש

### מה מריצים
תרחישים קשים שלא ב-benchmark הרגיל:

| קטגוריה | דוגמאות | Failure Modes רלוונטיים |
|----------|---------|------------------------|
| הוראות סותרות | "תשלחי מייל ליוסי — לא, חכי, אל תשלחי — בעצם כן" | FM-002, FM-007 |
| שינוי נושא באמצע | "מה מזג האוויר? אגב, מה עם הפגישה של מחר?" | FM-008, FM-009 |
| כשל כלים | tool שלא מגיב, timeout, credentials פגומים | FM-001, FM-006 |
| credentials חסרים | בקשה שדורשת integration לא מוגדר | FM-001, FM-018 |
| בקשות עמומות | "תטפלי בזה", "תעשי מה שצריך" | FM-002, FM-007 |
| שיחות ארוכות multi-turn | 10+ הודעות עם context shifting | FM-008, FM-009, FM-010 |
| עומס מקבילי | מספר בקשות בו-זמנית | FM-012 |
| מידע סותר ב-memory | שני קבצי memory עם עובדות סותרות | FM-011 |

### איך מריצים
**שלב נוכחי:**
1. בנק תרחישי stress (נבנה ידנית, מתעדכן כל שבוע)
2. מריצים 5-10 תרחישים כל שבוע (rotation)
3. trace logging פעיל
4. human review ממוקד ב-failure modes ספציפיים

**שלב עתידי:**
- סקריפט שמייצר תרחישי edge case רנדומליים מתבניות
- ⚠️ תרחישים שנוצרים אוטומטית ע"י אותו מודל → blind spots מובנים

### זיהוי רגרסיה
- השוואת תוצאות שבועיות: אותם תרחישים שרצים מחדש
- מעקב אחרי failure modes חוזרים (FM שמופיע ≥3 שבועות ברצף → escalation)
- דגש על failure modes FM-001 עד FM-018 מ-`FAILURE_MODES.md`

### מי סוקר
- **עכשיו**: יוני (human review), עם דגש על תרחישים שנכשלו
- **עתיד**: automated failure mode detection + human review על unknowns

---

## שכבה C — Live Monitoring (ניטור רציף)

### מתי רץ
- **תמיד**. כל interaction אמיתי מייצר trace.

### מה נאסף
- כל interaction מייצר trace record לפי `TRACE_SCHEMA.md`
- Self-check רץ אחרי כל response לפי `SELF_CHECK_POLICY.md`
- Traces נשמרים ב-`traces/YYYY-MM-DD.jsonl`

### אגרגציה
- **שבועית**: metrics.py מעבד את כל ה-traces ומחשב metrics
- **output**: `traces/weekly_metrics_YYYY-WNN.json`
- מטריקות מחושבות לפי הגדרות ב-`METRICS.md`

### התראות אוטומטיות

| Metric | סף התראה | חומרה |
|--------|----------|-------|
| premature_surrender_rate | > 5% | 🔴 Blocker |
| false_completion_rate | > 5% | 🔴 Blocker |
| loop_closure_rate | < 80% | 🟡 Warning |
| tool_precision | < 80% | 🟡 Warning |
| response_strategy_accuracy | < 75% | 🟡 Warning |

- התראה = הודעה ליוני + flag ב-dashboard
- ⚠️ חלק מההתראות דורשות human verification (false_completion בפרט)

### סקירה אנושית
- **שבועית**: יוני סוקר metrics summary
- **חודשית**: יוני סוקר מדגם של 10-15 interactions מלאים
  - דגש על: interactions עם self-check flags, failures, edge cases
  - מטרה: calibration של metrics ו-ground truth labeling

### זיהוי רגרסיה
- השוואה שבוע-על-שבוע של כל metric
- trend analysis: 3 שבועות רצופים של ירידה → alert
- חודש-על-חודש: דוח trend מלא

### מי סוקר
- **אוטומטי**: metrics script, self-check flags
- **אנושי**: יוני — שבועי (summary), חודשי (deep review)

---

## סיכום שכבות

| | שכבה A — Benchmark | שכבה B — Stress | שכבה C — Live |
|---|---|---|---|
| **תדירות** | per-change | שבועי (ראשון) | רציף |
| **תרחישים** | 20 קבועים | 5-10 rotating | כל interaction |
| **אוטומטי** | trace logging, עתיד: scoring | trace logging | trace + self-check + metrics |
| **ידני** | scoring, pass/fail | review של failures | שבועי summary, חודשי deep review |
| **רגרסיה** | run-vs-run | שבוע-vs-שבוע | trend analysis |
| **סוקר** | יוני + עתיד: סקריפט | יוני | metrics script + יוני |

---

## מגבלות ידועות

- ⚠️ **Self-evaluation bias**: דבורה מעריכה את עצמה. זה לא אובייקטיבי. שכבה C תלויה ב-self-check שדבורה מפעילה על עצמה.
- ⚠️ **Ground truth gap**: חלק מהמטריקות (response_strategy_accuracy, context_understanding) דורשות human labels שאין עדיין.
- ⚠️ **Non-determinism**: אותו תרחיש benchmark יכול לייצר תוצאות שונות. צריך multiple runs לסטטיסטיקה אמינה.
- ⚠️ **Coverage**: 20 benchmarks + ~10 stress cases לא מכסים את כל מרחב הכשלים האפשריים. Live monitoring הוא רשת הביטחון.
