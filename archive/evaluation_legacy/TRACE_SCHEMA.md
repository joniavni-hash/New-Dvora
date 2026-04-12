# סכמת Trace — Dvorah Interaction Trace Schema
<!-- Status: Canonical -->
<!-- Purpose: Structured log schema for every interaction -->
<!-- Authority: Source of truth for trace format -->

## מבוא

כל interaction של דבורה מייצר trace record. זה הבסיס לכל שכבות ההערכה.

**פורמט**: JSON object per interaction.  
**אחסון**: JSONL file, rotated daily.  
**מיקום**: `/home/jonia/.openclaw/workspace/evaluation/traces/YYYY-MM-DD.jsonl`

---

## שדות הסכמה

### מטא-דאטה

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `trace_id` | string (UUID) | ✅ | מזהה ייחודי ל-trace | — |
| `timestamp` | string (ISO 8601) | ✅ | זמן ההתחלה | latency calculations |
| `session_id` | string | ✅ | מזהה session | multi_turn_consistency |
| `channel` | string | ✅ | ערוץ (whatsapp, heartbeat, cli, etc.) | segmentation |
| `model_used` | string | ✅ | מודל שבשימוש (e.g. "claude-sonnet-4-20250514") | segmentation |
| `latency_ms` | integer | ✅ | זמן מ-input עד response סופי | performance tracking |

### Input & Intent

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `user_input` | string | ✅ | הטקסט המלא מהמשתמש | — |
| `interpreted_intent` | enum | ✅ | מה דבורה הבינה שהמשתמש רוצה | response_strategy_accuracy |
| `conversation_state` | enum | ✅ | מצב השיחה | multi_turn_consistency |

**interpreted_intent values:**
- `execute` — בקשה לביצוע
- `clarify` — שאלה להבהרה
- `suggest` — בקשה להמלצה
- `report` — בקשה לדיווח/סטטוס
- `silence` — לא צריך תגובה (למשל בקבוצה)
- `redirect` — צריך להפנות למקום אחר

**conversation_state values:**
- `new_request` — בקשה חדשה
- `continuation` — המשך של משימה פתוחה
- `followup` — שאלת המשך
- `correction` — תיקון של משהו שדבורה עשתה
- `multi_step` — חלק מתהליך רב-שלבי

### זיהוי חסרים וסתירות

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `detected_missing_info` | object | ✅ | `{found: boolean, details: string\|null}` | missing_info_detection_rate |
| `contradiction_flags` | object | ✅ | `{found: boolean, details: string\|null}` | contradiction_detection_rate |

### אסטרטגיית תגובה

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `selected_response_strategy` | enum | ✅ | האסטרטגיה שנבחרה | response_strategy_accuracy |

**selected_response_strategy values:**
- `execute` — מבצע את הפעולה
- `clarify` — שואל הבהרה
- `suggest` — מציע אפשרויות
- `report` — מדווח סטטוס
- `silence` — לא מגיב (בעיקר בקבוצות)
- `redirect` — מפנה למקום אחר

### כלים (Tools)

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `tool_candidates` | array[string] | ✅ | כלים שנשקלו | tool_precision, tool_recall |
| `tool_decision` | enum | ✅ | החלטה לגבי שימוש בכלים | tool_precision, unnecessary_tool_rate |
| `tools_used` | array[string] | ✅ | כלים שהופעלו בפועל | tool_precision, tool_recall |
| `tool_calls_count` | integer | ✅ | מספר קריאות כלים | unnecessary_tool_rate |

**tool_decision values:**
- `used` — השתמש בכלים
- `skipped` — היה כלי רלוונטי, החליט לא להשתמש
- `not_needed` — לא היה צורך בכלים

### זיכרון (Memory)

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `memory_write_decision` | enum | ✅ | האם נכתב לזיכרון | memory_precision, memory_recall |
| `memory_write_reason` | string\|null | optional | סיבה אם נכתב | memory_precision |

**memory_write_decision values:**
- `wrote` — נכתב לזיכרון
- `skipped` — היה מידע רלוונטי, החליט לא לשמור
- `not_applicable` — לא רלוונטי

### לולאות פתוחות (Open Loops)

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `open_loops_before` | integer | ✅ | מספר לולאות פתוחות לפני | loop_closure_rate |
| `open_loops_after` | integer | ✅ | מספר לולאות פתוחות אחרי | loop_closure_rate |
| `open_loops_created` | array[string] | ✅ | לולאות שנוצרו (תיאור קצר) | loop_closure_rate |
| `open_loops_closed` | array[string] | ✅ | לולאות שנסגרו (תיאור קצר) | loop_closure_rate |

### מעקב (Followup)

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `followup_needed` | boolean | ✅ | האם נדרש followup | followup_accuracy |
| `followup_type` | enum | ✅ | סוג ה-followup | followup_accuracy |

**followup_type values:**
- `reminder` — תזכורת ליוני
- `verification` — בדיקה שהפעולה הצליחה
- `proactive_check` — בדיקה יזומה מאוחר יותר
- `none` — לא נדרש

### ביצוע והתאוששות

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `execution_status` | enum | ✅ | סטטוס הביצוע | task_completion_rate |
| `recovery_needed` | boolean | ✅ | האם נדרשה התאוששות | recovery_success_rate |
| `recovery_action` | string\|null | optional | מה נעשה להתאוששות | recovery_success_rate |

**execution_status values:**
- `completed` — הושלם
- `partial` — הושלם חלקית
- `failed` — נכשל
- `not_applicable` — לא היה ביצוע (שאלה, שיחה, וכו')

### סטטוס סיום

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `completion_status` | enum | ✅ | סטטוס המשימה | task_completion_rate, false_completion_rate |

**completion_status values:**
- `task_complete` — המשימה הושלמה
- `task_open` — המשימה עדיין פתוחה
- `task_progressed` — התקדמות אבל לא סיום
- `no_task` — לא הייתה משימה (שיחה, שאלה)

### מיצוי חיפוש

| Field | Type | Required | Description | Used in Metrics |
|-------|------|----------|-------------|-----------------|
| `search_exhaustion` | enum | ✅ | כמה מקיף היה החיפוש | search_exhaustion_rate, premature_surrender_rate |

**search_exhaustion values:**
- `exhaustive` — נבדקו כל המקורות הרלוונטיים
- `partial` — נבדקו חלק מהמקורות
- `single_source` — נבדק מקור אחד בלבד
- `not_applicable` — לא היה חיפוש

---

## דוגמת Trace Record

```json
{
  "trace_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "timestamp": "2026-03-20T14:30:00+02:00",
  "session_id": "session-xyz-123",
  "channel": "whatsapp",
  "model_used": "claude-sonnet-4-20250514",
  "latency_ms": 3200,
  
  "user_input": "תבדקי מה קורה עם הקמפיין של גוגל אדס",
  "interpreted_intent": "execute",
  "conversation_state": "new_request",
  
  "detected_missing_info": {"found": false, "details": null},
  "contradiction_flags": {"found": false, "details": null},
  
  "selected_response_strategy": "execute",
  
  "tool_candidates": ["gog", "web_search", "browser"],
  "tool_decision": "used",
  "tools_used": ["browser"],
  "tool_calls_count": 3,
  
  "memory_write_decision": "skipped",
  "memory_write_reason": null,
  
  "open_loops_before": 1,
  "open_loops_after": 1,
  "open_loops_created": [],
  "open_loops_closed": [],
  
  "followup_needed": false,
  "followup_type": "none",
  
  "execution_status": "completed",
  "recovery_needed": false,
  "recovery_action": null,
  
  "completion_status": "task_complete",
  "search_exhaustion": "exhaustive",
  
  "self_check": {
    "action_taken": true,
    "open_loop_created": false,
    "user_waiting": false,
    "pending_state_unhandled": false,
    "followup_required": false,
    "tool_intended_not_used": false,
    "tool_used_unnecessarily": false,
    "critical_info_missing": false,
    "unresolved_contradiction": false,
    "recovery_needed": false,
    "memory_written_unnecessarily": false,
    "memory_not_written": false,
    "search_exhausted": true
  }
}
```

---

## הערות מימוש

### איסוף Trace
הדרך הפשוטה ביותר למימוש ראשוני:
1. דבורה מייצרת trace object כחלק מ-self-check
2. כותבת ל-JSONL file ב-workspace
3. Evaluator script קורא את הקבצים ומחשב metrics

### מה לא לשמור ב-trace
- תוכן מלא של מיילים / הודעות (privacy)
- Credentials או tokens
- Raw tool output (רק summary)

### Trace Versioning
- שדה `schema_version: "1.0"` בכל record
- כששדות מתווספים, הגרסה עולה
- Parser חייב לטפל ב-backwards compatibility

### גודל צפוי
- ~1-2KB per trace record
- ~50-200 interactions ביום → ~100-400KB ביום
- Rotation שבועי מספיק בשלב הזה
