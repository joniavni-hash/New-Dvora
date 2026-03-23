#!/usr/bin/env python3
"""
Legal Intent Classification - מזהה משימות משפטיות לmאשה
"""

import re
import json
from typing import Dict, List, Tuple, Optional

class LegalIntentClassifier:
    
    def __init__(self):
        # Primary legal terms - high confidence
        self.primary_legal_terms = [
            'חוזה', 'הסכם', 'contract', 'agreement',
            'nda', 'סודיות', 'confidentiality',
            'liability', 'אחריות', 'חבות',
            'indemnity', 'פיצוי', 'שיפוי',
            'warranty', 'ערבות',
            'termination', 'ביטול', 'סיום',
            'intellectual property', 'זכויות יוצרים', 'ip',
            'force majeure', 'כח עליון',
            'משפט', 'court', 'litigation', 'תביעה'
        ]
        
        # Secondary legal terms - medium confidence  
        self.secondary_legal_terms = [
            'סעיף', 'clause', 'תנאים', 'terms',
            'תקופה', 'duration', 'מועד', 'deadline',
            'תמורה', 'payment', 'שכר', 'fee',
            'זכויות', 'rights', 'חובות', 'obligations',
            'הודעה', 'notice', 'הודעה מוקדמת',
            'שינוי', 'amendment', 'modification',
            'החלה', 'applicability', 'תוקף'
        ]
        
        # Legal action verbs
        self.legal_actions = [
            'תסכמי', 'סכמי', 'summarize',
            'תבדקי', 'בדקי', 'review', 'analyze', 
            'תעברי על', 'go over', 'examine',
            'תמצאי', 'find', 'locate', 'extract',
            'תשווי', 'compare', 'השוואה',
            'תכיני', 'prepare', 'draft',
            'תנסחי', 'write', 'compose'
        ]
        
        # Legal file patterns
        self.legal_file_patterns = [
            r'.*agreement.*\.(pdf|docx?)',
            r'.*contract.*\.(pdf|docx?)', 
            r'.*nda.*\.(pdf|docx?)',
            r'.*terms.*\.(pdf|docx?)',
            r'.*חוזה.*\.(pdf|docx?)',
            r'.*הסכם.*\.(pdf|docx?)'
        ]
        
        # Legal request patterns
        self.legal_patterns = [
            r'(תסכמי|בדקי|עברי על).*(חוזה|הסכם|contract)',
            r'(מה ה|איפה ה).*(סיכונים|risks|בעיות)', 
            r'(תכיני|prepare).*(תגובה|response|מכתב)',
            r'(השוואה|compare).*(גרסה|version)',
            r'(סעיפי|clauses?).*(אחריות|liability|תשלום|payment)',
            r'(נקודות|points).*(משא.*ומתן|negotiation)'
        ]

    def classify_legal_intent(self, message: str, attachments: List[str] = None, context: Dict = None) -> Dict:
        """
        Classify if message is a legal task and what type
        
        Returns:
        {
            "is_legal": bool,
            "confidence": float,
            "task_type": str,
            "triggers": List[str],
            "reasoning": str
        }
        """
        if attachments is None:
            attachments = []
        if context is None:
            context = {}
            
        legal_score = 0.0
        triggers = []
        task_type = "unknown"
        
        message_lower = message.lower()
        
        # Check primary legal terms
        for term in self.primary_legal_terms:
            if term.lower() in message_lower:
                legal_score += 0.3
                triggers.append(f"primary_term: {term}")
                
        # Check secondary legal terms
        for term in self.secondary_legal_terms:
            if term.lower() in message_lower:
                legal_score += 0.15
                triggers.append(f"secondary_term: {term}")
                
        # Check legal action verbs
        for action in self.legal_actions:
            if action.lower() in message_lower:
                legal_score += 0.2
                triggers.append(f"action: {action}")
                
        # Check legal patterns
        for pattern in self.legal_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                legal_score += 0.25
                triggers.append(f"pattern: {pattern[:20]}...")
                
        # Check attachments
        for attachment in attachments:
            for pattern in self.legal_file_patterns:
                if re.match(pattern, attachment.lower()):
                    legal_score += 0.3
                    triggers.append(f"file: {attachment}")
                    
        # Apply context boosts
        if context.get('sender') == 'yoni':
            legal_score += 0.05
            
        if 'urgent' in message_lower or 'דחוף' in message_lower:
            legal_score += 0.1
            triggers.append("urgency_indicator")
            
        # Determine task type
        task_type = self._classify_task_type(message_lower, triggers)
        
        # Cap at 1.0
        legal_score = min(legal_score, 1.0)
        
        return {
            "is_legal": legal_score >= 0.4,
            "confidence": legal_score,
            "task_type": task_type,
            "triggers": triggers,
            "reasoning": f"Score: {legal_score:.2f} based on {len(triggers)} triggers"
        }

    def _classify_task_type(self, message: str, triggers: List[str]) -> str:
        """Determine specific legal task type"""
        
        # Contract Review
        if any('תסכמי' in t or 'review' in t for t in triggers):
            if any('חוזה' in t or 'contract' in t for t in triggers):
                return "contract_review"
                
        # Risk Analysis  
        if 'סיכונים' in message or 'risks' in message or 'בעיות' in message:
            return "risk_analysis"
            
        # Clause Extraction
        if ('תמצאי' in message or 'extract' in message) and ('סעיף' in message or 'clause' in message):
            return "clause_extraction"
            
        # Comparison
        if 'תשווי' in message or 'compare' in message or 'גרסה' in message:
            return "compare_versions"
            
        # Draft Response
        if 'תכיני' in message or 'draft' in message or 'תגובה' in message:
            return "draft_response"
            
        # Negotiation Prep
        if 'משא ומתן' in message or 'negotiation' in message:
            return "negotiation_prep"
            
        # Legal Summary (default for legal content)
        if any('חוזה' in t or 'הסכם' in t or 'contract' in t for t in triggers):
            return "legal_summary"
            
        return "unknown"

    def should_route_to_masha(self, classification: Dict) -> Tuple[bool, str]:
        """
        Decide if task should be routed to מאשה
        
        Returns: (should_route, action_type)
        action_type: 'direct' | 'confirm' | 'clarify' | 'decline'
        """
        confidence = classification['confidence']
        
        if confidence >= 0.8:
            return True, 'direct'
        elif confidence >= 0.6:
            return True, 'confirm'  # Ask user confirmation
        elif confidence >= 0.4:
            return False, 'clarify'  # Ask for clarification
        else:
            return False, 'decline'  # Not legal

def test_classifier():
    """Test the classifier with sample inputs"""
    classifier = LegalIntentClassifier()
    
    test_cases = [
        ("תסכמי את החוזה המצורף", ["contract.pdf"]),
        ("מה הסיכונים בהסכם הזה?", []),
        ("תמצאי סעיפי אחריות", []),
        ("תכיני תגובה לעורך הדין", []),
        ("תשווי בין שתי הגרסאות", ["v1.pdf", "v2.pdf"]), 
        ("תסכמי את הפגישה", []),  # Should NOT be legal
        ("בדקי מיילים", [])  # Should NOT be legal
    ]
    
    for message, attachments in test_cases:
        result = classifier.classify_legal_intent(message, attachments)
        should_route, action = classifier.should_route_to_masha(result)
        
        print(f"\nMessage: {message}")
        print(f"Attachments: {attachments}")
        print(f"Legal: {result['is_legal']} (confidence: {result['confidence']:.2f})")
        print(f"Task Type: {result['task_type']}")
        print(f"Route to Masha: {should_route} ({action})")
        print(f"Triggers: {result['triggers'][:3]}...")

if __name__ == "__main__":
    test_classifier()