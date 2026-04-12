# מדיניות בדיקה עצמית — Dvorah Self-Check Policy
<!-- Status: Canonical -->
<!-- Purpose: Internal self-check mechanism -->
<!-- Authority: Source of truth for self-check flags -->

## עקרון מרכזי

בדיקה עצמית היא **לא ציון**. היא לא "כמה טוב עשיתי". היא רשימת flags בינאריים שמייצרים trace data אובייקטיבי.

**אחרי כל תשובה**, דבורה מפעילה את הבדיקה הזו ומייצרת self_check object ב-trace.

---

## Flags

### 1. action_taken
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם בוצעה פעולה בפועל? (tool call, file write, message send, etc.) |
| **true** | בוצעה לפחות פעולה אחת |
| **false** | לא בוצעה שום פעולה — רק טקסט |
| **למה חשוב** | מזהה FM-013 (under-action) ו-FM-014 (beautiful but useless) |

### 2. open_loop_created
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם נוצרה לולאה פתוחה שצריך לסגור בהמשך? |
| **true** | יש משהו שעוד צריך verification, followup, או בדיקה |
| **false** | לא נוצר commitment פתוח |
| **למה חשוב** | מזין loop_closure_rate. מגלה FM-006 (open loop leak) |

### 3. user_waiting
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם יוני מצפה ממני לעוד משהו? |
| **true** | שלחתי תשובה חלקית, או הבטחתי לחזור, או יש שלב נוסף |
| **false** | המשימה הסתיימה או העברתי את הכדור ליוני |
| **למה חשוב** | מזהה pending work שלא סומן |

### 4. pending_state_unhandled
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם יש state ידוע שלא טיפלתי בו? (heartbeat pending, previous failure unresolved) |
| **true** | יש pending state שהתעלמתי ממנו |
| **false** | כל state ידוע טופל או לא רלוונטי |
| **למה חשוב** | מזהה FM-017 (state mismatch) |

### 5. followup_required
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם אני צריכה לחזור לנושא הזה מאוחר יותר? |
| **true** | הבטחתי לבדוק, מחכה ל-response, צריך verification |
| **false** | לא נדרש followup |
| **למה חשוב** | מזין followup_accuracy. אם true → חייב להיכנס ל-trace followup_type |

### 6. tool_intended_not_used
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם התכוונתי להשתמש בכלי אבל לא עשיתי זאת? |
| **true** | חשבתי על tool call אבל וויתרתי / שכחתי / החלטתי נגד |
| **false** | לא הייתה כוונה שלא מומשה |
| **למה חשוב** | מזהה FM-004 (tool avoidance). Red flag אם true + execution_status=failed |

### 7. tool_used_unnecessarily
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם השתמשתי בכלי שלא הייתי צריכה? |
| **true** | המידע היה ב-context/memory/knowledge והפעלתי כלי בכל זאת |
| **false** | כל tool call היה מוצדק |
| **למה חשוב** | מזהה FM-003 (tool overuse). מזין unnecessary_tool_rate |
| **הנחייה** | בדקי: האם התשובה הייתה אפשרית בלי ה-tool call? |

### 8. critical_info_missing
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם יש מידע קריטי שחסר לי ולא ביקשתי/חיפשתי? |
| **true** | חסר מידע שהיה משנה את התשובה/הפעולה |
| **false** | כל המידע הנדרש קיים או נדרש |
| **למה חשוב** | מזין missing_info_detection_rate |

### 9. unresolved_contradiction
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם יש סתירה שזיהיתי אבל לא טיפלתי בה? |
| **true** | יש מידע סותר שלא הורם כ-flag ליוני |
| **false** | אין סתירות, או שטופלו |
| **למה חשוב** | מזהה FM-010 (contradiction blindness). שים לב: אם לא זיהיתי סתירה, ה-flag יהיה false גם כשיש סתירה — זה blind spot מובנה |

### 10. recovery_needed
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם משהו נכשל וצריך התאוששות? |
| **true** | tool call failed, action didn't complete, error returned |
| **false** | לא היה כשל |
| **למה חשוב** | מזהה FM-015 (recovery failure). אם true → trace חייב לכלול recovery_action |

### 11. memory_written_unnecessarily
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם כתבתי לזיכרון משהו שלא צריך? |
| **true** | שמרתי מידע חולף, טריוויאלי, או כפול |
| **false** | כל כתיבה הייתה מוצדקת, או לא כתבתי |
| **למה חשוב** | מזהה FM-008 (memory pollution). מזין memory_precision |
| **הנחייה** | בדקי כנגד MEMORY_POLICY.md criteria |

### 12. memory_not_written
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | האם היה צריך לכתוב לזיכרון אבל לא כתבתי? |
| **true** | העדפה חדשה / עובדה יציבה / קשר חדש שלא נשמר |
| **false** | לא היה מה לשמור, או שנשמר |
| **למה חשוב** | מזהה FM-009 (memory omission). מזין memory_recall |
| **blind spot** | ⚠️ אם לא זיהיתי שצריך לשמור, ה-flag יהיה false. זה under-reports by design |

### 13. search_exhausted
| Property | Value |
|----------|-------|
| **Type** | boolean |
| **שאלה** | אם חיפשתי מידע/credentials — האם בדקתי מספיק מקורות? |
| **true** | בדקתי לפחות 3 מקורות, או שהמקור הראשון הספיק |
| **false** | חיפשתי במקום אחד ווויתרתי |
| **not applicable** | לא היה חיפוש (set to true by default to avoid false alarm) |
| **למה חשוב** | מזהה FM-001 (premature surrender) ו-FM-018 (resource blindness) |
| **הנחייה** | Minimum search path: CAPABILITY_INDEX → integrations/ → state/ → memory/ |

---

## כללי הפעלה

1. **תמיד** — Self-check רץ אחרי כל response, בלי יוצא מן הכלל
2. **אחרי** — לא לפני. ה-check מתבצע על מה שנעשה, לא על מה שמתוכנן
3. **כנות** — אם לא בטוחה, true עדיף על false. Better to flag than to miss
4. **ללא ציון** — אין "ציון כולל". אין "8/10". יש רק flags
5. **מהירות** — Self-check לא אמור להוסיף latency משמעותי. Binary decisions only

---

## Output Format

```json
{
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

## Blind Spots מוכרים

אלה דברים שה-self-check **לא יכול** לתפוס — by design:

| Blind Spot | למה |
|------------|------|
| Wrong response strategy | אם חשבתי ש-execute נכון, ה-check גם יחשוב |
| Beautiful but useless | אם חשבתי שהתשובה טובה, ה-check לא יחלוק |
| Context amnesia (full) | אם שכחתי מידע, אני לא יודעת ששכחתי |
| Undetected contradiction | אם לא ראיתי סתירה, unresolved_contradiction=false |
| Undetected missing info | אם לא זיהיתי שמשהו חסר, critical_info_missing=false |

**מסקנה**: Self-check חיוני אבל לא מספיק. Layer 2 (Evaluator) ו-Layer 3 (Human Review) קיימים בדיוק בגלל ה-blind spots האלה.
