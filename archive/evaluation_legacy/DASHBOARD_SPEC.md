# מפרט Dashboard — Dvorah Evaluation Dashboard Spec
<!-- Status: Canonical -->
<!-- Purpose: Dashboard structure and integration -->
<!-- Authority: Source of truth for dashboard design -->

## עקרון

Dashboard אחד שמראה את מצב דבורה. לא יפה — שימושי. הדגש: לזהות בעיות מהר, לא להציג מספרים.

---

## מקור נתונים

- **Input**: trace logs (JSONL) מ-`traces/YYYY-MM-DD.jsonl`
- **Processing**: metrics.py aggregation — שבועי
- **Output**: `traces/weekly_metrics_YYYY-WNN.json`
- **Format**: JSON object עם כל ה-metrics + metadata

---

## פאנלים

### 1. בריאות מערכת — System Health

**מטריקות**: gating metrics מ-`PASS_FAIL_POLICY.md` שכבה 1

| Metric | סף ירוק | סף צהוב | סף אדום |
|--------|---------|---------|---------|
| task_completion_rate | ≥ 85% | 65-85% | < 65% |
| premature_surrender_rate | ≤ 5% | 5-15% | > 15% |
| false_completion_rate | ≤ 5% | 5-15% | > 15% |

**תצוגה**: שלושה gauges עם color coding. ירוק/צהוב/אדום. ערך נוכחי + trend arrow (↑↓→).

**עדיפות**: 🔴 זה הפאנל הכי חשוב. אם כאן אדום — כל השאר לא רלוונטי.

### 2. שימוש בכלים — Tool Usage

**מטריקות**: tool_precision, tool_recall, unnecessary_tool_rate

**תצוגה**: bar chart — ערכים שבועיים ב-4 שבועות אחרונים.

| Metric | מה מודד | סף |
|--------|---------|-----|
| tool_precision | כלי שנקרא היה נחוץ? | ≥ 85% |
| tool_recall | כלי שהיה נחוץ נקרא? | ≥ 80% ⚠️ |
| unnecessary_tool_rate | קריאות מיותרות | ≤ 10% |

⚠️ tool_recall דורש human labeling — proxy בלבד עד שיש ground truth.

### 3. ניהול לולאות — Loop Management

**מטריקות**: loop_closure_rate, open_loops_count

**תצוגה**:
- loop_closure_rate: line chart שבועי
- open_loops_count: counter נוכחי + trend

**סף**: loop_closure_rate ≥ 80%. מתחת → צהוב. מתחת ל-60% → אדום.

### 4. איכות זיכרון — Memory Quality

**מטריקות**: memory_precision, memory_recall

**תצוגה**: dual bar chart

| Metric | מה מודד | סף |
|--------|---------|-----|
| memory_precision | מה שנכתב היה רלוונטי? | ≥ 85% ⚠️ |
| memory_recall | מה שהיה צריך להיכתב נכתב? | ≥ 70% ⚠️ |

⚠️ שני המטריקות דורשים human review. ב-dashboard יוצגו רק אחרי calibration.

### 5. כשלים — Failure Modes

**מקור**: trace analysis → failure mode classification

**תצוגה**:
- Top 5 failure modes חוזרים — bar chart (frequency)
- Trend: האם FM ספציפי עולה או יורד
- Color: FM עם severity=Blocker באדום

**דוגמה**:
```
FM-001 (Premature Surrender)  ████████ 12
FM-002 (Wrong Strategy)       ██████ 9
FM-007 (Missing Clarify)      ████ 6
FM-010 (Loop Not Closed)      ███ 4
FM-013 (Under-action)         ██ 3
```

### 6. אסטרטגיית תגובה — Response Strategy

**מטריקות**: response_strategy_accuracy, strategy distribution

**תצוגה**:
- Pie chart: חלוקת strategies (execute, clarify, inform, defer, refuse)
- Line chart: accuracy over time

⚠️ Accuracy = proxy בלבד (intent-strategy consistency). True accuracy דורשת human labels.

### 7. מיצוי חיפוש — Search Exhaustion

**מטריקות**: premature_surrender_rate, search_exhaustion distribution

**תצוגה**:
- Line chart: premature_surrender_rate trend (שבועי)
- Stacked bar: search_exhaustion levels (exhaustive / partial / single_source)

**סף**: premature_surrender_rate ≤ 5%. מעל → alert.

### 8. התראת רגרסיה — Regression Alert

**לוגיקה**: כל metric שירד >5% מהתקופה הקודמת

**תצוגה**:
- רשימה של metrics שירדו
- כל שורה: metric name, ערך קודם, ערך נוכחי, % שינוי
- צבע אדום
- אם אין רגרסיות → פאנל ירוק עם "✓ No regressions"

**דוגמה**:
```
🔴 task_completion_rate: 89% → 82% (-7.9%)
🔴 loop_closure_rate: 85% → 78% (-8.2%)
```

---

## אינטגרציה

### Vercel Dashboard
- **URL**: `vercel-dashboard-two-ruby.vercel.app`
- **שיטה**: Push API — metrics.py דוחף JSON אחרי כל aggregation שבועי
- **Endpoint**: `/api/eval-metrics` (צריך ליצור)
- **Auth**: API key (לא לשמור ב-workspace files)
- **Payload**: weekly_metrics JSON object

### Local Fallback
- אם ה-dashboard לא זמין: metrics.py מדפיס summary ל-console
- קובץ `traces/latest_summary.md` מתעדכן כ-human-readable report

---

## תדירות עדכון

| רכיב | תדירות |
|-------|--------|
| Trace collection | רציף (כל interaction) |
| Self-check flags | רציף (real-time) |
| Metrics aggregation | שבועי (metrics.py) |
| Dashboard push | שבועי (אחרי aggregation) |
| Regression check | שבועי (אוטומטי) |
| Human review | חודשי |

---

## מגבלות

- ⚠️ Dashboard מציג מה שניתן למדוד. מטריקות שדורשות human labels יוצגו רק אחרי calibration ראשוני.
- ⚠️ Regression detection הוא שבועי. בעיה שמתחילה ביום שני תזוהה רק ביום ראשון.
- ⚠️ Self-check flags הם real-time אבל self-reported — לא objective.
- ⚠️ ב-MVP אין dashboard ויזואלי. יש JSON + summary file. ויזואליזציה בשלב מאוחר יותר.
