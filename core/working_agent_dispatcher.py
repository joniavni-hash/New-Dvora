#!/usr/bin/env python3
"""
Working Agent Dispatcher - מעביר context לsubagent בלי agentId
כיוון שOpenClaw לא מאפשר cross-agent spawning, אנחנו מעבירים context בinstructions
"""

import json
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

class WorkingAgentDispatcher:
    """
    Dispatcher שעובד עם המגבלות הנוכחיות של OpenClaw
    """
    
    def __init__(self):
        self.agents_registry = self._load_agents_registry()
        self.domain_routing = {
            "legal": "masha",
            "groups": "odya", 
            "marketing": "tali",
            "research": "tzofit",
            "automation": "eti",
            "fitness": "dana"
        }
    
    def _load_agents_registry(self) -> Dict[str, Any]:
        """טען agents registry"""
        registry_path = Path("config/AGENTS_REGISTRY.json")
        if registry_path.exists():
            with open(registry_path) as f:
                data = json.load(f)
                return data.get("agents", {})
        return {}
    
    def classify_message_domain(self, message: str) -> Tuple[str, str, float]:
        """זיהוי domain והagent המתאים"""
        msg_lower = message.lower()
        
        # Legal
        if any(word in msg_lower for word in ['חוזה', 'הסכם', 'משפטי', 'חוק', 'סיכון', 'legal', 'מאשה']):
            return ("legal", "masha", 0.9)
        
        # Groups
        if any(word in msg_lower for word in ['קבוצה', 'whatsapp', 'הודעות', 'סיכום קבוצת', 'אלון', 'אודיה']):
            return ("groups", "odya", 0.9)
        
        # Marketing  
        if any(word in msg_lower for word in ['villa', 'tiktok', 'marketing', 'larry', 'פרסום', 'שיווק', 'טלי']):
            return ("marketing", "tali", 0.9)
        
        # Research
        if any(word in msg_lower for word in ['חקר', 'בדק', 'מחקר', 'נתח', 'שוק', 'research', 'צופית']):
            return ("research", "tzofit", 0.9)
        
        # Fitness
        if any(word in msg_lower for word in ['שקלתי', 'אכלתי', 'קלוריות', 'חלבון', 'כושר', 'דיאטה', 'דנה']):
            return ("fitness", "dana", 0.9)
        
        # Automation
        if any(word in msg_lower for word in ['אוטומציה', 'תהליך', 'אינטגרציה', 'זרימה', 'אתי']):
            return ("automation", "eti", 0.9)
        
        return ("general", None, 0.1)
    
    def build_agent_context_prompt(self, agent_id: str, original_task: str) -> str:
        """בונה prompt עם הקשר לagent הספציפי"""
        
        if agent_id not in self.agents_registry:
            return original_task
        
        agent_config = self.agents_registry[agent_id]
        agent_name = agent_config["name"]
        domain = agent_config["domain"] 
        description = agent_config["description"]
        
        # Agent-specific context
        context_prompts = {
            "masha": """
אתה מאשה - היועצת המשפטית של יוני.
התמחותך: ניתוח חוזים, זיהוי סיכונים משפטיים, חוות דעת משפטית.
פעל לפי הפורמטים ב-agents/masha/ והשתמש ב-Legal Risk Rubric.
ביצע ניתוח מקצועי עם המלצות ברורות.
""",
            "odya": """
את אודיה - מתאמת קבוצות WhatsApp של יוני.
התמחותך: סיכומי קבוצות, ניתוח הודעות, תקשורת מקצועית.
פעלי לפי הפורמטים ב-agents/odya/ והשתמשי בstructured summaries.
צרי סיכומים קצרים ומקצועיים עם action items.
""",
            "tali": """
את טלי - מומחית השיווק הדיגיטלי של יוני. 
התמחותך: TikTok, Instagram, פרסום Villa Lithos, Larry methodology.
פעלי לפי הפורמטים ב-agents/tali/ והשתמשי ב-Larry skill.
צרי תוכן יצירתי ואטרקטיבי לרשתות חברתיות.
""",
            "tzofit": """
את צופית - החוקרת של יוני.
התמחותך: מחקר שוק, ניתוח תחרותי, מודיעין עסקי.
פעלי לפי הפורמטים ב-agents/tzofit/ והשתמשי בכלי מחקר.
בצעי מחקר יסודי עם תובנות מעשיות.
""",
            "eti": """
את אתי - מומחית האוטומציה של יוני.
התמחותך: תהליכי עבודה, אינטגרציות, אופטימיזציה.
פעלי לפי הפורמטים ב-agents/eti/ והתמקדי ביעילות.
בני פתרונות אוטומטיים ומובנים.
""",
            "dana": """
את דנה - המאמנת הכושר של יוני.
התמחותך: מעקב תזונה, יעדי כושר, ניתוח קלורי.
פעלי לפי הפורמטים ב-agents/dana/ ועדכני קבצי מעקב.
תני המלצות מעשיות וביצעי מעקב מדויק.
"""
        }
        
        agent_context = context_prompts.get(agent_id, f"""
אתה {agent_name}.
תחום התמחותך: {domain}.
{description}
""")
        
        return f"""{agent_context}

המשימה המקורית: {original_task}

פעל בתור {agent_name} והתמחה בתחום {domain}. 
השתמש בכלים והפורמטים המתאימים לתחום שלך.
"""
    
    def dispatch_to_agent(self, message: str, sessions_spawn_func) -> Dict[str, Any]:
        """מנתב עם context, בלי agentId"""
        
        # Classification
        domain, agent_id, confidence = self.classify_message_domain(message)
        
        if not agent_id:
            return {
                "status": "direct_handling",
                "domain": domain,
                "confidence": confidence,
                "reason": "לא זוהה domain ברור - דבורה מטפלת ישירות"
            }
        
        # Agent context building
        agent_config = self.agents_registry.get(agent_id, {})
        enhanced_task = self.build_agent_context_prompt(agent_id, message)
        
        # Sessions spawn בלי agentId אבל עם context מלא
        try:
            result = sessions_spawn_func(
                runtime="subagent",
                mode="run",
                task=enhanced_task,
                model=agent_config.get("defaultModel", "anthropic/claude-sonnet-4-20250514"),
                label=f"{agent_config.get('name', agent_id)} - {domain} domain"
            )
            
            return {
                "status": "success",
                "dispatch_method": "context_injection",
                "intended_agent": agent_id,
                "agent_name": agent_config.get("name", agent_id),
                "domain": domain,
                "confidence": confidence,
                "context_enhanced": True,
                "sessions_spawn_result": result,
                "session_key": result.get("childSessionKey", "unknown"),
                "run_id": result.get("runId", "unknown")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"sessions_spawn נכשל: {str(e)}",
                "intended_agent": agent_id,
                "domain": domain
            }

# Global dispatcher
working_dispatcher = WorkingAgentDispatcher()

def dispatch_message_working(message: str, sessions_spawn_func) -> Dict[str, Any]:
    """Entry point לdispatcher עובד"""
    return working_dispatcher.dispatch_to_agent(message, sessions_spawn_func)

if __name__ == "__main__":
    # Test classification
    test_messages = [
        "בדקי חוזה שכירות",
        "סכמי הודעות קבוצת אלון", 
        "צרי פרסום Villa Lithos לTikTok",
        "חקרי שוק הנדלן"
    ]
    
    for msg in test_messages:
        domain, agent, conf = working_dispatcher.classify_message_domain(msg)
        print(f"'{msg}' → {agent} ({domain}, {conf:.1f})")