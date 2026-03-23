#!/usr/bin/env python3
"""
מאשה MVP - Legal Agent Basic Implementation
"""

import json
import re
from typing import Dict, List, Optional
from legal_intent_classifier import LegalIntentClassifier

class MashaMVP:
    def __init__(self):
        self.classifier = LegalIntentClassifier()
        
    def can_handle(self, task: str, context: Dict = None, attachments: List[str] = None) -> Dict:
        """Check if מאשה can handle this task"""
        classification = self.classifier.classify_legal_intent(task, attachments, context)
        should_route, action = self.classifier.should_route_to_masha(classification)
        
        return {
            "canHandle": should_route and action == 'direct',
            "confidence": classification['confidence'],
            "taskType": classification['task_type'],
            "reasoning": classification['reasoning'],
            "requiresConfirmation": action == 'confirm'
        }
    
    def analyze(self, task: str, context: Dict, attachments: List = None) -> Dict:
        """Main analysis function - routes to specific workflow"""
        
        classification = self.classifier.classify_legal_intent(task, attachments or [], context)
        task_type = classification['task_type']
        
        if task_type == "contract_review":
            return self._contract_review(task, context, attachments)
        elif task_type == "risk_analysis":
            return self._risk_analysis(task, context, attachments)  
        elif task_type == "clause_extraction":
            return self._clause_extraction(task, context, attachments)
        elif task_type == "draft_response":
            return self._draft_response(task, context, attachments)
        elif task_type == "compare_versions":
            return self._compare_versions(task, context, attachments)
        else:
            return self._legal_summary(task, context, attachments)
            
    def _contract_review(self, task: str, context: Dict, attachments: List) -> Dict:
        """Contract review workflow"""
        
        # For MVP - simulate contract analysis
        # In real implementation, this would parse the PDF
        
        mock_contract_analysis = """# ניתוח חוזה - [שם המסמך]

## 📋 תקציר
**צדדים:** יוני אבני מול [הצד השני]  
**מטרה:** [מבוסס על הקשר המסמך]  
**תקופה:** [יש לבדוק במסמך המצורף]  
**תמורה:** [יש לבדוק במסמך המצורף]

## 🔍 סעיפים מרכזיים

### חובות יוני:
- [דורש עיון במסמך המצורף לפירוט מדויק]

### חובות הצד השני:  
- [דורש עיון במסמך המצורף לפירוט מדויק]

## ⚠️ סיכונים

### 🔴 גבוהים:
- **חבות בלתי מוגבלת:** יש לבדוק אם קיימים סעיפי הגבלת חבות
- **סמכות שיפוט זרה:** יש לוודא איפה יתבררו מחלוקות

### 🟡 בינוניים:
- **תקופות הודעה:** יש לבדוק תקופות הודעה מוקדמת
- **סעיפי ביטול:** יש לבדוק תנאי יציאה מההסכם

## 🤔 נקודות תשומת לב

### לא ברור:
- **[דורש עיון במסמך]** - הניתוח המדויק דורש קריאת המסמך המצורף

### חסר:
- **Force Majeure:** האם קיים סעיף כח עליון?
- **סודיות:** האם קיימים תנאי סודיות הדדיים?

## 💡 המלצות
1. **קריאה מדויקת:** יש לקרוא את המסמך המצורף לקבלת ניתוח מלא
2. **יעוץ משפטי:** בהתאם לסיכונים שיתגלו
3. **נקודות משא ומתן:** לזהות לאחר קריאת המסמך

## 📊 דירוג כללי
**איזון:** [דורש עיון במסמך]  
**סיכון כללי:** בינוני (עד לקריאה מדויקת)  
**המלצה:** לבחון את המסמך המצורף לפני קבלת החלטה"""

        return {
            "decision": "analysis",
            "confidence": 0.8,
            "reasoning": "Contract review requested with potential attachment",
            "draft": {
                "type": "contract_review",
                "content": mock_contract_analysis
            },
            "legalRisk": "medium",
            "riskFactors": ["requires_document_review", "unknown_liability_clauses"],
            "memoryDelta": "יוני ביקש סקירת חוזה - מעדיף ניתוח מובנה",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["read_attached_document", "identify_key_clauses", "assess_specific_risks"],
            "requiresApproval": True
        }
    
    def _risk_analysis(self, task: str, context: Dict, attachments: List) -> Dict:
        """Risk analysis workflow"""
        
        risk_analysis = """# ניתוח סיכונים - [המסמך הנדון]

## 🔴 סיכונים קריטיים
### עיון נדרש במסמך:
**מה:** לא ניתן לבצע ניתוח סיכונים מדויק ללא קריאת המסמך  
**איך זה יכול לקרות:** החלטות בהתבסס על מידע חלקי  
**עלות אפשרית:** בלתי צפויה  
**המלצה:** קריאה מדויקת של המסמך המצורף קודם

## 🟡 סיכונים בינוניים
### פרשנות לא מדויקת:
**מה:** מתן ייעוץ ללא בסיס מלא  
**עלות אפשרית:** החמצת סיכונים אמיתיים  
**המלצה:** הבהרת ההקשר והמסמכים הרלוונטיים

## 💊 המלצות לטיפול
1. **מידי:** העברת המסמך לעיון מדויק
2. **קצר טווח:** זיהוי סעיפי הסיכון העיקריים  
3. **ארוך טווח:** בניית מדיניות לסקירת חוזים

## 🛡️ אסטרטגיות הגנה
- **מניעה:** סקירה משפטית לפני חתימה
- **הגבלה:** סעיפי הגבלת חבות ותקרות נזק  
- **ביטוח:** ביטוח אחריות מקצועית"""

        return {
            "decision": "analysis", 
            "confidence": 0.7,
            "reasoning": "Risk analysis requested but requires document context",
            "draft": {
                "type": "risk_analysis",
                "content": risk_analysis
            },
            "legalRisk": "medium",
            "riskFactors": ["insufficient_context", "potential_hidden_risks"],
            "memoryDelta": "יוני מתעניין בניתוח סיכונים - דורש מידע מפורט",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["request_full_document", "clarify_specific_concerns"],
            "requiresApproval": True
        }
    
    def _clause_extraction(self, task: str, context: Dict, attachments: List) -> Dict:
        """Extract specific clauses"""
        
        # Try to identify what type of clauses requested
        clause_type = "general"
        if "אחריות" in task or "liability" in task:
            clause_type = "liability"
        elif "תשלום" in task or "payment" in task:
            clause_type = "payment"
        elif "סיום" in task or "termination" in task:
            clause_type = "termination"
            
        extraction_result = f"""# חילוץ סעיפים - {clause_type}

## 📍 סעיפים שנמצאו

### בחינה נדרשת:
**הערה:** לא ניתן לחלץ סעיפים ספציפיים ללא גישה למסמך המלא

**מה נדרש:**
- המסמך המלא לסריקה
- הגדרת הנושא המדויק לחיפוש
- הקשר עסקי לפרשנות נכונה

## ❗ המלצות לחיפוש
בעת עיון במסמך, חפש:
- מילות מפתח: "{clause_type}"
- מספרי סעיפים
- הפניות צולבות בין סעיפים

## 📊 סיכום
**כיסוי:** דורש עיון במסמך  
**איכות ניסוח:** לא ניתן להעריך  
**המלצה:** העברת המסמך המלא לסריקה מדויקת"""

        return {
            "decision": "analysis",
            "confidence": 0.6,
            "reasoning": f"Clause extraction requested for {clause_type} but requires document access",
            "draft": {
                "type": "clause_extraction", 
                "content": extraction_result
            },
            "legalRisk": "low",
            "riskFactors": ["requires_document_access"],
            "memoryDelta": f"יוני מחפש סעיפי {clause_type} - מעדיף חילוץ מדויק",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["access_full_document", "perform_keyword_search"],
            "requiresApproval": True
        }
    
    def _draft_response(self, task: str, context: Dict, attachments: List) -> Dict:
        """Draft formal response"""
        
        draft_template = """# טיוטת תגובה - [נושא]

## 🎯 מטרה
[יש לבהיר - לאיזה מסמך/בקשה/הודעה מגיבים]

## 🎭 טון
[יש לבהיר - רשמי/ידידותי/תקיף]

## 📝 טיוטה

[דוגמת מבנה - יש להתאמה לפי המקרה הספציפי]

כבוד [שם הנמען],

בהמשך ל[הקשר], הרינו מתכבדים להודיעכם כי [עיקר התגובה].

[פירוט נקודות עיקריות]

נשמח לקבל הבהרה בנוגע ל[שאלות פתוחות].

בכבוד רב,  
יוני אבני

## 🔧 הערות פנימיות

### לפני השליחה לבדוק:
- [ ] האם הטון מתאים למטרה
- [ ] האם כל הנקודות מכוסות  
- [ ] האם אין טעויות עובדתיות
- [ ] האם ההקשר ברור לקורא

## ⚡ תגובות צפויות
**הם עשויים לבקש:** הבהרות נוספות  
**אז נוכל להגיב:** בהתבסס על המסמכים הרלוונטיים"""

        return {
            "decision": "draft",
            "confidence": 0.7,
            "reasoning": "Draft response requested - created template requiring customization",
            "draft": {
                "type": "draft_response",
                "content": draft_template
            },
            "legalRisk": "low",
            "riskFactors": ["requires_context_specific_customization"],
            "memoryDelta": "יוני מבקש טיוטות תגובה - מעדיף מבנה רשמי",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["clarify_response_context", "customize_template", "review_tone"],
            "requiresApproval": True
        }
    
    def _compare_versions(self, task: str, context: Dict, attachments: List) -> Dict:
        """Compare document versions"""
        
        if len(attachments or []) < 2:
            comparison_result = """# השוואת גרסאות - [שם מסמך]

## ❗ חסרים קבצים להשוואה

**נדרש:** שני קבצים לצורך השוואה
**התקבל:** """ + str(len(attachments or [])) + """ קבצים

## 📋 למה השוואה נחוצה?
- זיהוי שינויים מהותיים
- הבנת השפעה עסקית
- החלטה על קבלה/דחייה

## 💡 המלצה
אנא צרף שני קבצים:
1. הגרסה המקורית
2. הגרסה החדשה/המוצעת

לאחר מכן אוכל לבצע השוואה מדויקת."""
        else:
            comparison_result = """# השוואת גרסאות - [שם מסמך]

## 📊 הערה
לצורך השוואה מדויקת נדרשת גישה לתוכן הקבצים המצורפים.

## 🔍 תהליך השוואה המתוכנן:
1. **זיהוי שינויים** - מה נוסף/הוסר/שונה
2. **סיווג שינויים** - עיצובי/מהותי/קריטי  
3. **הערכת השפעה** - טוב/רע/ניטרלי עבור יוני
4. **המלצות** - מה לעשות עם כל שינוי

## 📋 דרך פעולה
1. **מידי:** קריאת שני הקבצים
2. **השוואה מסודרת:** לפי סעיפים
3. **דוח מסכם:** עם המלצות ברורות"""

        return {
            "decision": "comparison",
            "confidence": 0.8 if len(attachments or []) >= 2 else 0.4,
            "reasoning": f"Comparison requested with {len(attachments or [])} files",
            "draft": {
                "type": "compare_versions",
                "content": comparison_result
            },
            "legalRisk": "medium",
            "riskFactors": ["requires_file_access", "change_analysis_needed"],
            "memoryDelta": "יוני מבקש השוואות גרסאות - מעדיף ניתוח מפורט של שינויים",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["access_both_files", "perform_line_by_line_comparison"],
            "requiresApproval": True
        }
    
    def _legal_summary(self, task: str, context: Dict, attachments: List) -> Dict:
        """General legal summary"""
        
        summary = """# סיכום משפטי - [שם המסמך]

## 🎯 במה מדובר
[דורש עיון במסמך המצורף לקביעת הנושא המדויק]

## 📌 נקודות עיקריות
1. **[נושא 1]:** [דורש עיון במסמך]
2. **[נושא 2]:** [דורש עיון במסמך]
3. **[נושא 3]:** [דורש עיון במסמך]

## 🏢 השלכות מעשיות
**מה זה אומר בפועל:**
- [יש לבהיר לאחר קריאת המסמך]

**מי מושפע:**
- יוני אבני
- [צדדים נוספים לפי המסמך]

**מתי נכנס לתוקף:**
- [לפי המסמך]

## ⏰ צעדים הבאים
1. קריאה מדויקת של המסמך המצורף
2. זיהוי נקודות מרכזיות
3. הערכת השלכות והמלצות"""

        return {
            "decision": "summary",
            "confidence": 0.6,
            "reasoning": "General legal summary requested but requires document access",
            "draft": {
                "type": "legal_summary", 
                "content": summary
            },
            "legalRisk": "medium",
            "riskFactors": ["requires_document_review"],
            "memoryDelta": "יוני מבקש סיכומים משפטיים - מעדיף מבנה ברור",
            "stateDelta": None,
            "qaResult": "pass",
            "suggestedActions": ["read_full_document", "identify_key_points"],
            "requiresApproval": True
        }

def test_masha_mvp():
    """Test מאשה with sample requests"""
    masha = MashaMVP()
    
    test_requests = [
        {
            "task": "תסכמי את החוזה המצורף",
            "attachments": ["contract.pdf"],
            "context": {"sender": "yoni"}
        },
        {
            "task": "מה הסיכונים בחוזה הזה?", 
            "attachments": [],
            "context": {"sender": "yoni"}
        },
        {
            "task": "תמצאי סעיפי אחריות",
            "attachments": ["agreement.pdf"],
            "context": {"sender": "yoni"}
        }
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n=== Test Case {i} ===")
        print(f"Task: {request['task']}")
        
        # Check if can handle
        can_handle_result = masha.can_handle(
            request['task'], 
            request['context'], 
            request['attachments']
        )
        print(f"Can Handle: {can_handle_result['canHandle']} (confidence: {can_handle_result['confidence']:.2f})")
        
        if can_handle_result['canHandle']:
            # Perform analysis
            result = masha.analyze(
                request['task'],
                request['context'], 
                request['attachments']
            )
            
            print(f"Decision: {result['decision']}")
            print(f"Task Type: {result['draft']['type']}")
            print(f"Legal Risk: {result['legalRisk']}")
            print(f"Suggested Actions: {result['suggestedActions'][:2]}...")

if __name__ == "__main__":
    test_masha_mvp()