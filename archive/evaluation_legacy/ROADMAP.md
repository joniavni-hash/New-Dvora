# מפת דרכים — Dvorah Evaluation Roadmap
<!-- Status: Canonical -->
<!-- Purpose: Implementation timeline -->
<!-- Authority: Source of truth for rollout plan -->

## עקרון מנחה

להתחיל מדברים שאפשר לעשות **עכשיו**, עם כלים שכבר קיימים. לא לחכות ל-infrastructure מושלם.

---

## שבוע 1 — MVP (בר-ביצוע מיידי)

### מה עושים

1. **Trace logging**
   - להפעיל JSON logging לפי `TRACE_SCHEMA.md`
   - כל interaction מייצר trace record ב-`traces/YYYY-MM-DD.jsonl`
   - שדות minimum: trace_id, timestamp, session_id, channel, interpreted_intent, selected_response_strategy, tool_calls, execution_status, self_check

2. **Self-check activation**
   - להפעיל את ה-self-check flags מ-`SELF_CHECK_POLICY.md`
   - בינארי, אחרי כל response
   - flags: action_taken, open_loop_created, search_exhausted, memory_written, followed_policy, confidence_level

3. **5 תרחישי benchmark קריטיים — ידני**
   - BM-001: Premature Surrender (credentials search)
   - BM-002: Response Strategy (execute vs clarify)
   - BM-005: Tool Decision (unnecessary tool call)
   - BM-010: Loop Closure (open loop tracking)
   - BM-015: Multi-turn (context retention)
   - להריץ כל אחד, לבדוק trace, לסמן pass/fail ידנית

4. **metrics.py — גרסה ראשונה**
   - סקריפט שקורא JSONL traces ומחשב:
     - task_completion_rate (מ-execution_status)
     - premature_surrender_rate (מ-execution_status + search_exhaustion)
     - tool call count statistics
     - loop_closure_rate (מ-self_check flags)
   - Output: JSON summary

### מגבלות כנות

- ⚠️ **Ground truth**: בלי human labels, המטריקות הן proxy בלבד. task_completion_rate מודד מה דבורה *דיווחה* שהושלם, לא מה *באמת* הושלם.
- ⚠️ **Self-check = self-report**: דבורה מעריכה את עצמה. זה טוב בתור signal, לא בתור truth.
- ⚠️ **5 benchmarks ≠ coverage**: זה דגימה. לא הערכה מקיפה. מטרה: להוכיח שה-pipeline עובד.

---

## שבוע 2 — Benchmark מלא + אוטומציה בסיסית

### מה עושים

1. **כל 20 תרחישי benchmark**
   - להריץ BM-001 עד BM-020 מ-`BENCHMARK_SCENARIOS.md`
   - לתעד תוצאות ב-`traces/benchmark_results_YYYY-MM-DD.json`

2. **metrics.py — אוטומטי**
   - הרצה שבועית (cron או ידני ביום ראשון)
   - כל המטריקות מ-`METRICS.md` שסומנו ✅ (ניתן למדידה עכשיו)
   - Output שבועי ב-`traces/weekly_metrics_YYYY-WNN.json`

3. **Baseline measurement**
   - מדידת baseline של כל metric
   - זה ה-"נקודת אפס" להשוואות עתידיות
   - ⚠️ Baseline ממדגם קטן = לא מייצג. לציין את n לכל metric.

4. **מיפוי: auto-scorable vs human-required**
   
   | ניתן ל-auto-score | דורש human annotation |
   |---|---|
   | task_completion_rate (proxy) | response_strategy_accuracy (true) |
   | premature_surrender_rate (proxy) | false_completion_rate |
   | tool_precision (partial) | tool_recall |
   | loop_closure_rate | memory_precision, memory_recall |
   | unnecessary_tool_rate | context_understanding_accuracy |

---

## שבוע 3 — Evaluator + Failure Detection

### מה עושים

1. **Post-hoc evaluator script**
   - סקריפט שקורא traces ומריץ ניתוח:
     - Pattern matching על failure modes (FM-001 עד FM-018)
     - Consistency checks (intent → strategy → action)
     - Anomaly detection (latency spikes, tool call bursts)
   - ⚠️ **Blind spot מובנה**: evaluator שמשתמש באותו מודל לא יזהה blind spots של המודל. הוא יחמיץ את מה שדבורה מחמיצה.

2. **Failure mode detection rules**
   - Rule per FM:
     - FM-001: `execution_status=failed AND search_exhaustion IN [single_source, partial]`
     - FM-002: `conversation_state=correction` ב-interaction הבא
     - FM-010: `self_check.open_loop_created=true` בלי `loop_closed=true` ב-48 שעות
   - לא כל FM ניתן לזיהוי אוטומטי. לסמן אילו כן ואילו דורשים human review.

3. **Stress test suite**
   - בנק של 20 תרחישי stress (ראו `OPERATIONAL_TEST_PLAN.md` שכבה B)
   - Rotation: 5-10 תרחישים כל שבוע
   - ⚠️ יצירת תרחישי stress ע"י אותו מודל = circular. עדיף שיוני יכתוב חלק מהם ידנית.

---

## שבוע 4 — Dashboard + Regression + תהליך חודשי

### מה עושים

1. **Dashboard integration**
   - Endpoint `/api/eval-metrics` ב-Vercel dashboard
   - metrics.py דוחף JSON אחרי כל aggregation
   - פאנלים לפי `DASHBOARD_SPEC.md`
   - ⚠️ MVP ויזואלי: טבלה + color coding. גרפים = שלב מאוחר יותר.

2. **Pass/fail automation**
   - metrics.py מחשב pass/fail אוטומטי לפי `PASS_FAIL_POLICY.md`
   - Gating metrics נבדקים אוטומטית
   - Warning metrics מדווחים אבל לא חוסמים

3. **Regression comparison ראשון**
   - שבוע 4 vs שבוע 2 baseline
   - דוח regression: metrics שירדו, failure modes חדשים, trends
   - ⚠️ שתי נקודות = לא trend. צריך ≥4 שבועות ל-trend אמיתי.

4. **תהליך סקירה חודשי**
   - יוני סוקר 10-15 interactions מלאים
   - Ground truth labeling על מדגם
   - Calibration: האם ה-proxy metrics תואמים את ה-human judgment?
   - עדכון failure modes catalog אם נמצאים patterns חדשים

---

## מה ריאלי עכשיו vs אחר כך

### עכשיו (שבועות 1-2)
- ✅ Trace logging — כלי הקלטה בסיסי
- ✅ Self-check flags — binary, פשוט, actionable
- ✅ Manual benchmarks — 5 ואז 20 תרחישים
- ✅ Basic metrics — proxy-based, מ-trace data
- ✅ metrics.py — aggregation script

### אחר כך (שבועות 3-4)
- 🔧 Automated scoring — חלקי, לא מלא
- 🔧 Dashboard integration — Vercel push
- 🔧 Regression automation — comparison script
- 🔧 Failure mode detection — rule-based, partial

### אספירציוני (חודש+)
- ⚠️ Real-time evaluation — דורש infrastructure שלא קיים
- ⚠️ Multi-model evaluator — להשתמש במודל אחר להעריך את דבורה. יקר, אבל מסיר self-eval bias
- ⚠️ Confidence calibration — "כמה דבורה בטוחה" vs "כמה היא צודקת". דורש הרבה labeled data.
- ⚠️ Automated scenario generation — מודל שמייצר test cases. Circular risk.
- ⚠️ A/B testing — השוואת policy versions. דורש traffic splitting.

---

## סקציית כנות קריטית

### מה אנחנו לא יודעים

1. **Self-evaluation is not evaluation.** דבורה מעריכה את עצמה בכל שכבות ה-framework. Self-check, trace logging, metrics — הכל עובר דרך אותו מודל. זה טוב בתור monitoring, לא בתור ground truth.

2. **Proxy ≠ Truth.** `task_completion_rate` מודד מה דבורה דיווחה. `false_completion_rate` דורש אדם שיאמר "לא, זה לא באמת הושלם". בלי human labels, אנחנו מודדים self-consistency, לא correctness.

3. **מטריקות אספירציוניות.** כמה מטריקות מ-`METRICS.md` נשמעות טוב אבל לא ניתנות למדידה אמיתית עכשיו:
   - ⚠️ `context_understanding_accuracy` — דורש human judgment על כל interaction
   - ⚠️ `conversation_state_detection_accuracy` — same
   - ⚠️ `response_strategy_accuracy` (true) — same
   - ⚠️ `memory_recall` — דורש human שיגיד מה *היה צריך* להישמר

4. **20 benchmarks ≠ comprehensive.** מרחב הכשלים האפשריים הוא אינסופי. Benchmarks מכסים known patterns. Unknown unknowns נתפסים רק ע"י live monitoring + human review.

5. **Small n problem.** בשבועות הראשונים יהיו מעט interactions. מטריקות מ-n=50 לא אמינות סטטיסטית. צריך ≥200 interactions ל-confidence סבירה על gating metrics.

### מה כן עובד

- **Observable behaviors**: tool calls, file writes, message sends — אלה אובייקטיביים.
- **Self-check as signal**: לא truth, אבל signal שימושי. אם דבורה מדווחת `search_exhausted=false`, זה indicator חזק.
- **Regression detection**: גם עם proxy metrics, ירידה שבועית = warning signal אמיתי.
- **Failure mode catalog**: FM-001 עד FM-018 מבוססים על כשלים אמיתיים. זיהוי שלהם = ערך ממשי.

### העיקרון

להתחיל ממה שניתן למדוד אובייקטיבית. לבנות human labeling בהדרגה. לא להתיימר שאנחנו מודדים מה שאנחנו לא באמת מודדים.
