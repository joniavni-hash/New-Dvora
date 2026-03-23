# Agent Architecture v2 — Dvorah
<!-- Status: Active Plan -->
<!-- Created: 22.3.2026 -->
<!-- Replaces: AGENT_ARCHITECTURE.md (lean draft) -->

## עקרון מנחה
מערכת נשלטת, עקבית, דיבאגבילית. לא סוכנים חופשיים — orchestrator מרכזי שמנהל הכל.

## מה קיים כבר

| רכיב | סטטוס | מיקום |
|-------|--------|-------|
| Orchestrator (דבורה) | עובד, לא פורמלי | AGENTS.md + SOUL.md |
| Policies (14 קבצים) | עובדים | policies/ |
| Memory & State | מאורגנים | memory/, state/, MEMORY_INDEX.md |
| Group Agent (אודיה) | POC עובד | agents/group_agent_prompt.md |
| Integrations (10) | מחוברים | integrations/ |
| Runbooks (7) | פעילים | runbooks/ |
| Monitoring | בסיסי | scripts/metrics.py, health_check.py |

## ארכיטקטורת יעד

```
Yoni → Dvorah (Orchestrator)
         │
         ├── Core Services
         │   ├── PolicyEngine      — טוען ובודק policies לפני כל פעולה
         │   ├── ApprovalGate      — READ/DRAFT/SEND/MUTATE classification
         │   ├── ContextLoader     — מרכיב context רלוונטי לכל agent
         │   ├── TraceLogger       — מתעד כל החלטה ופעולה
         │   └── QALayer           — בדיקת איכות לפני שליחה
         │
         ├── Domain Agents (Phase 1)
         │   └── WhatsAppGroupAgent (אודיה)
         │
         ├── Domain Agents (Phase 2)
         │   ├── ResearchAgent
         │   └── SchedulingAgent
         │
         └── Domain Agents (Phase 3)
             ├── TravelAgent
             ├── LegalAgent
             └── DocumentAgent
```

### מה דבורה ממשיכה לעשות
- כל routing וזיהוי כוונה
- כל אישור פעולות חיצוניות
- כל הכתיבה ל-memory/state
- תקשורת ישירה עם יוני
- משימות פשוטות (תזכורות, חישובים, שאלות מהירות)

### מה מואצל
- ניתוח הודעות קבוצות → WhatsAppGroupAgent
- מחקר עמוק → ResearchAgent
- תיאום לוחות זמנים → SchedulingAgent
- מחקר נסיעות → TravelAgent
- ניתוח חוזים → LegalAgent
- סיכום מסמכים → DocumentAgent

---

## Core Services

### 1. Orchestrator Flow

כל בקשה עוברת את הזרימה הזו:

```
1. INTAKE      — קבלת הודעה/בקשה
2. CONTEXT     — ContextLoader טוען state/, memory/, policies רלוונטיים
3. CLASSIFY    — זיהוי כוונה + domain + סוג פעולה (READ/DRAFT/SEND/MUTATE)
4. POLICY      — PolicyEngine בודק constraints
5. ROUTE       — בחירת agent או טיפול ישיר
6. INVOKE      — הפעלת agent עם context מורכב
7. QA          — QALayer בודק את התוצר
8. APPROVE     — ApprovalGate — SEND/MUTATE דורשים אישור
9. EXECUTE     — ביצוע הפעולה
10. WRITEBACK  — עדכון memory/state אם רלוונטי
11. TRACE      — TraceLogger מתעד
```

**כלל:** דבורה לא מכילה לוגיקה דומיינית עמוקה. היא מנהלת flow.

### 2. PolicyEngine
**קובץ:** `core/policy_engine.md`

**אחריות:**
- טעינת policies רלוונטיים לפי domain + סוג פעולה
- בדיקת תאימות פעולה ל-policy
- החזרת constraints ל-agent (מה מותר, מה אסור, מה דורש אישור)

**איך עובד:** לא קוד — פרוטוקול. לפני כל הפעלת agent, דבורה:
1. מזהה domain (group, email, legal, travel...)
2. טוענת את ה-policies הרלוונטיים
3. מוסיפה את ה-constraints ל-task prompt של ה-agent

**למה לא קוד:** כי policies הם כבר קבצים. PolicyEngine הוא מיפוי: domain → אילו קבצים לטעון + אילו כללים לאכוף.

### 3. ApprovalGate
**קובץ:** `core/approval_gate.md`

**אחריות:**
- סיווג כל פעולה: `READ` / `DRAFT` / `SEND` / `MUTATE`
- `READ` — חופשי
- `DRAFT` — agent מכין, דבורה בודקת
- `SEND` — דורש אישור דבורה (ובמקרים רגישים — אישור יוני)
- `MUTATE` — שינוי state/memory — דבורה בלבד

**אכיפה:**
- כל agent מקבל ב-prompt: "אתה מחזיר DRAFT בלבד. לא שולח, לא כותב קבצים."
- דבורה בודקת כל output לפני ביצוע
- pending approvals מתועדים ב-`state/approvals/`

### 4. ContextLoader
**קובץ:** `core/context_loader.md`

**אחריות:**
- לפי domain + task, מרכיב את ה-context שה-agent צריך
- טוען רק מה שרלוונטי (לא הכל)

**מיפוי:**
| Domain | קבצים לטעון |
|--------|-------------|
| group | KNOWN_GROUPS, GROUP_MEMORY, GROUP_MEMBERS, GROUP_BEHAVIOR_POLICY |
| email | OUTLOOK integration, OPEN_TASKS, PRIVACY_POLICY |
| legal | EXTERNAL_ACTIONS_POLICY, relevant docs |
| travel | relevant bookings, preferences from memory |
| fitness | state/fitness_tracker.md |

### 5. TraceLogger
**קובץ:** `core/trace_logger.md`
**State:** `state/traces/`

**מתעד לכל פעולת agent:**
- timestamp
- trigger (מה הפעיל)
- route decision (איזה agent נבחר, למה)
- loaded context (מה נטען)
- agent output (summary)
- approval status
- action taken
- memory/state writes

**למה חשוב:** בלי trace, כשמשהו נשלח בטעות — אין דרך לדעת למה. עם trace — אפשר לדבג ולתקן.

### 6. QALayer
**קובץ:** `core/qa_layer.md`

**בדיקות לפני כל שליחה:**
- factual fit — האם העובדות נכונות?
- style fit — האם הטון מתאים ליעד?
- policy fit — האם עומד ב-policies?
- risk check — סיכון פרטיות, מבוכה, conflict?
- missing context — האם חסר מידע קריטי?
- wrong tool — האם ה-agent השתמש בכלי לא נכון?

**כשל בכל בדיקה → הפעולה נעצרת ודבורה מחליטה.**

---

## Agent Contract — חוזה אחיד

כל agent עובד לפי אותו interface:

```
INPUT:
  - task: מה צריך לעשות
  - context: קבצים + מידע רלוונטי (מ-ContextLoader)
  - constraints: כללים מ-PolicyEngine
  - outputFormat: מבנה ה-JSON הנדרש

OUTPUT:
  - decision: מה ה-agent מחליט (reply/no-reply, draft, summary...)
  - confidence: 0-1
  - reasoning: למה
  - draft: התוצר (טקסט, סיכום, ניתוח...)
  - memoryDelta: מה לזכור (דבורה מחליטה אם לכתוב)
  - stateDelta: מה לעדכן ב-state (דבורה מחליטה)
  - qaResult: self-check של ה-agent
```

**כללי ברזל לכל agent:**
1. לא שולח הודעות ישירות
2. לא כותב קבצים
3. לא ניגש ל-memory_search (דבורה מספקת context)
4. לא מפעיל sub-agents משלו
5. מחזיר JSON בלבד

---

## Phase 1 — Core + WhatsAppGroupAgent

### מה לבנות
| קובץ | סוג | תיאור |
|-------|------|--------|
| `core/orchestrator_flow.md` | חדש | זרימת ה-orchestrator (10 שלבים) |
| `core/policy_engine.md` | חדש | מיפוי domain → policies |
| `core/approval_gate.md` | חדש | סיווג פעולות + כללי אישור |
| `core/context_loader.md` | חדש | מיפוי domain → context files |
| `core/trace_logger.md` | חדש | פורמט trace + אחסון |
| `core/qa_layer.md` | חדש | בדיקות QA |
| `core/agent_contract.md` | חדש | interface אחיד לכל agent |
| `agents/group_agent_prompt.md` | עדכון | התאמה ל-contract החדש |
| `state/traces/` | חדש | תיקיית traces |
| `state/approvals/` | חדש | pending approvals |

### מה לא לבנות עכשיו
- ❌ TravelAgent, LegalAgent, DocumentAgent (Phase 3)
- ❌ ResearchAgent, SchedulingAgent (Phase 2)
- ❌ MemoryService/StateService נפרדים (דבורה ממשיכה לנהל ישירות)
- ❌ מבנה תיקיות מורכב per-agent (skeleton ריק לא שווה כלום)
- ❌ learning/optimization layer (מוקדם מדי)
- ❌ TriggerScorer עם 12 features (אודיה כבר עושה scoring — לשפר בהדרגה)

### למה לא MemoryService/StateService נפרדים
כי memory ו-state הם קבצים. דבורה קוראת וכותבת אותם. להוסיף שכבה ביניהם עכשיו זה abstraction בלי תועלת. אם יגיעו 5+ agents שכותבים — אז כן.

### למה לא skeletons ריקים
כי הם מתיישנים לפני שמשתמשים בהם. agent נבנה כשיש צורך אמיתי — לא לפני.

---

## Phase 2 — ResearchAgent + SchedulingAgent

**תנאי כניסה:** Phase 1 מושלם, 20+ הודעות קבוצה עברו דרך המערכת.

### ResearchAgent
- שאלה מורכבת → דבורה מזהה → spawn עם context
- חוקר ברקע (web, docs, APIs)
- מחזיר: סיכום + מקורות + confidence + שאלות פתוחות
- דבורה בודקת → מעבירה ליוני

### SchedulingAgent
- בקשות תיאום (פגישות, תזכורות, לו"ז)
- ניגש ליומן דרך integrations
- מחזיר draft — דבורה מאשרת

---

## Phase 3 — TravelAgent + LegalAgent + DocumentAgent

**תנאי כניסה:** Phase 2 מושלם, contracts מוכחים.

**TravelAgent:** איסוף אילוצים, השוואת חלופות, draft itinerary. לעולם לא מזמין בעצמו.

**LegalAgent:** סקירת חוזים, זיהוי סיכונים, סיכום structured. תמיד DRAFT-first, תמיד מציין uncertainty.

**DocumentAgent:** סיכום מסמכים ארוכים, extraction, השוואה.

---

## Success Criteria

### Phase 1 done when:
- [ ] Core services מתועדים ופעילים
- [ ] כל הודעת קבוצה עוברת orchestrator flow
- [ ] Traces נכתבים לכל פעולה
- [ ] ApprovalGate מסווג כל פעולה
- [ ] 20+ הודעות קבוצה עברו דרך המערכת
- [ ] אפס הודעות נשלחו בלי אישור דבורה
- [ ] עלות per message < $0.01

### Phase 2 done when:
- [ ] ResearchAgent השלים 5+ משימות
- [ ] איכות שווה או טובה יותר מדבורה inline
- [ ] זמן תגובה מהיר יותר (parallel)

---

## סיכונים

| סיכון | הפחתה |
|--------|--------|
| Agent שולח ישירות | prompt + ApprovalGate + trace |
| Agent נותן תשובה שגויה | QALayer + דבורה בודקת |
| עלות מתפוצצת | sonnet כברירת מחדל, תקציב per-agent |
| Latency גבוה | parallel execution |
| Context גדול מדי | ContextLoader טוען רק רלוונטי |
| Over-engineering | לא בונים מה שלא צריך עכשיו |
