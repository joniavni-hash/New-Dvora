# ארכיטקטורת הערכה — Dvorah Evaluation Architecture
<!-- Status: Canonical -->
<!-- Purpose: Overall evaluation system design -->
<!-- Authority: Source of truth for evaluation layers -->

## מבוא כנה

מערכת הערכה ל-LLM agent היא לא כמו test suite רגיל. שלושה דברים צריך להבין לפני שמתחילים:

1. **Non-determinism**: אותו input יכול לתת output שונה. אין "expected output" מדויק — יש התנהגות צפויה.
2. **Self-evaluation blind spots**: כש-Claude מעריך את Claude, יש inherent bias. השכבה הפנימית חייבת להיות objective/binary, לא subjective.
3. **Ground truth dependency**: רוב המטריקות דורשות human labels כדי לכייל. בלי זה, יש לנו proxy metrics בלבד.

---

## שלוש שכבות הערכה

```
┌─────────────────────────────────────────────────┐
│              Layer 3: Human Review               │
│         (periodic, calibration, ground truth)    │
├─────────────────────────────────────────────────┤
│           Layer 2: Evaluator (External)          │
│      (automated, post-hoc, objective criteria)   │
├─────────────────────────────────────────────────┤
│           Layer 1: Self-Check (Internal)         │
│       (real-time, binary flags, per-response)    │
├─────────────────────────────────────────────────┤
│                  Trace Layer                      │
│          (structured log of every interaction)   │
└─────────────────────────────────────────────────┘
```

---

## שכבה 1: Self-Check (בדיקה עצמית)

### מה זה
בדיקה פנימית שדבורה מבצעת **אחרי כל תשובה**. לא ציון סובייקטיבי — רק flags בינאריים.

### מה היא יכולה לתפוס
- לולאות פתוחות שנוצרו ולא נסגרו
- כלים שתוכננו אבל לא הופעלו
- מידע חסר שלא נדרש
- סתירות שלא טופלו
- כתיבה לזיכרון מיותרת או חסרה
- חיפוש חלקי (מקור יחיד במקום כמה)

### מה היא **לא יכולה** לתפוס
- ⚠️ אסטרטגיית תגובה שגויה (היא לא יודעת מה ה-"נכון")
- ⚠️ false closure (היא חושבת שסיימה, אז הבדיקה העצמית גם תחשוב שסיימה)
- ⚠️ context amnesia (אם שכחה משהו, היא לא יודעת ששכחה)
- ⚠️ beautiful-but-useless response (היא חושבת שהתשובה טובה)

### יתרונות
- Real-time, אפס latency נוסף
- מייצרת structured trace data
- אפשר להפעיל מיום ראשון

### חסרונות
- Same model, same blind spots
- לא יכולה לתפוס שגיאות שמקורן בשיפוט שגוי
- מוגבלת ל-observable facts על הפעולות שבוצעו

### מימוש
ראי `SELF_CHECK_POLICY.md`

---

## שכבה 2: Evaluator (הערכה חיצונית/אוטומטית)

### מה זה
תהליך שרץ **post-hoc** על traces שנאספו. יכול להיות:
- Script שבודק trace fields כנגד כללים
- מודל אחר (או אותו מודל עם prompt שונה) שמעריך interactions
- Rule-based checks על patterns ידועים

### מה הוא יכול לתפוס
- Tool overuse/avoidance (על בסיס patterns סטטיסטיים)
- Premature surrender (search_exhaustion=single_source + execution_status=failed)
- Open loop leaks (open_loops_after > open_loops_before בלי סיבה)
- False closure (completion_status=task_complete + followup שלא בוצע)
- Memory pollution patterns (memory writes תכופים מדי)
- Contradiction blindness (כשיש contradiction_flags=false אבל human reviewer מצא סתירה)

### מה הוא **לא יכול** לתפוס (בלי ground truth)
- ⚠️ response_strategy_accuracy — דורש human label על "מה היה הנכון"
- ⚠️ tool_recall — דורש human label על "מה היה צריך להפעיל"
- ⚠️ memory_recall — דורש human label על "מה היה צריך לשמור"
- ⚠️ multi_turn_consistency — דורש human judgment על "האם ההקשר נשמר"

### יתרונות
- יכול לעבור על כמויות גדולות של traces
- Object criteria שלא משתנים בין הרצות
- יכול לזהות patterns שהשכבה הפנימית מפספסת

### חסרונות
- Post-hoc — לא עוצר שגיאות בזמן אמת
- Rule-based checks תופסים רק מה שחשבנו עליו מראש
- LLM-based evaluation עדיין LLM — עם bias משלו
- דורש תשתית (storage, scripts, scheduling)

### מימוש
- Benchmark scenarios → ראי `BENCHMARK_SCENARIOS.md`
- Failure mode detection → ראי `FAILURE_MODES.md`
- Metrics computation → ראי `METRICS.md`

---

## שכבה 3: Human Review (סקירה אנושית)

### מה זה
יוני (או מי שהוא מגדיר) עובר על מדגם של interactions ומסמן:
- האם ההחלטה הייתה נכונה
- האם התוצאה הייתה טובה
- האם היה failure mode שלא נתפס

### מה היא יכולה לתפוס
- **הכול**. זה ה-ground truth.
- בפרט: beautiful-but-useless, wrong strategy, context amnesia, state mismatch

### מה היא **לא יכולה** לתפוס
- Scale — אי אפשר לסקור כל interaction
- Latency — הביקורת מגיעה זמן אחרי האירוע
- Consistency — human judgment משתנה לפי מצב רוח ועייפות

### יתרונות
- Ground truth אמיתי
- תופס מה שאוטומציה מפספסת
- מכייל את שתי השכבות האחרות

### חסרונות
- לא scalable
- דורש זמן ומוטיבציה של יוני
- צריך כלי labeling נוח (אחרת לא יקרה)

### מימוש
- Sampling strategy: 10-20 interactions בשבוע, biased toward flagged interactions
- Labeling interface: minimal — Google Sheet או form פשוט
- Output: labeled dataset שמזין calibration ל-Layer 2

---

## איך השכבות מתקשרות

```
Interaction happens
    │
    ├─→ Layer 1: Self-Check flags emitted (real-time)
    │       │
    │       ├─→ Written to trace
    │       └─→ If critical flag → alert
    │
    ├─→ Trace stored
    │
    ├─→ Layer 2: Evaluator runs (batch/scheduled)
    │       │
    │       ├─→ Computes metrics from traces
    │       ├─→ Detects failure mode patterns
    │       ├─→ Compares against pass/fail thresholds
    │       └─→ Generates report
    │
    └─→ Layer 3: Human Review (weekly/biweekly)
            │
            ├─→ Reviews sampled interactions
            ├─→ Labels ground truth
            ├─→ Calibrates Layer 2 thresholds
            └─→ Updates failure mode catalog if needed
```

---

## מגבלות כלליות של כל המערכת

### מה אנחנו יכולים למדוד באמת (עכשיו)
- Self-check flags (binary, objective)
- Trace field completeness
- Tool usage patterns (count, timing)
- Open loop tracking (before/after)
- Latency
- Benchmark scenario pass/fail

### מה דורש human labels כדי להיות אמיתי ⚠️
- Response strategy accuracy
- Tool precision/recall (מה באמת היה "נחוץ")
- Memory precision/recall
- Multi-turn consistency
- Contradiction detection rate
- Missing info detection rate

### מה שנשמע טוב אבל קשה מאוד למדוד ⚠️
- "User satisfaction" — יוני לא ימלא סקר אחרי כל הודעה
- "Task quality" — מה זה "איכות" של סיכום קבוצה?
- "Proactive value" — האם המערכת הוסיפה ערך שלא התבקש?

---

## עקרונות עיצוב

1. **Observable over subjective**: כל metric חייב להתבסס על trace fields שניתנים למדידה
2. **Binary over continuous**: Self-check flags הם true/false, לא 1-10
3. **Honest about gaps**: אם metric דורש ground truth שאין לנו, מסמנים ⚠️
4. **Incremental value**: כל שכבה מוסיפה ערך גם בלי האחרות
5. **Low friction for humans**: ה-Human Review layer חייב להיות קל לשימוש, אחרת הוא ימות
