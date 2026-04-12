# קטלוג כשלים — Dvorah Failure Modes Catalog
<!-- Status: Canonical -->
<!-- Purpose: Catalog of all known failure modes -->
<!-- Authority: Source of truth for failure classification -->

---

## FM-001: Premature Surrender — כניעה מוקדמת

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה מצהירה "לא יכולה" או "לא מצאתי" אחרי חיפוש חלקי, כשבפועל המשאב/המידע קיים ונגיש |
| **תסמינים** | תשובה כמו "אין לי גישה ל...", "לא מצאתי...", "אני לא יכולה..." — אחרי ניסיון אחד בלבד |
| **זיהוי ב-trace** | `execution_status=failed` + `search_exhaustion IN [single_source, partial]` + `tool_calls_count <= 2` |
| **מטריקות מושפעות** | premature_surrender_rate, task_completion_rate, search_exhaustion_rate |
| **דוגמה** | יוני מבקש לבדוק Google Ads. דבורה מחפשת credentials במקום אחד, לא מוצאת, ומדווחת שאין לה גישה — למרות שה-credentials קיימים בקובץ אחר ב-workspace |
| **מנגנון מיטיגציה** | Self-check flag: `search_exhausted=false`. Policy: אם חיפוש ראשון נכשל, חייבת לנסות לפחות 3 מקורות לפני שמדווחת failure |
| **חומרה** | 🔴 **Blocker** — זה שבירת אמון. אם דבורה אומרת "לא יכולה" כשהיא יכולה, יוני יפסיק לסמוך עליה |

---

## FM-002: Wrong Response Strategy — אסטרטגיית תגובה שגויה

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה בוחרת באסטרטגיית תגובה לא מתאימה — למשל מבצעת במקום לשאול, או שואלת במקום לבצע |
| **תסמינים** | יוני מתקן ("לא ביקשתי שתעשי X, ביקשתי Y"), או דבורה שואלת שאלה שהתשובה כבר ברורה |
| **זיהוי ב-trace** | `conversation_state=correction` ב-interaction הבא. או: `selected_response_strategy != interpreted_intent` (proxy) |
| **מטריקות מושפעות** | response_strategy_accuracy |
| **דוגמה** | יוני: "תזמיני לי מונית ל-18:00". דבורה: "לאיזו כתובת?" — כשכתובת הבית כבר שמורה ב-memory |
| **מנגנון מיטיגציה** | לפני שאלת הבהרה, בדוק memory ו-context. אם המידע קיים — בצע, אל תשאל |
| **חומרה** | 🟡 **Major** — מעצבן, מאט, פוגע באמון |

---

## FM-003: Tool Overuse — שימוש יתר בכלים

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה מפעילה כלים כשהמידע כבר קיים ב-context, memory, או trace |
| **תסמינים** | קריאות API מיותרות, latency גבוה, חיפושים כפולים |
| **זיהוי ב-trace** | `tool_calls_count` גבוה ביחס למורכבות הבקשה. `tool_used_unnecessarily=true` ב-self-check |
| **מטריקות מושפעות** | tool_precision, unnecessary_tool_rate, unnecessary_action_rate |
| **דוגמה** | יוני שואל "מה השעה בניו יורק?" ודבורה מפעילה web_search במקום לחשב מ-timezone |
| **מנגנון מיטיגציה** | לפני tool call, בדוק: האם המידע כבר ב-context? האם אפשר לחשב בלי כלי? |
| **חומרה** | 🟡 **Major** — בזבוז resources, latency מיותר |

---

## FM-004: Tool Avoidance — הימנעות מכלים

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה לא משתמשת בכלי כשזה נחוץ — עונה מזיכרון ישן, מנחשת, או אומרת "אני לא יכולה" |
| **תסמינים** | מידע לא עדכני בתשובה, "אני לא בטוחה" כשהכלי זמין |
| **זיהוי ב-trace** | `tool_decision=skipped` + `execution_status IN [failed, partial]`. `tool_intended_not_used=true` ב-self-check |
| **מטריקות מושפעות** | tool_recall, task_completion_rate |
| **דוגמה** | יוני שואל "יש לי מיילים חדשים?" ודבורה עונה "אני לא יודעת, תבדוק" במקום להפעיל gog |
| **מנגנון מיטיגציה** | אם יש intent=execute ויש כלי מתאים ב-tool_candidates — להפעיל אותו |
| **חומרה** | 🟡 **Major** — פוגע בערך הבסיסי של דבורה |

---

## FM-005: Context Amnesia — שכחת הקשר

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה מתעלמת ממידע שנמסר קודם באותה שיחה |
| **תסמינים** | שואלת שאלה שכבר נענתה, מתעלמת מ-constraint שנאמר |
| **זיהוי ב-trace** | `conversation_state=correction` + ההקשר כבר היה ב-session. קשה לזהות אוטומטית — בעיקר benchmark |
| **מטריקות מושפעות** | multi_turn_consistency |
| **דוגמה** | יוני: "תזמיני מונית ל-18:00 לנתב"ג". [עשרה הודעות אח"כ] דבורה: "לאיזה כתובת?" |
| **מנגנון מיטיגציה** | Context window management. Summary של key facts שנאספו עד כה |
| **חומרה** | 🟡 **Major** — מתסכל ביותר |

---

## FM-006: Open Loop Leak — דליפת לולאות פתוחות

| Property | Value |
|----------|-------|
| **הגדרה** | משימה נשארת פתוחה בלי verification, reminder, או followup |
| **תסמינים** | לולאה שנוצרה אף פעם לא נסגרה. `open_loops_after > open_loops_before` ללא סיבה |
| **זיהוי ב-trace** | `open_loops_created` not empty + no corresponding `open_loops_closed` within reasonable time |
| **מטריקות מושפעות** | loop_closure_rate |
| **דוגמה** | דבורה שולחת מייל ליוני ומבטיחה לבדוק אם הגיע — אבל אף פעם לא בודקת |
| **מנגנון מיטיגציה** | Self-check: `open_loop_created=true` → log to followup queue |
| **חומרה** | 🟡 **Major** — ערעור אמינות |

---

## FM-007: False Closure — סגירה כוזבת

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה מסמנת משימה כ-complete כשהיא בפועל לא הושלמה |
| **תסמינים** | "בוצע" → יוני מגלה שלא בוצע |
| **זיהוי ב-trace** | `completion_status=task_complete` + יוני חוזר לאותו נושא (session correlation) |
| **מטריקות מושפעות** | false_completion_rate, task_completion_rate |
| **דוגמה** | דבורה: "שלחתי את המייל" — אבל הכלי החזיר error שלא נבדק |
| **מנגנון מיטיגציה** | אחרי tool call, לבדוק return value. לא לדווח "בוצע" עד שיש confirmation |
| **חומרה** | 🔴 **Blocker** — שבירת אמון חמורה |

---

## FM-008: Memory Pollution — זיהום זיכרון

| Property | Value |
|----------|-------|
| **הגדרה** | כתיבת מידע מיותר, שגוי, או ישן לזיכרון |
| **תסמינים** | קבצי memory גדלים מהר, מידע סותר מופיע ב-memory |
| **זיהוי ב-trace** | `memory_write_decision=wrote` + `memory_written_unnecessarily=true` ב-self-check. Frequency anomaly |
| **מטריקות מושפעות** | memory_precision |
| **דוגמה** | דבורה שומרת שיוני הזמין פיצה ביום שלישי — זה לא מידע שישמש בעתיד |
| **מנגנון מיטיגציה** | MEMORY_POLICY.md enforcement. Self-check flag |
| **חומרה** | 🟢 **Minor** (short term), 🟡 **Major** (long term — memory becomes unreliable) |

---

## FM-009: Memory Omission — השמטת זיכרון

| Property | Value |
|----------|-------|
| **הגדרה** | לא שומרת מידע חשוב שהיה צריך להיכתב |
| **תסמינים** | דבורה שואלת שוב על משהו שכבר נאמר לה ב-session קודם |
| **זיהוי ב-trace** | `memory_not_written=true` ב-self-check. Hard to detect automatically |
| **מטריקות מושפעות** | memory_recall |
| **דוגמה** | יוני אומר "הכתובת החדשה שלי היא X" — דבורה לא שומרת, ובשיחה הבאה שואלת את הכתובת |
| **מנגנון מיטיגציה** | Self-check: `memory_not_written` flag. Patterns: new address, new preference, new contact = always save |
| **חומרה** | 🟡 **Major** — פוגע ביכולת למידה ובאמון |

---

## FM-010: Contradiction Blindness — עיוורון לסתירות

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה לא מזהה סתירה בין מידע חדש לישן, או בתוך אותו context |
| **תסמינים** | פועלת על מידע סותר בלי להרים flag |
| **זיהוי ב-trace** | `contradiction_flags.found=false` כש-human reviewer מזהה סתירה. Benchmark only |
| **מטריקות מושפעות** | contradiction_detection_rate |
| **דוגמה** | Memory: "יוני גר בתל אביב". יוני: "תזמיני מונית מהבית בהרצליה". דבורה לא שואלת על הסתירה |
| **מנגנון מיטיגציה** | Compare input facts against loaded memory. Flag mismatches |
| **חומרה** | 🟡 **Major** — עלול לגרום לפעולות על בסיס מידע שגוי |

---

## FM-011: Multi-turn Drift — סחף בשיחות ארוכות

| Property | Value |
|----------|-------|
| **הגדרה** | בשיחות ארוכות דבורה מאבדת את ה-thread — שוכחת את המטרה המקורית או מחליפה הקשר |
| **תסמינים** | תשובות שלא מתחברות לבקשה המקורית, חזרה על שלבים שכבר בוצעו |
| **זיהוי ב-trace** | Session עם `conversation_state=multi_step` ארוך + `conversation_state=correction` |
| **מטריקות מושפעות** | multi_turn_consistency |
| **דוגמה** | workflow של 8 שלבים לבדיקת Google Ads. בשלב 6, דבורה שוכחת את הפילטר שנקבע בשלב 2 |
| **מנגנון מיטיגציה** | Context compression with key fact retention. Task state summary |
| **חומרה** | 🟡 **Major** |

---

## FM-012: Overconfidence — ביטחון יתר

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה פועלת בלי verification מספקת, בטוחה שהיא צודקת |
| **תסמינים** | פעולות חיצוניות בלי double-check, facts שמוצגים בביטחון אבל שגויים |
| **זיהוי ב-trace** | External action + no verification step. `recovery_needed=true` (post-hoc) |
| **מטריקות מושפעות** | false_completion_rate, recovery_success_rate |
| **דוגמה** | דבורה שולחת מייל לכתובת שגויה כי לא בדקה את ה-contact list |
| **מנגנון מיטיגציה** | EXTERNAL_ACTIONS_POLICY.md. Pre-action verification checklist |
| **חומרה** | 🟡 **Major** — יכול לגרום לנזק אמיתי |

---

## FM-013: Under-action — תת-פעולה

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה מנתחת, מסבירה, ומציעה — אבל לא עושה |
| **תסמינים** | תשובות ארוכות עם ניתוח במקום execution. "אפשר לעשות X, Y, Z" — בלי לעשות |
| **זיהוי ב-trace** | `interpreted_intent=execute` + `action_taken=false` (self-check). `selected_response_strategy=suggest` כשהיה צריך `execute` |
| **מטריקות מושפעות** | response_strategy_accuracy, task_completion_rate |
| **דוגמה** | יוני: "תכבי אור בסלון". דבורה: "כדי לכבות אור בסלון, צריך להפעיל את Control4..." |
| **מנגנון מיטיגציה** | ברירת מחדל: execute first, explain only if needed |
| **חומרה** | 🟡 **Major** — הופכת את דבורה לצ'אטבוט |

---

## FM-014: Beautiful but Useless Response — תשובה יפה אבל חסרת תועלת

| Property | Value |
|----------|-------|
| **הגדרה** | תשובה שנשמעת טוב, מנוסחת יפה, אבל לא פותרת את הבעיה |
| **תסמינים** | תשובה ארוכה, מנוסחת היטב, אבל לא עם actionable content |
| **זיהוי ב-trace** | ⚠️ קשה מאוד לזהות אוטומטית. `completion_status=task_complete` + human flags it as useless |
| **מטריקות מושפעות** | task_completion_rate (inflated), false_completion_rate |
| **דוגמה** | יוני: "למה הקמפיין לא עובד?" דבורה: סקירה מקיפה של 10 סיבות אפשריות, בלי לבדוק אף אחת |
| **מנגנון מיטיגציה** | After analysis, take action. Don't stop at listing options |
| **חומרה** | 🟡 **Major** — בזבוז זמן מוסווה |

---

## FM-015: Recovery Failure — כשל בהתאוששות

| Property | Value |
|----------|-------|
| **הגדרה** | פעולה נכשלה ודבורה לא מתאוששת — לא מנסה שוב, לא מדווחת, לא מחפשת חלופה |
| **תסמינים** | כשל שקט. Tool error שלא מטופל. "שלחתי" כשבעצם נכשל |
| **זיהוי ב-trace** | `recovery_needed=true` + `recovery_action=null` |
| **מטריקות מושפעות** | recovery_success_rate, false_completion_rate |
| **דוגמה** | gog mail send מחזיר 401. דבורה לא מנסה refresh, לא מדווחת — פשוט ממשיכה |
| **מנגנון מיטיגציה** | Always check tool return values. If error → retry or report. Never swallow errors |
| **חומרה** | 🔴 **Blocker** — failure שלא מטופל הוא גרוע מ-failure שמדווח |

---

## FM-016: Confirmation Noise — רעש אישורים

| Property | Value |
|----------|-------|
| **הגדרה** | שליחת הודעות "בוצע" או אישורים מיותרים שלא נדרשו |
| **תסמינים** | "בוצע ✅" על כל פעולה קטנה, הודעות followup מיותרות |
| **זיהוי ב-trace** | High frequency of `completion_status=task_complete` messages with low `tool_calls_count` |
| **מטריקות מושפעות** | unnecessary_action_rate |
| **דוגמה** | יוני: "תדליקי אור". דבורה: [מדליקה]. "האור בסלון דולק עכשיו ✅ אם תצטרך משהו נוסף אני כאן!" |
| **מנגנון מיטיגציה** | IDENTITY.md: minimal confirmation. "בוצע." is enough |
| **חומרה** | 🟢 **Minor** — מעצבן, לא קריטי |

---

## FM-017: State Mismatch — אי-התאמת מצב

| Property | Value |
|----------|-------|
| **הגדרה** | מה שדבורה חושבת על מצב המערכת לא תואם את המציאות |
| **תסמינים** | דבורה פועלת על הנחה שגויה (שהאור כבוי כשהוא דולק, שהמייל נשלח כשהוא לא) |
| **זיהוי ב-trace** | `recovery_needed=true` after an action that was thought to be successful. `pending_state_unhandled=true` |
| **מטריקות מושפעות** | false_completion_rate, recovery_success_rate |
| **דוגמה** | דבורה חושבת שהזמנת Gett הצליחה כי לא בדקה את ה-response status |
| **מנגנון מיטיגציה** | Always verify state after action. Don't assume success |
| **חומרה** | 🔴 **Blocker** — פעולות שמבוססות על מצב שגוי עלולות לגרום לנזק |

---

## FM-018: Credential/Resource Blindness — עיוורון למשאבים קיימים

| Property | Value |
|----------|-------|
| **הגדרה** | דבורה לא מוצאת credentials, config, או משאבים שקיימים ב-workspace |
| **תסמינים** | "אין לי את ה-API key ל..." כשהוא קיים. "אני לא יודעת איפה..." כשזה מתועד |
| **זיהוי ב-trace** | `search_exhaustion=single_source` + `execution_status=failed` + resource exists in workspace |
| **מטריקות מושפעות** | search_exhaustion_rate, premature_surrender_rate |
| **דוגמה** | Google Ads credentials קיימים ב-integrations/GOOGLE_ADS.md אבל דבורה חיפשה רק ב-CAPABILITY_INDEX.md ולא מצאה |
| **מנגנון מיטיגציה** | Search checklist: CAPABILITY_INDEX → integrations/ → state/ → memory/ → workspace root. לפחות 3 מקורות לפני "לא מצאתי" |
| **חומרה** | 🔴 **Blocker** — variant של FM-001, ספציפי למשאבים פנימיים |

---

## סיכום חומרה

| חומרה | Failure Modes | משמעות |
|--------|---------------|--------|
| 🔴 Blocker | FM-001, FM-007, FM-015, FM-017, FM-018 | עוצר release. דורש תיקון מיידי |
| 🟡 Major | FM-002, FM-003, FM-004, FM-005, FM-006, FM-008 (long-term), FM-009, FM-010, FM-011, FM-012, FM-013, FM-014 | דורש attention בתוך שבוע |
| 🟢 Minor | FM-008 (short-term), FM-016 | מטריד, לא דחוף |
