# תרחישי בנצ'מרק — Dvorah Benchmark Scenarios
<!-- Status: Canonical -->
<!-- Purpose: Concrete test scenarios for evaluation -->
<!-- Authority: Source of truth for benchmark tests -->

## הנחיות

- כל תרחיש מדמה interaction אמיתי של דבורה
- "Expected output" הוא **התנהגותי**, לא טקסט מדויק (LLM = non-deterministic)
- Success criteria = observable behaviors, not string matching
- כל תרחיש מניח שדבורה טעונה עם workspace מלא (memory, integrations, policies)

---

## BM-001: חיפוש Credentials — Google Ads

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, task closure |
| **מטרה** | לוודא שדבורה מחפשת credentials במספר מקורות לפני שמוותרת |
| **רמת קושי** | intermediate |
| **Input** | "תבדקי מה קורה עם הקמפיין של גוגל אדס" |
| **Setup** | credentials נמצאים ב-`integrations/GOOGLE_ADS.md` אבל לא ב-`CAPABILITY_INDEX.md` |
| **מה המערכת צריכה לזהות** | שזו בקשת execute, שצריך credentials, שצריך לחפש ביותר ממקום אחד |
| **החלטה נכונה** | חפש ב-CAPABILITY_INDEX → integrations/ → state/ → memory/. מצא ב-integrations, בצע |
| **מה אסור שיקרה** | ❌ "אין לי גישה ל-Google Ads" אחרי חיפוש אחד. ❌ premature surrender |
| **קריטריוני הצלחה** | `search_exhaustion=exhaustive` + `execution_status=completed` + credentials נמצאו |
| **Failure Modes צפויים** | FM-001, FM-018 |

---

## BM-002: הפעלת אור — ביצוע מיידי

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy, tool usage |
| **מטרה** | לוודא שדבורה מבצעת פעולה פשוטה בלי לנתח/להסביר/לשאול |
| **רמת קושי** | basic |
| **Input** | "תדליקי אור בסלון" |
| **Setup** | Control4 integration מוגדר ומחובר |
| **מה המערכת צריכה לזהות** | intent=execute, כלי=Control4, אין צורך בהבהרה |
| **החלטה נכונה** | execute immediately. Response: "בוצע." (or equivalent minimal) |
| **מה אסור שיקרה** | ❌ "כדי להדליק אור בסלון..." ❌ "לאיזה חדר?" ❌ הסבר ארוך |
| **קריטריוני הצלחה** | `selected_response_strategy=execute` + `tool_calls_count >= 1` + response ≤ 10 words |
| **Failure Modes צפויים** | FM-013, FM-016 |

---

## BM-003: סיכום קבוצת WhatsApp — silence vs report

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy, context understanding |
| **מטרה** | לוודא שדבורה יודעת מתי לשתוק בקבוצה ומתי לענות |
| **רמת קושי** | intermediate |
| **Input** | הודעה בקבוצה: "מישהו יודע מתא פיצה טובה בתל אביב?" (לא מכוונת לדבורה) |
| **Setup** | GROUP_BEHAVIOR_POLICY loaded, group context = social group |
| **מה המערכת צריכה לזהות** | שזו הודעה בקבוצה, לא מכוונת לדבורה, silence = correct strategy |
| **החלטה נכונה** | `selected_response_strategy=silence` |
| **מה אסור שיקרה** | ❌ תשובה עם המלצות פיצה. ❌ כל תגובה שלא התבקשה |
| **קריטריוני הצלחה** | `selected_response_strategy=silence` + no message sent |
| **Failure Modes צפויים** | FM-002 |

---

## BM-004: בדיקת מייל — דיווח סטטוס

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, response strategy |
| **מטרה** | לוודא שדבורה מושכת מיילים ומדווחת בצורה מסוננת |
| **רמת קושי** | basic |
| **Input** | "מה יש במייל?" |
| **Setup** | gog/Gmail integration active |
| **מה המערכת צריכה לזהות** | intent=report, tool=gog, format=filtered summary |
| **החלטה נכונה** | הפעל gog mail → סנן → הצג טבלה/רשימה מסוננת |
| **מה אסור שיקרה** | ❌ "בוקר טוב! אשמח לסקור..." ❌ Full dump של כל מייל ❌ "אין לי גישה" |
| **קריטריוני הצלחה** | Tool used + structured output + no filler text |
| **Failure Modes צפויים** | FM-004, FM-016 |

---

## BM-005: הזמנת מונית עם כתובת חסרה

| Property | Value |
|----------|-------|
| **קטגוריה** | missing info, response strategy |
| **מטרה** | לוודא שדבורה מזהה מידע חסר ושואלת — אבל רק מה שחסר באמת |
| **רמת קושי** | intermediate |
| **Input** | "תזמיני לי מונית לעוד שעה" |
| **Setup** | Gett integration active. כתובת בית שמורה ב-memory. כתובת יעד לא ידועה |
| **מה המערכת צריכה לזהות** | intent=execute, missing_info=destination, available_info=home address + time |
| **החלטה נכונה** | `selected_response_strategy=clarify`. שאלה: "לאן?" (לא "מאיפה ולאן?" — כי כתובת בית ידועה) |
| **מה אסור שיקרה** | ❌ "מאיזו כתובת?" (כבר ב-memory). ❌ הזמנה בלי יעד. ❌ ניתוח ארוך |
| **קריטריוני הצלחה** | `detected_missing_info.found=true` + asks only for destination + doesn't re-ask known info |
| **Failure Modes צפויים** | FM-002, FM-005 |

---

## BM-006: סתירה בין memory לבקשה

| Property | Value |
|----------|-------|
| **קטגוריה** | contradiction detection |
| **מטרה** | לוודא שדבורה מזהה סתירה ומרימה flag |
| **רמת קושי** | advanced |
| **Input** | "תזמיני מונית מהבית בהרצליה" |
| **Setup** | Memory: "יוני גר ברחוב X בתל אביב" |
| **מה המערכת צריכה לזהות** | סתירה: memory אומר ת"א, input אומר הרצליה |
| **החלטה נכונה** | `contradiction_flags.found=true`. שאלה: "ב-memory שמור שאתה גר בת"א — עברת להרצליה?" |
| **מה אסור שיקרה** | ❌ להזמין מהרצליה בלי לשאול. ❌ להזמין מת"א ולהתעלם מהבקשה. ❌ להתעלם מהסתירה |
| **קריטריוני הצלחה** | Contradiction flagged + clarification asked + memory potentially updated |
| **Failure Modes צפויים** | FM-010 |

---

## BM-007: Multi-step workflow — שליחת מייל

| Property | Value |
|----------|-------|
| **קטגוריה** | multi-turn consistency, task closure |
| **מטרה** | לוודא שדבורה שומרת הקשר לאורך workflow רב-שלבי |
| **רמת קושי** | advanced |
| **Input (multi-turn)** | Turn 1: "תשלחי מייל לדוד" / Turn 2: "תכתבי שהפגישה ביום רביעי בעשר" / Turn 3: "ותוסיפי שישלח את המסמכים מראש" / Turn 4: "תשלחי" |
| **Setup** | gog integration active. "דוד" = contact in memory |
| **מה המערכת צריכה לזהות** | multi_step conversation, accumulating content, final execute trigger |
| **החלטה נכונה** | Build email progressively. On "תשלחי" → send with all accumulated content |
| **מה אסור שיקרה** | ❌ שולח אחרי Turn 1. ❌ שוכח content מ-Turn 2 בזמן Turn 4. ❌ שואל "מה לכתוב?" |
| **קריטריוני הצלחה** | All content from turns 1-3 in final email + sent on turn 4 + `completion_status=task_complete` |
| **Failure Modes צפויים** | FM-005, FM-011 |

---

## BM-008: Recovery מכשל API

| Property | Value |
|----------|-------|
| **קטגוריה** | recovery |
| **מטרה** | לוודא שדבורה מתאוששת מ-API failure |
| **רמת קושי** | intermediate |
| **Input** | "תשלחי מייל ליעל על הפגישה מחר" |
| **Setup** | gog mail send returns 401 Unauthorized (token expired) |
| **מה המערכת צריכה לזהות** | execution failed, recovery needed, token issue |
| **החלטה נכונה** | Detect error → try token refresh → if still fails → report to Yoni with specific error |
| **מה אסור שיקרה** | ❌ "בוצע" (false closure). ❌ שקט (swallow error). ❌ ויתור מיידי |
| **קריטריוני הצלחה** | `recovery_needed=true` + `recovery_action` not null + error reported or resolved |
| **Failure Modes צפויים** | FM-007, FM-015 |

---

## BM-009: שאלה שלא דורשת כלים

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage |
| **מטרה** | לוודא שדבורה לא מפעילה כלים כשאפשר לענות מ-context |
| **רמת קושי** | basic |
| **Input** | "מה ההפרש בשעות בין ישראל לניו יורק?" |
| **Setup** | No special setup needed |
| **מה המערכת צריכה לזהות** | intent=report, no tools needed, answerable from knowledge |
| **החלטה נכונה** | Answer directly: "7 שעות" (or current DST-aware answer) |
| **מה אסור שיקרה** | ❌ web_search for timezone. ❌ "אבדוק..." + tool call |
| **קריטריוני הצלחה** | `tool_decision=not_needed` + `tool_calls_count=0` + correct answer |
| **Failure Modes צפויים** | FM-003 |

---

## BM-010: בקשת דעה

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy |
| **מטרה** | לוודא שדבורה נותנת דעה ישירה, לא ניתוח בלי עמדה |
| **רמת קושי** | basic |
| **Input** | "מה דעתך, עדיף לפרסם בגוגל או בפייסבוק לקמפיין B2B?" |
| **Setup** | Google Ads experience from integrations |
| **מה המערכת צריכה לזהות** | intent=suggest, opinion requested |
| **החלטה נכונה** | Direct opinion: "גוגל. הסיבה: [X]. אבל שווה לשקול [Y]" |
| **מה אסור שיקרה** | ❌ "זו שאלה מעניינת! יש כמה גישות..." ❌ Long analysis without stance ❌ "זה תלוי ב..." without recommendation |
| **קריטריוני הצלחה** | Response starts with clear recommendation + reasoning + brief caveat |
| **Failure Modes צפויים** | FM-013, FM-014 |

---

## BM-011: לולאה פתוחה — followup נדרש

| Property | Value |
|----------|-------|
| **קטגוריה** | open loops, followup |
| **מטרה** | לוודא שדבורה מסמנת followup כשנדרש |
| **רמת קושי** | intermediate |
| **Input** | "תשלחי ליעל את ההצעה שעבדנו עליה אתמול ותבדקי שהיא קיבלה" |
| **Setup** | gog integration active, file "הצעה" exists |
| **מה המערכת צריכה לזהות** | Two tasks: (1) send email, (2) verify receipt. Task 2 requires followup |
| **החלטה נכונה** | Send → report sent → mark `followup_needed=true`, `followup_type=verification` |
| **מה אסור שיקרה** | ❌ Send + "בוצע" without marking followup. ❌ Forgetting the verification request |
| **קריטריוני הצלחה** | Email sent + `open_loop_created` includes verification + `followup_needed=true` |
| **Failure Modes צפויים** | FM-006, FM-007 |

---

## BM-012: שמירה לזיכרון — העדפה חדשה

| Property | Value |
|----------|-------|
| **קטגוריה** | memory |
| **מטרה** | לוודא שדבורה שומרת העדפה חדשה |
| **רמת קושי** | basic |
| **Input** | "מעכשיו כשאני מבקש מונית, תמיד תזמיני Gett ולא אובר" |
| **Setup** | Both Gett and Uber in integrations. No preference in memory yet |
| **מה המערכת צריכה לזהות** | New preference, should be saved to memory |
| **החלטה נכונה** | Acknowledge + save to memory: "Yoni prefers Gett over Uber" |
| **מה אסור שיקרה** | ❌ "בסדר" without saving. ❌ "אשמור" without actually writing. ❌ Not saving at all |
| **קריטריוני הצלחה** | `memory_write_decision=wrote` + `memory_write_reason` references preference + actual file write |
| **Failure Modes צפויים** | FM-009 |

---

## BM-013: לא לשמור לזיכרון — מידע חד-פעמי

| Property | Value |
|----------|-------|
| **קטגוריה** | memory |
| **מטרה** | לוודא שדבורה לא שומרת מידע חולף/חד-פעמי |
| **רמת קושי** | basic |
| **Input** | "תזמיני לי מונית ל-ויצמן 10 רמת גן" |
| **Setup** | One-time destination, not home/work |
| **מה המערכת צריכה לזהות** | This is a one-time destination, not a preference |
| **החלטה נכונה** | Order taxi + `memory_write_decision=skipped` |
| **מה אסור שיקרה** | ❌ Saving "Yoni goes to Weizmann 10 Ramat Gan" to memory |
| **קריטריוני הצלחה** | `memory_write_decision=skipped` or `not_applicable` |
| **Failure Modes צפויים** | FM-008 |

---

## BM-014: תיקון טעות — correction handling

| Property | Value |
|----------|-------|
| **קטגוריה** | conversation state detection, recovery |
| **מטרה** | לוודא שדבורה מזהה תיקון ופועלת בהתאם |
| **רמת קושי** | intermediate |
| **Input (multi-turn)** | Turn 1: "תשלחי מייל לדוד" / [דבורה שולחת לדוד כהן] / Turn 2: "לא, לדוד לוי" |
| **Setup** | Two contacts named David in memory |
| **מה המערכת צריכה לזהות** | conversation_state=correction, wrong recipient, need to resend |
| **החלטה נכונה** | Identify correction → resend to correct David → confirm |
| **מה אסור שיקרה** | ❌ "שלחתי כבר" (ignoring correction). ❌ "לאיזה דוד?" (already told). ❌ Not actually resending |
| **קריטריוני הצלחה** | `conversation_state=correction` detected + resent to correct recipient + confirmed |
| **Failure Modes צפויים** | FM-005, FM-015 |

---

## BM-015: ניהול משימות — workspace

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, task closure |
| **מטרה** | לוודא שדבורה מעדכנת state/task files כשנדרש |
| **רמת קושי** | intermediate |
| **Input** | "ההצעה לקליינט X אושרה, תעדכני את הסטטוס" |
| **Setup** | Task tracking in workspace state/ files |
| **מה המערכת צריכה לזהות** | State update needed, specific file to update |
| **החלטה נכונה** | Find relevant state file → update status → confirm |
| **מה אסור שיקרה** | ❌ "באיזה קובץ?" (should find it). ❌ "עדכנתי" without actually writing. ❌ Creating duplicate entry |
| **קריטריוני הצלחה** | File found + updated + `completion_status=task_complete` |
| **Failure Modes צפויים** | FM-018, FM-007 |

---

## BM-016: Smart Home — פעולה מורכבת

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, multi-turn consistency |
| **מטרה** | לוודא שדבורה מטפלת בפעולת smart home מורכבת |
| **רמת קושי** | advanced |
| **Input** | "תכיני את הבית — אני מגיע בעוד 20 דקות. אור בסלון, מזגן על 23, וסגרי תריסים בחדר שינה" |
| **Setup** | Control4 integration active |
| **מה המערכת צריכה לזהות** | Three separate actions, all execute, via Control4 |
| **החלטה נכונה** | Execute all three → report completion of each |
| **מה אסור שיקרה** | ❌ Doing only one. ❌ "מה הטמפרטורה?" (already specified). ❌ Forgetting one action |
| **קריטריוני הצלחה** | All 3 actions executed + brief confirmation covering all |
| **Failure Modes צפויים** | FM-005, FM-011, FM-007 |

---

## BM-017: Gett — הזמנה עם כל המידע

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, response strategy |
| **מטרה** | לוודא ביצוע ישיר כשכל המידע קיים |
| **רמת קושי** | basic |
| **Input** | "תזמיני לי מונית ל-18:00 לנתב"ג" |
| **Setup** | Gett integration active. Home address in memory |
| **מה המערכת צריכה לזהות** | All info available: from=home, to=airport, time=18:00 |
| **החלטה נכונה** | Execute immediately. No clarification needed |
| **מה אסור שיקרה** | ❌ "מאיזו כתובת?" (home is in memory). ❌ "באיזה שדה תעופה?" (נתב"ג = TLV, obvious) |
| **קריטריוני הצלחה** | `tool_decision=used` + `detected_missing_info.found=false` + `execution_status=completed` |
| **Failure Modes צפויים** | FM-002, FM-004 |

---

## BM-018: סיכום קבוצה — כשנשאל ישירות

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy, context understanding |
| **מטרה** | לוודא שדבורה מסכמת קבוצה כשמבקשים ממנה |
| **רמת קושי** | intermediate |
| **Input** | "דבורה, מה פספסתי בקבוצה?" (in WhatsApp group) |
| **Setup** | GROUP_BEHAVIOR_POLICY loaded. Recent group messages available |
| **מה המערכת צריכה לזהות** | Addressed directly → should respond. intent=report |
| **החלטה נכונה** | `selected_response_strategy=report`. Summarize key points from recent group messages |
| **מה אסור שיקרה** | ❌ silence (was addressed directly). ❌ Full transcript. ❌ "אין לי גישה להודעות ישנות" |
| **קריטריוני הצלחה** | Summary provided + concise + covers key topics |
| **Failure Modes צפויים** | FM-002, FM-014 |

---

## BM-019: בקשה עמומה — clarify vs execute

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy, missing info |
| **מטרה** | לוודא שדבורה מבחינה בין מקרה שצריך הבהרה לבין מקרה שאפשר להתקדם |
| **רמת קושי** | advanced |
| **Input** | "תטפלי לי בעניין של הביטוח" |
| **Setup** | No recent context about insurance. No insurance info in memory |
| **מה המערכת צריכה לזהות** | Ambiguous request. No context to infer. Must clarify |
| **החלטה נכונה** | `selected_response_strategy=clarify`. "איזה ביטוח? רכב, בריאות, דירה? ומה צריך — חידוש, תביעה, בירור?" |
| **מה אסור שיקרה** | ❌ Start searching for "insurance" randomly. ❌ "מה זה ביטוח?" ❌ Long analysis of insurance types |
| **קריטריוני הצלחה** | `detected_missing_info.found=true` + focused clarification question + no unnecessary action |
| **Failure Modes צפויים** | FM-002, FM-013 |

---

## BM-020: Redirect — בקשה מחוץ לתחום

| Property | Value |
|----------|-------|
| **קטגוריה** | response strategy |
| **מטרה** | לוודא שדבורה מפנה כשלא יכולה באמת לעזור |
| **רמת קושי** | basic |
| **Input** | "יש לי כאב ראש חזק כבר שלושה ימים, מה לעשות?" |
| **Setup** | Standard setup |
| **מה המערכת צריכה לזהות** | Medical question → redirect, don't advise |
| **החלטה נכונה** | `selected_response_strategy=redirect`. "לך לרופא. שלוש ימים של כאב ראש חזק זה סיבה לבדיקה." |
| **מה אסור שיקרה** | ❌ Medical advice. ❌ "קח אקמול". ❌ Long health analysis. ❌ "אני לא רופאה אבל..." + advice anyway |
| **קריטריוני הצלחה** | redirect strategy + short directive answer + no medical advice |
| **Failure Modes צפויים** | FM-012, FM-014 |

---

## BM-021: False Closure Detection — מייל שנכשל

| Property | Value |
|----------|-------|
| **קטגוריה** | task closure, recovery |
| **מטרה** | לוודא שדבורה לא מדווחת "בוצע" כשהכלי החזיר error |
| **רמת קושי** | intermediate |
| **Input** | "תשלחי מייל ללקוח עם ה-invoice" |
| **Setup** | gog mail send returns error (e.g., attachment too large) |
| **מה המערכת צריכה לזהות** | Tool returned error. Must not report success |
| **החלטה נכונה** | Report failure + explain why + suggest alternative (smaller attachment, link, etc.) |
| **מה אסור שיקרה** | ❌ "נשלח ✅". ❌ Silent failure. ❌ No error handling |
| **קריטריוני הצלחה** | `execution_status=failed` + `recovery_needed=true` + error reported to user |
| **Failure Modes צפויים** | FM-007, FM-015 |

---

## BM-022: Context from Previous Session — memory usage

| Property | Value |
|----------|-------|
| **קטגוריה** | memory, context understanding |
| **מטרה** | לוודא שדבורה משתמשת ב-memory מ-sessions קודמים |
| **רמת קושי** | intermediate |
| **Input** | "תמשיכי עם הפרויקט שדיברנו עליו" |
| **Setup** | Memory file contains recent project discussion details |
| **מה המערכת צריכה לזהות** | Needs to load memory, find recent project, continue |
| **החלטה נכונה** | Load relevant memory → identify project → continue where left off |
| **מה אסור שיקרה** | ❌ "איזה פרויקט?" (it's in memory). ❌ Starting from scratch. ❌ Hallucinating wrong project |
| **קריטריוני הצלחה** | Correct project identified from memory + contextual continuation |
| **Failure Modes צפויים** | FM-005, FM-009, FM-018 |

---

## BM-023: Unnecessary Memory Write — filtering noise

| Property | Value |
|----------|-------|
| **קטגוריה** | memory |
| **מטרה** | לוודא שדבורה לא שומרת מידע לא רלוונטי |
| **רמת קושי** | basic |
| **Input** | "מה מזג האוויר היום?" / [דבורה עונה: "25 מעלות, בהיר"] / "תודה" |
| **Setup** | Standard |
| **מה המערכת צריכה לזהות** | Weather query = ephemeral, no memory write needed |
| **החלטה נכונה** | `memory_write_decision=not_applicable` |
| **מה אסור שיקרה** | ❌ Saving "Yoni asked about weather on March 20". ❌ Any memory write |
| **קריטריוני הצלחה** | No memory write + no self-check flags |
| **Failure Modes צפויים** | FM-008 |

---

## BM-024: Concurrent Requests — priority handling

| Property | Value |
|----------|-------|
| **קטגוריה** | context understanding, response strategy |
| **מטרה** | לוודא שדבורה מתמודדת עם כמה בקשות במקביל |
| **רמת קושי** | advanced |
| **Input** | "תבדקי מייל, ותזמיני מונית ל-17:00 לבית ספר של הילדים" |
| **Setup** | gog + Gett active. School address in memory |
| **מה המערכת צריכה לזהות** | Two independent tasks. Both should be executed |
| **החלטה נכונה** | Execute both. Report both results |
| **מה אסור שיקרה** | ❌ Doing only one. ❌ "אטפל קודם ב..." (just do both). ❌ Forgetting the second task |
| **קריטריוני הצלחה** | Both tasks attempted + both reported + `open_loops_after` accounts for both |
| **Failure Modes צפויים** | FM-005, FM-006 |

---

## BM-025: Edge — empty result handling

| Property | Value |
|----------|-------|
| **קטגוריה** | tool usage, response strategy |
| **מטרה** | לוודא שדבורה מטפלת נכון בתוצאה ריקה |
| **רמת קושי** | intermediate |
| **Input** | "יש מיילים חדשים מאיתי?" |
| **Setup** | gog returns empty result (no emails from "Itai") |
| **מה המערכת צריכה לזהות** | Empty result ≠ error. Report "no results" cleanly |
| **החלטה נכונה** | "אין מיילים חדשים מאיתי." |
| **מה אסור שיקרה** | ❌ "משהו השתבש". ❌ "אין לי גישה". ❌ Long explanation of why there are no emails |
| **קריטריוני הצלחה** | `execution_status=completed` + clean "no results" message + `completion_status=task_complete` |
| **Failure Modes צפויים** | FM-001, FM-014 |

---

## סיכום תרחישים לפי קטגוריה

| קטגוריה | תרחישים |
|----------|---------|
| response strategy | BM-002, BM-003, BM-010, BM-017, BM-019, BM-020 |
| tool usage | BM-001, BM-004, BM-009, BM-016, BM-025 |
| missing info / contradiction | BM-005, BM-006, BM-019 |
| memory | BM-012, BM-013, BM-022, BM-023 |
| open loops / followup | BM-011, BM-024 |
| recovery | BM-008, BM-014, BM-021 |
| multi-turn consistency | BM-007, BM-016 |
| task closure | BM-001, BM-015, BM-021 |
| context understanding | BM-003, BM-018, BM-024 |

## סיכום לפי רמת קושי

| רמת קושי | תרחישים |
|-----------|---------|
| basic (8) | BM-002, BM-004, BM-009, BM-010, BM-012, BM-013, BM-017, BM-020, BM-023 |
| intermediate (10) | BM-001, BM-003, BM-005, BM-008, BM-011, BM-014, BM-015, BM-018, BM-022, BM-025 |
| advanced (5) | BM-006, BM-007, BM-016, BM-019, BM-024 |
