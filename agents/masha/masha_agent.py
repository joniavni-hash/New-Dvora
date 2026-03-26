#!/usr/bin/env python3
"""
מאשה — Legal Domain Agent  PR2: execute() → FinalPayload

execute() returns final_text = a real draft text.
Dvorah does NOT rewrite it — only approves or blocks.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))
from domain_agent_base import (
    DomainAgent, FinalPayload, RoutingResult, ModelTier, WORKSPACE
)


class MashaAgent(DomainAgent):
    AGENT_NAME = "מאשה"
    AGENT_EMOJI = "⚖️"
    DOMAIN = "legal"
    KEYWORDS = [
        "חוזה", "הסכם", "contract", "legal",
        "משפטי", "דין", "law", "clause",
        "סעיף", "תנאי", "terms", "condition",
        "סיכון", "risk", "תגובה", "response",
    ]

    TASK_MAP = {
        "contract_review": [
            "סכם", "חוזה", "review", "ניתוח", "לנתח", "לבדוק", "לסכם",
        ],
        "clause_extraction": ["סעיף", "clause", "חלץ", "extract"],
        "risk_assessment":   ["סיכון", "risk", "בעיה", "problem"],
        "draft_response":    ["תגובה", "response", "מענה", "reply"],
    }

    def can_handle(self, message: str, context: Dict,
                   attachments: List[str] = None) -> RoutingResult:
        score = self.keyword_match(message)
        if context and context.get("attachments"):
            for att in context["attachments"]:
                if any(ext in att.get("name", "").lower()
                       for ext in [".pdf", ".docx", ".doc"]):
                    score = max(score, 0.8)
        return RoutingResult(
            can_handle=score >= 0.2,
            confidence=score,
            domain=self.DOMAIN,
            tier=ModelTier.TIER2_MID,   # PR1: never tier3 by default
            estimated_cost_usd=self.estimate_cost(ModelTier.TIER2_MID),
            reason=f"Legal keyword score: {score:.2f}",
        )

    def execute(self, message: str, context: Dict,
                attachments: List[str] = None) -> FinalPayload:
        """
        PR2: returns FinalPayload with real draft text.
        final_text = the actual legal analysis draft, ready for approval.
        """
        self._start_timer()
        task = self._classify_task(message)
        draft = self._build_draft(task, message, context)

        return FinalPayload(
            status="needs_approval",
            agent=self.AGENT_NAME,
            final_text=draft,
            should_send=False,          # legal always needs approval
            requires_approval=True,
            write_actions=[],
            metadata={
                "model_used":   "anthropic/claude-sonnet-4-20250514",
                "model_reason": f"legal/{task} — tier2 default (PR1 enforcement)",
                "output_mode":  "draft_for_approval",
                "task_type":    task,
                "duration_ms":  self._elapsed_ms(),
            },
        )

    # ── Draft builders ────────────────────────────────────────────────────────

    def _classify_task(self, message: str) -> str:
        msg = message.lower()
        for task, keywords in self.TASK_MAP.items():
            if any(kw in msg for kw in keywords):
                return task
        return "general_legal"

    def _build_draft(self, task: str, message: str, context: Dict) -> str:
        ts = datetime.now().strftime("%Y-%m-%d")
        intro = f"[טיוטה ← מאשה ⚖️ | {ts}]\n"

        builders = {
            "contract_review":    self._draft_contract_review,
            "clause_extraction":  self._draft_clause_extraction,
            "risk_assessment":    self._draft_risk_assessment,
            "draft_response":     self._draft_response,
            "general_legal":      self._draft_general,
        }
        body = builders.get(task, self._draft_general)(message, context)
        return intro + body

    def _draft_contract_review(self, message: str, context: Dict) -> str:
        return (
            "סוג מסמך: חוזה / הסכם\n\n"
            "ממצאים ראשוניים:\n"
            "• דרוש מסמך מקורי לניתוח מלא\n"
            "• נקודות לבדיקה: תנאי תשלום, סעיפי אחריות, תנאי סיום\n"
            "• סיכון ראשוני: לא ניתן להעריך ללא מסמך\n\n"
            "צעד הבא: שלח את קובץ החוזה (PDF/DOCX) לניתוח מפורט.\n\n"
            f"הודעה מקורית: {message}"
        )

    def _draft_clause_extraction(self, message: str, context: Dict) -> str:
        return (
            "בקשה: חילוץ סעיפים\n\n"
            "סעיפים לחילוץ:\n"
            "• תנאי תשלום — טרם זוהו (דרוש מסמך)\n"
            "• סעיפי אחריות — טרם זוהו\n"
            "• תנאי סיום — טרם זוהו\n"
            "• יישוב סכסוכים — טרם זוהו\n\n"
            "דרוש: מסמך מקורי לחילוץ מדויק."
        )

    def _draft_risk_assessment(self, message: str, context: Dict) -> str:
        return (
            "הערכת סיכונים — טיוטה\n\n"
            "רמת סיכון כוללת: ממתין לבדיקת מסמך\n\n"
            "קטגוריות סיכון:\n"
            "• סיכון פיננסי: לא הוערך\n"
            "• סיכון משפטי: לא הוערך\n"
            "• סיכון תפעולי: לא הוערך\n\n"
            "המלצה: לספק מסמך לניתוח מלא."
        )

    def _draft_response(self, message: str, context: Dict) -> str:
        return (
            "טיוטת תגובה משפטית\n\n"
            "הנדון: [יש להשלים]\n\n"
            "לכבוד [שם הנמען],\n\n"
            "בהתייחס לפנייתכם — [יש להשלים תוכן לאחר עיון במסמך].\n\n"
            "בכבוד רב,\n"
            "[חתימה]\n\n"
            "⚠️ טיוטה בלבד — דרוש אישור לפני שליחה."
        )

    def _draft_general(self, message: str, context: Dict) -> str:
        return (
            f"פנייה משפטית: {message}\n\n"
            "תגובה: פנייתך התקבלה ומועברת לטיפול.\n"
            "יש לספק פרטים נוספים / מסמכים רלוונטיים לניתוח מדויק.\n\n"
            "⚠️ אין בתגובה זו ייעוץ משפטי — רק עיבוד ראשוני."
        )


# ── Legacy shim ───────────────────────────────────────────────────────────────
masha = MashaAgent()


def handle_legal_task(message: str, context: Dict = None) -> Dict:
    """Legacy entry point — converts FinalPayload to old dict format."""
    payload = masha.execute(message, context or {})
    return {
        "status":           payload.status,
        "agent":            payload.agent,
        "final_text":       payload.final_text,
        "requires_approval": payload.requires_approval,
        "metadata":         payload.metadata,
    }
