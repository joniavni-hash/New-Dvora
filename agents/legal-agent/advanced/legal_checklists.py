#!/usr/bin/env python3
"""
Legal Checklists — Structured checklist system for cheap-model legal analysis.
Enables Tier 1 (Sonnet) to handle 60-70% of legal analysis work using
structured extraction rather than open-ended reasoning.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ChecklistItem:
    """Single item in a legal checklist."""
    id: str
    category: str
    question_he: str     # Hebrew question for output
    question_en: str     # English question for model prompt
    risk_if_missing: str  # low/medium/high/critical
    extraction_hint: str  # Hint for the model on where to look
    standard_expectation: str  # What's normal/expected


@dataclass 
class ChecklistResult:
    """Result of evaluating a single checklist item."""
    item_id: str
    found: bool
    value: Optional[str] = None      # Extracted value/clause text
    clause_ref: Optional[str] = None  # Section/clause number
    assessment: str = "pending"       # ok/warning/risk/missing
    note: Optional[str] = None        # Additional observation


# ============================================================
# MASTER CHECKLISTS
# ============================================================

CONTRACT_REVIEW_CHECKLIST: List[ChecklistItem] = [
    # --- PARTIES & BASICS ---
    ChecklistItem("parties", "basics", "מי הצדדים?", "Who are the parties to this agreement?", "high", "Look at preamble/recitals", "Clear identification of all parties with full legal names"),
    ChecklistItem("effective_date", "basics", "מתי ההסכם נכנס לתוקף?", "When does the agreement take effect?", "medium", "Preamble or definitions", "Clear effective date or signing date"),
    ChecklistItem("purpose", "basics", "מה מטרת ההסכם?", "What is the purpose/subject of the agreement?", "medium", "Recitals or first operative clause", "Clear statement of purpose"),
    ChecklistItem("definitions", "basics", "האם יש הגדרות ברורות?", "Are key terms clearly defined?", "medium", "Definitions section", "Critical terms should be defined"),

    # --- OBLIGATIONS ---
    ChecklistItem("client_obligations", "obligations", "מה החובות של הלקוח?", "What are the client's/Yoni's obligations?", "high", "Services/obligations/scope sections", "Clearly scoped, measurable obligations"),
    ChecklistItem("counterparty_obligations", "obligations", "מה חובות הצד השני?", "What are the counterparty's obligations?", "high", "Services/obligations/scope sections", "Balanced with client obligations"),
    ChecklistItem("delivery_timeline", "obligations", "מהם לוחות הזמנים?", "What are the delivery timelines?", "medium", "Schedule/milestones sections", "Reasonable timelines with buffer"),

    # --- PAYMENT ---
    ChecklistItem("payment_amount", "payment", "מהי התמורה?", "What is the payment/consideration?", "high", "Payment/fees/consideration section", "Clear amounts or calculation method"),
    ChecklistItem("payment_schedule", "payment", "מהו לוח התשלומים?", "What is the payment schedule?", "medium", "Payment terms section", "Regular intervals, milestone-based, or upon completion"),
    ChecklistItem("late_payment", "payment", "מה קורה בפיגור תשלום?", "What are the late payment consequences?", "medium", "Payment/penalties section", "Interest rate with cap, not punitive"),
    ChecklistItem("expenses", "payment", "מי נושא בהוצאות?", "Who bears expenses?", "low", "Expenses/reimbursement section", "Clear allocation or cap on expenses"),

    # --- LIABILITY ---
    ChecklistItem("liability_cap", "liability", "האם יש תקרת חבות?", "Is there a liability cap?", "critical", "Liability/limitation section", "Liability capped at contract value or reasonable multiple"),
    ChecklistItem("indemnification", "liability", "האם יש שיפוי?", "Is there an indemnification clause?", "high", "Indemnification section", "Mutual or balanced indemnification"),
    ChecklistItem("warranty", "liability", "מה ההתחייבויות/ערבויות?", "What warranties are provided?", "medium", "Warranties/representations section", "Reasonable warranties with limitations"),
    ChecklistItem("exclusion_of_damages", "liability", "אילו נזקים מוחרגים?", "What types of damages are excluded?", "high", "Liability section", "Consequential/indirect damages excluded"),

    # --- TERMINATION ---
    ChecklistItem("term_duration", "termination", "מהי תקופת ההסכם?", "What is the term/duration?", "medium", "Term section", "Clear start and end, or renewal mechanism"),
    ChecklistItem("termination_for_cause", "termination", "ביטול עקב הפרה?", "Can the agreement be terminated for cause?", "high", "Termination section", "Both parties can terminate for material breach"),
    ChecklistItem("termination_for_convenience", "termination", "ביטול ללא סיבה?", "Can either party terminate for convenience?", "medium", "Termination section", "Mutual right with reasonable notice"),
    ChecklistItem("notice_period", "termination", "מהי תקופת ההודעה המוקדמת?", "What is the notice period for termination?", "medium", "Termination/notice section", "30-90 days is standard"),
    ChecklistItem("post_termination", "termination", "מה קורה אחרי סיום?", "What happens post-termination?", "medium", "Survival/post-termination section", "IP returns, payment of accrued fees, wind-down"),

    # --- IP ---
    ChecklistItem("ip_ownership", "ip", "מי הבעלים של ה-IP?", "Who owns the intellectual property?", "critical", "IP/ownership section", "Client retains pre-existing IP; work product ownership clear"),
    ChecklistItem("ip_license", "ip", "מה הרישיון ל-IP?", "What IP licenses are granted?", "high", "IP/license section", "Appropriate license scope, not overly broad"),
    ChecklistItem("background_ip", "ip", "מה לגבי IP קיים?", "How is pre-existing/background IP handled?", "medium", "IP section", "Pre-existing IP remains with original owner"),

    # --- CONFIDENTIALITY ---
    ChecklistItem("confidentiality", "confidentiality", "האם יש סעיף סודיות?", "Is there a confidentiality clause?", "high", "Confidentiality/NDA section", "Mutual, with reasonable duration and exceptions"),
    ChecklistItem("confidentiality_duration", "confidentiality", "כמה זמן חלה הסודיות?", "How long does confidentiality last?", "medium", "Confidentiality section", "2-5 years is standard"),
    ChecklistItem("confidentiality_exceptions", "confidentiality", "מה היוצאים מן הכלל?", "What are the confidentiality exceptions?", "low", "Confidentiality section", "Standard exceptions: public info, independent development, legal requirement"),

    # --- DISPUTE RESOLUTION ---
    ChecklistItem("governing_law", "dispute", "מהו הדין החל?", "What is the governing law?", "high", "Governing law section", "Israeli law for domestic agreements"),
    ChecklistItem("jurisdiction", "dispute", "מהי סמכות השיפוט?", "What is the jurisdiction/venue?", "high", "Jurisdiction/dispute section", "Israeli courts for domestic agreements"),
    ChecklistItem("dispute_mechanism", "dispute", "מהו מנגנון יישוב סכסוכים?", "What is the dispute resolution mechanism?", "medium", "Dispute section", "Negotiation → Mediation → Litigation/Arbitration"),

    # --- GENERAL ---
    ChecklistItem("force_majeure", "general", "האם יש כח עליון?", "Is there a force majeure clause?", "medium", "Force majeure section", "Mutual, with clear trigger events"),
    ChecklistItem("assignment", "general", "האם ניתן להעביר את ההסכם?", "Can the agreement be assigned?", "medium", "Assignment section", "Requires consent, with exceptions"),
    ChecklistItem("amendment", "general", "איך משנים את ההסכם?", "How can the agreement be amended?", "low", "Amendment section", "Written agreement of both parties"),
    ChecklistItem("entire_agreement", "general", "סעיף הסכם שלם?", "Is there an entire agreement clause?", "low", "Miscellaneous section", "Standard entire agreement clause"),
    ChecklistItem("non_compete", "general", "האם יש אי-תחרות?", "Is there a non-compete clause?", "high", "Non-compete section", "Reasonable in scope, duration, and geography"),
]


RISK_ANALYSIS_CHECKLIST: List[ChecklistItem] = [
    # Financial risks
    ChecklistItem("unlimited_liability", "financial", "חבות בלתי מוגבלת?", "Is there unlimited liability exposure?", "critical", "Liability section", "Should be capped"),
    ChecklistItem("penalty_clauses", "financial", "סעיפי קנס?", "Are there penalty/liquidated damages clauses?", "high", "Penalties section", "Should be reasonable and proportionate"),
    ChecklistItem("payment_risk", "financial", "סיכון תשלום?", "Is there payment risk (no security)?", "medium", "Payment section", "Payment milestones or security"),
    ChecklistItem("currency_risk", "financial", "סיכון מטבע?", "Is there currency/exchange rate risk?", "medium", "Payment section", "Fixed currency or adjustment mechanism"),

    # Operational risks
    ChecklistItem("sla_requirements", "operational", "דרישות SLA קשיחות?", "Are SLA requirements unreasonable?", "high", "SLA/service levels section", "Achievable with standard resources"),
    ChecklistItem("staffing_restrictions", "operational", "מגבלות צוות?", "Are there key person/staffing restrictions?", "medium", "Personnel section", "Reasonable substitution rights"),
    ChecklistItem("exclusivity", "operational", "בלעדיות?", "Is there exclusivity that limits other work?", "high", "Exclusivity section", "Narrow scope if any"),
    ChecklistItem("insurance_requirements", "operational", "דרישות ביטוח?", "Are insurance requirements unusual?", "medium", "Insurance section", "Standard professional indemnity"),

    # Legal risks
    ChecklistItem("foreign_jurisdiction", "legal", "סמכות שיפוט זרה?", "Is jurisdiction in a foreign country?", "high", "Jurisdiction section", "Domestic jurisdiction preferred"),
    ChecklistItem("regulatory_compliance", "legal", "ציות רגולטורי?", "Are there regulatory compliance obligations?", "medium", "Compliance section", "Clear allocation of compliance responsibilities"),
    ChecklistItem("data_protection", "legal", "הגנת מידע?", "Are there data protection obligations?", "high", "Data protection section", "GDPR/privacy compliance if applicable"),
    ChecklistItem("audit_rights", "legal", "זכויות ביקורת?", "Are there broad audit rights?", "medium", "Audit section", "Reasonable scope and frequency"),

    # Strategic risks  
    ChecklistItem("ip_transfer", "strategic", "העברת IP?", "Is IP being transferred away?", "critical", "IP section", "IP retention or fair compensation"),
    ChecklistItem("non_compete_broad", "strategic", "אי-תחרות רחב?", "Is non-compete overly broad?", "high", "Non-compete section", "Narrow and time-limited"),
    ChecklistItem("lock_in", "strategic", "נעילה?", "Is there vendor/client lock-in?", "medium", "Termination/exclusivity sections", "Reasonable exit path"),
    ChecklistItem("reputation_risk", "strategic", "סיכון מוניטין?", "Is there reputational risk?", "medium", "Publicity/branding sections", "Approval rights over public statements"),
]


# Mapping from workflow type to applicable checklist
WORKFLOW_CHECKLISTS = {
    "contract_review": CONTRACT_REVIEW_CHECKLIST,
    "risk_analysis": RISK_ANALYSIS_CHECKLIST,
    "clause_extraction": CONTRACT_REVIEW_CHECKLIST,  # Uses same items, filtered by category
    "legal_summary": CONTRACT_REVIEW_CHECKLIST[:12],  # Basics + obligations + payment
    "compare_versions": CONTRACT_REVIEW_CHECKLIST,     # Compare each item between versions
    "draft_response": CONTRACT_REVIEW_CHECKLIST,       # Need to know current state
    "negotiation_prep": CONTRACT_REVIEW_CHECKLIST + RISK_ANALYSIS_CHECKLIST,  # Full picture
}


def get_checklist_for_workflow(workflow_type: str, focus_category: Optional[str] = None) -> List[ChecklistItem]:
    """
    Get the appropriate checklist for a workflow type.
    Optionally filter by category (e.g., "liability", "termination").
    """
    items = WORKFLOW_CHECKLISTS.get(workflow_type, CONTRACT_REVIEW_CHECKLIST)
    if focus_category:
        items = [item for item in items if item.category == focus_category]
    return items


def build_extraction_prompt(checklist: List[ChecklistItem]) -> str:
    """
    Build a structured extraction prompt for Tier 1 models.
    This is the key enabler — turns open-ended analysis into structured extraction.
    """
    prompt_parts = [
        "Analyze the following document and extract information for each checklist item.",
        "For each item, provide:",
        "- found: true/false (is this addressed in the document?)",
        "- value: the relevant text or summary (if found)",
        "- clause_ref: section/clause number (if identifiable)",
        "- assessment: ok/warning/risk/missing",
        "- note: any additional observation",
        "",
        "Return results as JSON array.",
        "",
        "CHECKLIST ITEMS:",
        ""
    ]

    for i, item in enumerate(checklist, 1):
        prompt_parts.append(f"{i}. [{item.id}] {item.question_en}")
        prompt_parts.append(f"   Look in: {item.extraction_hint}")
        prompt_parts.append(f"   Expected: {item.standard_expectation}")
        prompt_parts.append(f"   Risk if missing: {item.risk_if_missing}")
        prompt_parts.append("")

    return "\n".join(prompt_parts)


def build_checklist_summary(results: List[ChecklistResult], checklist: List[ChecklistItem]) -> str:
    """
    Build a Hebrew summary from checklist results.
    Used as the structured output for Tier 1 analysis.
    """
    # Map items by id for lookup
    item_map = {item.id: item for item in checklist}
    
    # Group by assessment
    ok_items = [r for r in results if r.assessment == "ok"]
    warning_items = [r for r in results if r.assessment == "warning"]
    risk_items = [r for r in results if r.assessment == "risk"]
    missing_items = [r for r in results if r.assessment == "missing"]

    lines = []

    if risk_items:
        lines.append("## 🔴 סיכונים")
        for r in risk_items:
            item = item_map.get(r.item_id)
            if item:
                lines.append(f"- **{item.question_he}** — {r.note or r.value or 'בעייתי'}")
                if r.clause_ref:
                    lines.append(f"  (סעיף {r.clause_ref})")
        lines.append("")

    if missing_items:
        lines.append("## ❌ חסר")
        for r in missing_items:
            item = item_map.get(r.item_id)
            if item:
                risk_label = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚫"}.get(item.risk_if_missing, "")
                lines.append(f"- {risk_label} **{item.question_he}** — לא נמצא ({item.standard_expectation})")
        lines.append("")

    if warning_items:
        lines.append("## 🟡 נקודות תשומת לב")
        for r in warning_items:
            item = item_map.get(r.item_id)
            if item:
                lines.append(f"- **{item.question_he}** — {r.note or r.value or 'דורש בדיקה'}")
                if r.clause_ref:
                    lines.append(f"  (סעיף {r.clause_ref})")
        lines.append("")

    if ok_items:
        lines.append("## ✅ תקין")
        for r in ok_items:
            item = item_map.get(r.item_id)
            if item:
                lines.append(f"- **{item.question_he}** — {r.value or 'נמצא תקין'}")
        lines.append("")

    # Summary stats
    total = len(results)
    lines.append("## 📊 סיכום")
    lines.append(f"- **תקין:** {len(ok_items)}/{total}")
    lines.append(f"- **אזהרות:** {len(warning_items)}/{total}")
    lines.append(f"- **סיכונים:** {len(risk_items)}/{total}")
    lines.append(f"- **חסר:** {len(missing_items)}/{total}")

    return "\n".join(lines)


def test_checklists():
    """Test checklist generation."""
    # Contract review checklist
    cl = get_checklist_for_workflow("contract_review")
    print(f"Contract review checklist: {len(cl)} items")
    print(f"Categories: {set(item.category for item in cl)}")

    # Risk analysis checklist
    cl = get_checklist_for_workflow("risk_analysis")
    print(f"\nRisk analysis checklist: {len(cl)} items")

    # Filtered by category
    cl = get_checklist_for_workflow("contract_review", focus_category="liability")
    print(f"\nLiability items: {len(cl)} items")

    # Build extraction prompt
    cl = get_checklist_for_workflow("clause_extraction", focus_category="payment")
    prompt = build_extraction_prompt(cl)
    print(f"\nExtraction prompt for payment clauses ({len(prompt)} chars):")
    print(prompt[:500] + "...")


if __name__ == "__main__":
    test_checklists()
