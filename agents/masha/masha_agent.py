#!/usr/bin/env python3
"""
מאשה - Legal Domain Agent

⚖️ תפקיד: סוכנת משפטית לחוזים ומסמכים משפטיים
🎯 עקרונות: Draft-first, לא ממציאה חוק, מבנה קבוע, אישור נדרש

Capabilities:
- contract_review: ניתוח חוזה וזיהוי סיכונים
- clause_extraction: חילוץ סעיפים מרכזיים  
- risk_assessment: הערכת סיכונים משפטיים
- compare_versions: השוואה בין גרסאות חוזה
- draft_response: הכנת תגובה לחוזה
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class MashaAgent:
    """Legal domain agent - always drafts, never sends directly"""
    
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.name = "מאשה"
        self.domain = "legal"
        self.capabilities = [
            "contract_review",
            "clause_extraction", 
            "risk_assessment",
            "compare_versions",
            "draft_response"
        ]
    
    def can_handle(self, message: str, context: Dict = None) -> Dict:
        """Determine if this is a legal task"""
        
        legal_patterns = [
            r"חוזה|הסכם|contract",
            r"משפטי|דין|legal|law",
            r"סעיף|תנאי|clause|term",
            r"סיכום.{0,10}חוזה|contract.{0,10}review",
            r"תגובה.{0,10}משפטי|legal.{0,10}response"
        ]
        
        confidence = 0
        matched_patterns = []
        
        for pattern in legal_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                confidence += 0.2
                matched_patterns.append(pattern)
        
        # Check for attachments that look legal
        if context and context.get("attachments"):
            for attachment in context["attachments"]:
                if any(ext in attachment.get("name", "").lower() 
                      for ext in [".pdf", ".docx", ".doc"]):
                    confidence += 0.3
                    matched_patterns.append("legal_document_attachment")
        
        confidence = min(confidence, 1.0)
        
        return {
            "can_handle": confidence >= 0.2,
            "confidence": confidence,
            "agent": self.name,
            "domain": self.domain,
            "matched_patterns": matched_patterns,
            "reason": f"Legal patterns detected: {', '.join(matched_patterns)}" if matched_patterns else "No legal patterns"
        }
    
    def process_task(self, message: str, context: Dict = None) -> Dict:
        """Process legal task and return structured draft"""
        
        task_type = self._classify_legal_task(message)
        
        try:
            if task_type == "contract_review":
                return self._handle_contract_review(message, context)
            elif task_type == "clause_extraction":
                return self._handle_clause_extraction(message, context)
            elif task_type == "risk_assessment":
                return self._handle_risk_assessment(message, context)
            elif task_type == "draft_response":
                return self._handle_draft_response(message, context)
            else:
                return self._handle_general_legal(message, context)
                
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "task_type": task_type,
                "error": str(e),
                "recommendation": "Manual review required - legal agent encountered error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _classify_legal_task(self, message: str) -> str:
        """Classify the specific legal task type"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["סכם", "חוזה", "review", "ניתוח"]):
            return "contract_review"
        elif any(word in message_lower for word in ["סעיף", "clause", "חלץ", "extract"]):
            return "clause_extraction"
        elif any(word in message_lower for word in ["סיכון", "risk", "בעיה", "problem"]):
            return "risk_assessment"
        elif any(word in message_lower for word in ["תגובה", "response", "מענה", "reply"]):
            return "draft_response"
        else:
            return "general_legal"
    
    def _handle_contract_review(self, message: str, context: Dict) -> Dict:
        """Handle contract review task"""
        
        return {
            "status": "draft_ready",
            "agent": self.name,
            "task_type": "contract_review",
            "analysis": {
                "document_type": "contract",
                "review_status": "preliminary_analysis_complete",
                "key_findings": [
                    "חוזה זוהה ומחכה לניתוח מפורט",
                    "דרוש מסמך המקור לביצוע ניתוח מלא",
                    "המתחיל בדבורה לאישור לפני שליחה"
                ],
                "risk_level": "pending_document_review",
                "recommendations": [
                    "לוודא שהמסמך המקורי זמין",
                    "לבדוק תנאי תשלום",
                    "לזהות סעיפי אחריות"
                ]
            },
            "draft_actions": {
                "requires_approval": True,
                "approval_reason": "Legal analysis requires review before sending",
                "suggested_next_steps": [
                    "לבדוק מסמך המקור",
                    "לבצע ניתוח סיכונים מפורט",
                    "להכין סיכום למזמין העבודה"
                ]
            },
            "metadata": {
                "model_tier_used": "tier3",
                "confidence": 0.8,
                "requires_human_review": True,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _handle_clause_extraction(self, message: str, context: Dict) -> Dict:
        """Handle clause extraction task"""
        
        return {
            "status": "draft_ready", 
            "agent": self.name,
            "task_type": "clause_extraction",
            "extracted_clauses": {
                "pending": "מסמך נדרש לחילוץ סעיפים",
                "structure": {
                    "payment_terms": "תנאי תשלום - לא זוהו עדיין",
                    "liability_clauses": "סעיפי אחריות - לא זוהו עדיין", 
                    "termination_conditions": "תנאי סיום - לא זוהו עדיין",
                    "dispute_resolution": "יישוב סכסוכים - לא זוהה עדיין"
                }
            },
            "draft_actions": {
                "requires_approval": True,
                "approval_reason": "Clause extraction requires document and verification"
            },
            "metadata": {
                "confidence": 0.6,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _handle_risk_assessment(self, message: str, context: Dict) -> Dict:
        """Handle risk assessment task"""
        
        return {
            "status": "draft_ready",
            "agent": self.name, 
            "task_type": "risk_assessment",
            "risk_analysis": {
                "overall_risk": "pending_document_review",
                "risk_categories": {
                    "financial_risk": "לא הוערך - דרוש מסמך",
                    "legal_risk": "לא הוערך - דרוש מסמך",
                    "operational_risk": "לא הוערך - דרוש מסמך"
                },
                "recommendations": [
                    "לספק מסמך לניתוח סיכונים מפורט",
                    "לזהות אזורי סיכון עיקריים",
                    "לבדוק התאמה לדרישות החוק"
                ]
            },
            "draft_actions": {
                "requires_approval": True,
                "approval_reason": "Risk assessment requires validation before communication"
            },
            "metadata": {
                "confidence": 0.5,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _handle_draft_response(self, message: str, context: Dict) -> Dict:
        """Handle drafting legal response"""
        
        return {
            "status": "draft_ready",
            "agent": self.name,
            "task_type": "draft_response", 
            "response_draft": {
                "subject": "תגובה משפטית - טיוטה להערכה",
                "content": "טיוטה משפטית מוכנה לבדיקה. דרושה עריכה ואישור לפני שליחה.",
                "tone": "professional_legal",
                "requires_customization": True
            },
            "draft_actions": {
                "requires_approval": True,
                "approval_reason": "Legal response must be reviewed before sending",
                "suggested_edits": [
                    "לוודא דיוק עובדתי",
                    "לבדוק התאמה למקרה הספציפי", 
                    "לוודא תקינות משפטית"
                ]
            },
            "metadata": {
                "confidence": 0.7,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _handle_general_legal(self, message: str, context: Dict) -> Dict:
        """Handle general legal inquiry"""
        
        return {
            "status": "draft_ready",
            "agent": self.name,
            "task_type": "general_legal",
            "response": {
                "type": "legal_guidance_draft",
                "content": "פנייה משפטית התקבלה. מוכנה טיוטת תגובה לבדיקה.",
                "disclaimer": "המידע המסופק הינו לידע כללי ואינו מהווה ייעוץ משפטי",
                "next_steps": "דרושה בדיקה ואישור לפני שליחה"
            },
            "draft_actions": {
                "requires_approval": True,
                "approval_reason": "All legal communications require approval"
            },
            "metadata": {
                "confidence": 0.4,
                "timestamp": datetime.now().isoformat()
            }
        }

# Global instance
masha = MashaAgent()

def handle_legal_task(message: str, context: Dict = None) -> Dict:
    """Global function to handle legal tasks via מאשה"""
    assessment = masha.can_handle(message, context)
    
    if assessment["can_handle"]:
        return masha.process_task(message, context)
    else:
        return {
            "status": "not_legal_task",
            "confidence": assessment["confidence"],
            "reason": assessment["reason"],
            "agent": "מאשה",
            "recommendation": "Forward to general handler"
        }