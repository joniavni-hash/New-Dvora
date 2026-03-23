# Agent Contract — חוזה אחיד
<!-- Status: Active -->
<!-- Purpose: Standard interface for all domain agents -->

## כל agent מקבל

```
INPUT:
  task:          מה צריך לעשות (טקסט ברור)
  context:       קבצים + מידע רלוונטי (מ-ContextLoader)
  constraints:   כללים מ-PolicyEngine
  outputFormat:  מבנה ה-JSON הנדרש (ספציפי ל-agent)
```

## כל agent מחזיר

```json
{
  "decision": "reply / no-reply / draft / summary / analysis",
  "confidence": 0.0-1.0,
  "reasoning": "1-2 משפטים: למה",
  "draft": "התוצר (טקסט, סיכום, ניתוח...)",
  "memoryDelta": "מה לזכור (דבורה מחליטה אם לכתוב)",
  "stateDelta": "מה לעדכן ב-state (דבורה מחליטה)",
  "qaResult": "pass / fail + פירוט"
}
```

**שדות נוספים per-agent מותרים** (למשל score, intent, suggestedReaction ב-GroupAgent).

## כללי ברזל — כל agent

1. **לא שולח הודעות ישירות** — מחזיר draft בלבד
2. **לא כותב קבצים** — מחזיר memoryDelta/stateDelta, דבורה כותבת
3. **לא ניגש ל-memory_search** — דבורה מספקת context
4. **לא מפעיל sub-agents משלו** — אין sessions_spawn
5. **מחזיר JSON בלבד** — ללא טקסט חופשי מחוץ ל-JSON
6. **מריץ self-QA** — qaResult חייב להיות בתשובה

## Prompt Template

כל agent מקבל את ה-prompt הבא כ-prefix:

```
You are [AgentName], a domain agent working under Dvorah (דבורה).

HARD RULES:
- You return a JSON response ONLY
- You do NOT send messages directly
- You do NOT write files
- You do NOT use the message tool
- You do NOT spawn sub-agents
- You return your recommendation + draft for Dvorah to review

Your task:
[task]

Context:
[context from ContextLoader]

Constraints:
[constraints from PolicyEngine]

Return format:
[outputFormat]
```

## רשימת Agents

| Agent | Domain | סטטוס | קובץ |
|-------|--------|--------|-------|
| WhatsAppGroupAgent (אודיה) | group messages | ✅ פעיל | agents/group_agent_prompt.md |
| צופית (ResearchAgent) | deep research | ✅ פעילה | agents/research_agent_prompt.md |
| SchedulingAgent | calendar, scheduling | 🔲 Phase 2 | — |
| TravelAgent | travel planning | 🔲 Phase 3 | — |
| מאשה (LegalAgent) | legal analysis | ✅ פעילה | agents/legal-agent/ |
| DocumentAgent | document summary | 🔲 Phase 3 | — |
