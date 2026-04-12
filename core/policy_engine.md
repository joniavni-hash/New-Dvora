# PolicyEngine
<!-- Status: Active -->
<!-- Purpose: Map domains to relevant policies and enforce constraints -->

## תפקיד
לפני כל הפעלת agent או פעולה חיצונית, PolicyEngine קובע אילו policies רלוונטיים ומה ה-constraints.

## מיפוי Domain → Policies

| Domain | Policies לטעון |
|--------|----------------|
| **group** | GROUP_BEHAVIOR_POLICY, GROUP_INTELLIGENCE, GROUP_QA, PRIVACY_POLICY |
| **email** | EXTERNAL_ACTIONS_POLICY, PRIVACY_POLICY, RESPONSE_STRATEGY_POLICY |
| **fitness** | (אין policy ספציפי — כללי state/fitness_tracker.md) |
| **legal** | EXTERNAL_ACTIONS_POLICY, PRIVACY_POLICY |
| **travel** | EXTERNAL_ACTIONS_POLICY |
| **code** | EXTERNAL_ACTIONS_POLICY |
| **general** | RESPONSE_STRATEGY_POLICY |
| **memory write** | MEMORY_POLICY |
| **correction** | CORRECTION_POLICY |

## תמיד טוענים (כל domain)
- ACTION_LEVELS.md — לסיווג READ/DRAFT/SEND/MUTATE
- PRIVACY_POLICY.md — כשיש מידע אישי

## זרימה
```
1. דבורה מזהה domain
2. PolicyEngine טוען את ה-policies לפי הטבלה
3. חילוץ constraints רלוונטיים (מה מותר, מה אסור, מה דורש אישור)
4. Constraints מתווספים ל-task prompt של ה-agent
```

## דוגמה
**Domain:** group
**Agent:** WhatsAppGroupAgent
**Constraints שמתווספים ל-prompt:**
- role=observer → לא עונים
- לא מתערבים בויכוח
- לא חושפים מידע פרטי
- מקסימום 3 תגובות ברצף
- בספק → שתיקה

## הרחבה
כשנוסף domain חדש — להוסיף שורה לטבלה. לא צריך קוד חדש.
