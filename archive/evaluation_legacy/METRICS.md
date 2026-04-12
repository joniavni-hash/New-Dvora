# מטריקות הערכה — Dvorah Evaluation Metrics
<!-- Status: Canonical -->
<!-- Purpose: Complete metric definitions -->
<!-- Authority: Source of truth for metrics -->

## מבוא כנה

לכל metric יש סימון:
- ✅ **ניתן למדידה עכשיו** — מבוסס על trace fields בלבד
- ⚠️ **דורש human labels** — צריך ground truth שעדיין אין לנו
- 🔮 **אספירציוני** — נשמע טוב, ימדד רק כשיהיה מספיק data

---

## 1. response_strategy_accuracy ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז ה-interactions שבהם האסטרטגיה שנבחרה תואמת את האסטרטגיה האידיאלית |
| **נוסחה** | `count(selected_response_strategy == ideal_strategy) / total_interactions` |
| **סף טוב** | ≥ 90% |
| **סף כשל** | < 75% |
| **שדות trace** | `selected_response_strategy`, `interpreted_intent` |
| **תדירות מדידה** | שבועית (דורש human labeling על מדגם) |
| **כנות** | ⚠️ `ideal_strategy` חייב להגיע מ-human review. בלי זה אפשר רק לבדוק consistency בין intent ל-strategy, לא correctness. **Proxy זמני**: בדיקה ש-`execute` intent → `execute` strategy, `clarify` intent → `clarify` strategy, וכו'. |

---

## 2. tool_precision ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | מתוך הכלים שהופעלו, כמה באמת היו נחוצים |
| **נוסחה** | `count(necessary_tools_used) / count(tools_used)` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 65% |
| **שדות trace** | `tools_used`, `tool_calls_count` |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ "necessary" דורש human label. **Proxy זמני**: אם `tool_used_unnecessarily=true` ב-self-check, סופרים את זה כ-unnecessary. זה under-estimates כי self-check יש לו blind spots. |

---

## 3. tool_recall ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | מתוך הכלים שהיה צריך להפעיל, כמה באמת הופעלו |
| **נוסחה** | `count(necessary_tools_used) / count(tools_that_should_have_been_used)` |
| **סף טוב** | ≥ 90% |
| **סף כשל** | < 70% |
| **שדות trace** | `tools_used`, `tool_candidates`, `tool_decision` |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ "tools that should have been used" דורש human label. **Proxy זמני**: `tool_decision=skipped` + `execution_status=failed` → probable missed tool. אבל זה תופס רק מקרים שנכשלו, לא מקרים שעבדו בלי הכלי הנכון. |

---

## 4. search_exhaustion_rate ✅

| Property | Value |
|----------|-------|
| **מה מודד** | כשנדרש חיפוש credentials/מידע, באיזה אחוז מהמקרים החיפוש היה מקיף |
| **נוסחה** | `count(search_exhaustion=exhaustive WHERE search_needed) / count(search_needed)` |
| **סף טוב** | ≥ 90% |
| **סף כשל** | < 60% |
| **שדות trace** | `search_exhaustion` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ ניתן למדידה — אבל ה-self-report על `search_exhaustion` עלול להיות אופטימי. Cross-validate עם `premature_surrender_rate`. |
| **איך מזהים "search_needed"** | `search_exhaustion != not_applicable` |

---

## 5. loop_closure_rate ✅ (partially)

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז הלולאות שנסגרו מתוך אלה שהיה צריך לסגור |
| **נוסחה** | `sum(open_loops_closed) / sum(open_loops_that_should_close)` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 65% |
| **שדות trace** | `open_loops_before`, `open_loops_after`, `open_loops_created`, `open_loops_closed` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ ניתן למדידה חלקית — הטרייס מתעד מה נסגר. אבל ⚠️ "should close" דורש judgment. **Proxy**: אם loop פתוח > 24 שעות בלי פעולה → probably should have closed. |

---

## 6. followup_accuracy ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז החלטות followup שהיו נכונות |
| **נוסחה** | `count(correct_followup_decisions) / count(total_followup_decisions)` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 65% |
| **שדות trace** | `followup_needed`, `followup_type` |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ "correct" דורש human label. **Proxy**: אם `followup_needed=true` ו-followup בוצע → assume correct (optimistic). אם `followup_needed=false` ויוני שאל שוב על אותו נושא → probably missed followup. |

---

## 7. memory_precision ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | מתוך מה שנכתב לזיכרון, כמה היה באמת נחוץ |
| **נוסחה** | `count(correct_memory_writes) / count(total_memory_writes)` |
| **סף טוב** | ≥ 90% |
| **סף כשל** | < 70% |
| **שדות trace** | `memory_write_decision`, `memory_write_reason` |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ דורש human review של memory writes. **Proxy**: `memory_written_unnecessarily=true` ב-self-check. Under-estimates. |

---

## 8. memory_recall ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | מתוך מה שהיה צריך לשמור בזיכרון, כמה באמת נשמר |
| **נוסחה** | `count(correct_memory_writes) / count(things_that_should_have_been_written)` |
| **סף טוב** | ≥ 80% |
| **סף כשל** | < 55% |
| **שדות trace** | `memory_write_decision`, `memory_not_written` (self-check) |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ "should have been written" דורש human label. **Proxy**: `memory_not_written=true` ב-self-check. Under-estimates — כי אם דבורה לא זיהתה שצריך לשמור, היא גם לא תסמן את ה-flag. |

---

## 9. task_completion_rate ✅

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז המשימות שהושלמו מתוך אלה שנוסו |
| **נוסחה** | `count(completion_status=task_complete) / count(completion_status IN [task_complete, task_open, task_progressed])` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 65% |
| **שדות trace** | `completion_status`, `execution_status` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ ניתן למדידה — אבל ⚠️ false completions ינפחו את המספר. חייבים למדוד `false_completion_rate` במקביל. |

---

## 10. false_completion_rate ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז המשימות שסומנו כ-complete אבל בפועל עדיין פתוחות |
| **נוסחה** | `count(marked_complete_but_actually_open) / count(completion_status=task_complete)` |
| **סף טוב** | ≤ 5% |
| **סף כשל** | > 15% |
| **שדות trace** | `completion_status`, human label |
| **תדירות מדידה** | שבועית |
| **כנות** | ⚠️ דורש human verification. **Proxy**: אם `completion_status=task_complete` ואחריו יוני שואל על אותו נושא שוב → probably false completion. דורש session correlation. |

---

## 11. unnecessary_action_rate ✅

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז הפעולות שלא היו נחוצות |
| **נוסחה** | `count(tool_used_unnecessarily=true) / count(action_taken=true)` |
| **סף טוב** | ≤ 10% |
| **סף כשל** | > 25% |
| **שדות trace** | self-check `tool_used_unnecessarily`, `action_taken` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ ניתן למדידה מ-self-check, אבל under-reports. |

---

## 12. unnecessary_tool_rate ✅

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז קריאות כלים מיותרות |
| **נוסחה** | `count(unnecessary_tool_calls) / count(total_tool_calls)` |
| **סף טוב** | ≤ 15% |
| **סף כשל** | > 30% |
| **שדות trace** | `tool_calls_count`, `tools_used`, self-check flags |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ Proxy: `tool_calls_count > len(tools_used)` → redundant calls. Also `tool_used_unnecessarily` self-check. |

---

## 13. contradiction_detection_rate ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז הסתירות שזוהו מתוך כלל הסתירות שהיו |
| **נוסחה** | `count(contradiction_flags.found=true) / count(actual_contradictions)` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 55% |
| **שדות trace** | `contradiction_flags` |
| **תדירות מדידה** | benchmark only (דורש scenarios עם סתירות מוכנות) |
| **כנות** | ⚠️ ב-live, אין דרך לדעת כמה סתירות "באמת היו" בלי human review. ניתן למדידה רק ב-benchmark scenarios שבהם הסתירה ידועה מראש. |

---

## 14. missing_info_detection_rate ⚠️

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז המקרים שבהם מידע חסר זוהה |
| **נוסחה** | `count(detected_missing_info.found=true) / count(actual_missing_info)` |
| **סף טוב** | ≥ 85% |
| **סף כשל** | < 55% |
| **שדות trace** | `detected_missing_info` |
| **תדירות מדידה** | benchmark only |
| **כנות** | ⚠️ כמו contradiction — ניתן למדידה אמיתית רק ב-benchmarks. |

---

## 15. recovery_success_rate ✅

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז ההתאוששויות המוצלחות |
| **נוסחה** | `count(recovery_needed=true AND subsequent_execution_status=completed) / count(recovery_needed=true)` |
| **סף טוב** | ≥ 80% |
| **סף כשל** | < 50% |
| **שדות trace** | `recovery_needed`, `recovery_action`, `execution_status` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ ניתן למדידה — אם recovery_needed=true, בודקים אם ה-interaction הבא הצליח. |

---

## 16. multi_turn_consistency 🔮

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז שיחות רב-תורניות ששמרו על הקשר נכון |
| **נוסחה** | `count(consistent_multi_turn_sessions) / count(multi_turn_sessions)` |
| **סף טוב** | ≥ 90% |
| **סף כשל** | < 70% |
| **שדות trace** | `session_id`, `conversation_state` |
| **תדירות מדידה** | שבועית |
| **כנות** | 🔮 "consistent" דורש human evaluation מורכבת. **Proxy**: אם `conversation_state=correction` → probable inconsistency before. אבל זה תופס רק מקרים שיוני תיקן, לא מקרים שעברו בשקט. |

---

## 17. premature_surrender_rate ✅ (partially)

| Property | Value |
|----------|-------|
| **מה מודד** | אחוז הפעמים שדבורה אמרה "לא יכולה" כשבעצם יכלה |
| **נוסחה** | `count(execution_status=failed AND search_exhaustion IN [single_source, partial]) / count(execution_status=failed)` |
| **סף טוב** | ≤ 5% |
| **סף כשל** | > 15% |
| **שדות trace** | `execution_status`, `search_exhaustion` |
| **תדירות מדידה** | שבועית |
| **כנות** | ✅ Proxy חלקי — `failed + non-exhaustive search` = red flag. אבל ⚠️ לא כל failure עם partial search היא premature surrender (אולי באמת אין פתרון). Human review על failures נדרש לכיול. |

---

## סיכום מצב מדידה

| Status | Metrics |
|--------|---------|
| ✅ ניתן למדידה עכשיו | search_exhaustion_rate, task_completion_rate, unnecessary_action_rate, unnecessary_tool_rate, recovery_success_rate, premature_surrender_rate (proxy) |
| ⚠️ דורש human labels | response_strategy_accuracy, tool_precision, tool_recall, followup_accuracy, memory_precision, memory_recall, false_completion_rate, contradiction_detection_rate, missing_info_detection_rate |
| 🔮 אספירציוני | multi_turn_consistency |
| ✅ (partial) | loop_closure_rate |

**מסקנה מעשית**: מתוך 17 metrics, רק ~6 ניתנים למדידה אוטומטית מלאה. השאר דורשים human labeling. זה לא בעיה — זו עובדה שצריך לתכנן סביבה.
