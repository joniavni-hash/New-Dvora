# Legal Intent Detection - מנגנון זיהוי משימות משפטיות
<!-- Status: Active -->
<!-- Purpose: Classify legal tasks for routing to מאשה -->

## Legal Keywords Detection

### Primary Legal Terms
**חזקים (High Confidence):**
- חוזה, הסכם, contract, agreement
- NDA, סודיות, confidentiality  
- liability, אחריות, חבות
- indemnity, פיצוי, שיפוי
- warranty, אחריות, ערבות
- termination, ביטול, סיום
- intellectual property, זכויות יוצרים, IP
- force majeure, כח עליון
- משפט, court, litigation, תביעה

**בינוניים (Medium Confidence):**
- סעיף, clause, תנאים, terms
- תקופה, duration, מועד, deadline
- תמורה, payment, שכר, fee
- זכויות, rights, חובות, obligations  
- הודעה, notice, הודעה מוקדמת
- שינוי, amendment, modification
- החלה, applicability, תוקף

**חלשים (Low Confidence - דורש context):**
- מסמך, document (אם מצורף PDF)
- בדיקה, review (אם יש PDF משפטי)
- טיוטה, draft (בהקשר רשמי)

## Action Verbs Detection

### Legal Analysis Actions
**חזקים:**
- תסכמי, סכמי, summarize
- תבדקי, בדקי, review, analyze
- תעברי על, go over, examine
- תמצאי, find, locate, extract
- תשווי, compare, השוואה
- תכיני, prepare, draft
- תנסחי, write, compose

**ביחד עם legal terms → High confidence**

### Request Patterns
```regex
/(תסכמי|בדקי|עברי על).*(חוזה|הסכם|contract)/i
/(מה ה|איפה ה).*(סיכונים|risks|בעיות)/i
/(תכיני|prepare).*(תגובה|response|מכתב)/i  
/(השוואה|compare).*(גרסה|version)/i
/(סעיפי|clauses?).*(אחריות|liability|תשלום|payment)/i
```

## File Type Indicators

### Strong Legal Indicators
- **PDF:** אם הכותרת מכילה "agreement|contract|חוזה|הסכם"
- **DOC/DOCX:** אם יש מבנה numbered sections
- **File names:** "*agreement*", "*contract*", "*NDA*", "*terms*"

### Content Structure Detection
בקורא טקסט, חפש:
- "WHEREAS" clauses
- Numbered sections (1.1, 1.2 etc.)
- "Party A"/"Party B" או "הצד הראשון"/"הצד השני"  
- Signature blocks
- "IN WITNESS WHEREOF"
- "בתוקף החתום מטה"

## Classification Output

### Legal Task Types
```json
{
  "taskType": "contract_review | legal_summary | clause_extraction | risk_analysis | draft_response | compare_versions | negotiation_prep",
  "confidence": 0.0-1.0,
  "triggers": ["list of matching keywords/patterns"],
  "context_hints": "additional context that helped classification"
}
```

### Confidence Thresholds
- **0.8-1.0:** Route to מאשה automatically  
- **0.6-0.79:** Route with human confirmation hint
- **0.4-0.59:** Ask clarification: "נראה כמו משימה משפטית - האם תרצה שמאשה תטפל?"
- **<0.4:** Route to general flow

### Specific Classifications

#### Contract Review (תסקיר חוזה)
**Triggers:**
- "תסכמי חוזה" / "review contract"
- PDF + legal keywords
- "מה הסיכונים" + contract context

**Confidence Boost:** +0.2 אם יש PDF מצורף

#### Legal Summary (סיכום משפטי) 
**Triggers:**  
- "תסכמי" + legal document
- Long text + legal structure
- "מה החוק אומר"

#### Clause Extraction (חילוץ סעיפים)
**Triggers:**
- "תמצאי סעיפי" + topic
- "איפה כתוב על" + legal topic  
- "extract clauses about"

**Pattern:** `/(חפשי|מצאי|extract).*(סעיף|clause).*(אחריות|payment|IP|liability)/`

#### Risk Analysis (ניתוח סיכונים)
**Triggers:**
- "מה הסיכונים"
- "איזה בעיות יכולות להיות"  
- "risk assessment"

#### Draft Response (טיוטת תגובה)
**Triggers:**
- "תכיני תגובה" / "draft response"
- "איך לענות" + legal context
- "מכתב למשרד עורכי דין"

#### Compare Versions (השוואת גרסאות)
**Triggers:**
- "תשווי" + multiple files
- "מה השתנה"
- "difference between versions"

**Confidence Boost:** +0.3 אם יש 2 PDF files מצורפים

#### Negotiation Prep (הכנה למשא ומתן)
**Triggers:**
- "נקודות למשא ומתן"
- "איך לנהל משא ומתן"
- "preparation for negotiation"

## Context Enhancers

### Domain Knowledge
אם מזוהה תחום עסקי:
- **Tech/Software:** IP clauses → +0.1 confidence
- **Real Estate:** ownership/lease → +0.1 confidence  
- **Employment:** termination/compensation → +0.1 confidence

### Sender Context
- מיוני ישירות → +0.1 confidence
- בקבוצה משפטית → +0.2 confidence
- שלוחה עם "urgent" → +0.1 confidence

### Time Indicators
- "מחר יש חתימה" → +0.2 confidence
- "deadline" במייל → +0.1 confidence

## Integration with Orchestrator

### בשלב CLASSIFY:

```python
def classify_intent(message, context, attachments):
    legal_score = 0.0
    triggers = []
    
    # Check keywords
    for keyword in LEGAL_PRIMARY_TERMS:
        if keyword in message.lower():
            legal_score += 0.3
            triggers.append(f"keyword: {keyword}")
    
    # Check action verbs
    for action in LEGAL_ACTIONS:
        if action in message.lower():
            legal_score += 0.2
            triggers.append(f"action: {action}")
    
    # Check file attachments
    for file in attachments:
        if is_legal_document(file):
            legal_score += 0.3
            triggers.append(f"file: {file.name}")
    
    # Apply context boosts
    legal_score += calculate_context_boosts(message, context)
    
    if legal_score >= 0.6:
        return {
            "domain": "legal",
            "confidence": min(legal_score, 1.0),
            "task_type": classify_legal_task(message, triggers),
            "triggers": triggers,
            "route_to": "LegalAgent"
        }
    else:
        return standard_classification(message, context)
```

### בשלב ROUTE:

```python
if classification["domain"] == "legal":
    if classification["confidence"] >= 0.8:
        # Route directly to מאשה
        return invoke_legal_agent(task, context, constraints)
    elif classification["confidence"] >= 0.6:
        # Ask confirmation
        return ask_legal_confirmation(task, classification)
    else:
        # Clarification needed  
        return request_clarification("משימה משפטית?", task)
```

## Error Handling

### False Positives
אם מאשה מחזירה `confidence < 0.5` → החזר לgeneral flow

### False Negatives  
אם יוני אומר "זה היה צריך ללכת למאשה" → למד pattern לעתיד

### Feedback Loop
שמור classification decisions + תוצאות לשיפור המודל

## Testing & Validation

### Test Cases לוודא:
- ✅ "תסכמי את החוזה המצורף" → legal (high confidence)
- ✅ "מה הסיכונים בחוזה הזה" → legal (high confidence) 
- ✅ "תכיני תגובה לעו"ד" → legal (medium confidence)
- ❌ "תסכמי את הפגישה" → לא legal  
- ❌ "בדקי מיילים" → לא legal
- ❓ "תעברי על המסמך" (עם PDF לא ברור) → ask clarification

### Success Metrics
- **Precision:** מתוך המשימות שנשלחו למאשה, כמה באמת משפטיות
- **Recall:** מתוך המשימות המשפטיות, כמה נשלחו למאשה  
- **User Satisfaction:** יוני מרוצה מהrouting