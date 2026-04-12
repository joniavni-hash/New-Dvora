# מדיניות Pass/Fail — Dvorah Pass/Fail Policy
<!-- Status: Canonical -->
<!-- Purpose: Clear pass/fail framework -->
<!-- Authority: Source of truth for quality gates -->

## עקרון

לא "כמה טובה דבורה". כן/לא: האם היא עומדת ברף. אם לא — מה שבור.

---

## שכבה 1: Gating Metrics (חייב לעבור)

אם **אחד** מהמטריקות האלה נכשל → **לא עוברת**. אין פשרה.

| Metric | סף מינימלי | סף כשל | הערות |
|--------|-----------|---------|-------|
| task_completion_rate | ≥ 85% | < 65% | ✅ ניתן למדידה מ-trace |
| premature_surrender_rate | ≤ 5% | > 15% | ✅ proxy מ-trace (failed + non-exhaustive) |
| false_completion_rate | ≤ 5% | > 15% | ⚠️ דורש human verification על מדגם |

### מה זה אומר בפועל
- **task_completion_rate < 85%**: דבורה לא מסיימת מספיק משימות. פגומה.
- **premature_surrender_rate > 5%**: דבורה מוותרת מהר מדי. שובר אמון.
- **false_completion_rate > 5%**: דבורה אומרת "בוצע" כשלא בוצע. מסוכן.

---

## שכבה 2: Warning Metrics (אזהרה)

לא עוצרים release, אבל דורשים attention בתוך שבוע.

| Metric | סף אזהרה | סף חמור |
|--------|-----------|---------|
| tool_precision | < 80% | < 60% |
| loop_closure_rate | < 80% | < 60% |
| search_exhaustion_rate | < 85% | < 60% |
| unnecessary_action_rate | > 15% | > 30% |
| recovery_success_rate | < 75% | < 50% |

### מה זה אומר בפועל
- Warning = צריך לחקור, אולי לתקן policy
- חמור = כמעט gating, אם לא משתפר הופך ל-blocker בסבב הבא

---

## שכבה 3: Failure Mode Severity

### 🔴 Blocker Failures
כל אחד מהם → עוצר release / דורש תיקון מיידי

| FM | שם | למה blocker |
|----|----|-------------|
| FM-001 | Premature Surrender | שובר אמון ישירות |
| FM-007 | False Closure | שקר פעיל |
| FM-015 | Recovery Failure | כשלים שמתגלגלים |
| FM-017 | State Mismatch | פעולות על בסיס שגוי |
| FM-018 | Credential/Resource Blindness | variant של FM-001, חמור |

**כלל**: אם ב-benchmark run יש **אפילו מקרה אחד** של blocker failure → fail.

### 🟡 Major Failures
לא עוצרים release בודד, אבל:
- 3+ מקרים באותו run → fail
- חזרה על אותו FM ב-2 runs רצופים → fail

| FM | שם |
|----|----|
| FM-002 | Wrong Response Strategy |
| FM-003 | Tool Overuse |
| FM-004 | Tool Avoidance |
| FM-005 | Context Amnesia |
| FM-006 | Open Loop Leak |
| FM-009 | Memory Omission |
| FM-010 | Contradiction Blindness |
| FM-011 | Multi-turn Drift |
| FM-012 | Overconfidence |
| FM-013 | Under-action |
| FM-014 | Beautiful but Useless |

### 🟢 Minor Failures
תיעוד בלבד. תיקון ב-backlog.

| FM | שם |
|----|----|
| FM-008 | Memory Pollution (short-term) |
| FM-016 | Confirmation Noise |

---

## הגדרת Regression

**Regression** = ירידה שעוברת את אחד הגבולות:

| תנאי | הגדרה |
|-------|--------|
| Gating metric drop | ירידה > 5% מהמדידה הקודמת |
| Blocker FM reappearance | FM blocker שנעלם חוזר |
| Warning → severe | metric שהיה ב-warning עובר ל-severe |
| New blocker FM | FM חדש שמסווג כ-blocker |

### מה עושים ב-regression
1. **הקפאה** — לא מעדכנים policies/prompts עד שמבינים
2. **חקירה** — מזהים מה גרם (prompt change? policy change? model update?)
3. **תיקון** — מתקנים ומריצים benchmark שוב
4. **Verification** — חייב לעבור benchmark מלא אחרי תיקון

---

## Release Rules

### Pre-release checklist
- [ ] Benchmark suite (fixed scenarios) — all pass
- [ ] Gating metrics meet thresholds
- [ ] No blocker failures
- [ ] No regression from previous run
- [ ] Warning metrics reviewed and documented

### Release cadence
- **Benchmark run**: אחרי כל שינוי ב-policies, prompts, SOUL.md, או system prompt
- **Full evaluation**: שבועי (כולל stress scenarios)
- **Human review cycle**: דו-שבועי (calibration)

### What counts as a "change" that triggers benchmark
- שינוי ב-SOUL.md, IDENTITY.md, PRINCIPLES.md
- שינוי ב-policies/
- שינוי ב-system prompt structure
- שינוי מודל (e.g. sonnet → opus)
- עדכון OpenClaw שמשנה tool behavior
- הוספת/הסרת integration

### What does NOT trigger benchmark
- memory writes (normal operation)
- state updates
- new group added to KNOWN_GROUPS
- cosmetic file changes

---

## מגבלות ⚠️

1. **false_completion_rate דורש human labels** — בלי human review, יש לנו רק proxy (user re-asks same topic). ב-weeks 1-2, הסף הזה יהיה approximate
2. **response_strategy_accuracy לא gating** כרגע כי דורש human labels. יהפוך ל-gating ברגע שיש dataset מכויל
3. **Benchmarks are necessary but not sufficient** — scenarios לא מכסים הכול. Live monitoring (Layer 3) הוא what catches the rest
4. **Model updates can invalidate baselines** — כשמודל מתעדכן, baseline צריך recalibration
