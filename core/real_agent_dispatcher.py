#!/usr/bin/env python3
"""
Real Agent Dispatcher - מנתב הודעות לagents אמיתיים
מחליף את הPython classes במערכת sessions_spawn אמיתית
"""

import json
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

class RealAgentDispatcher:
    """
    Dispatcher אמיתי שמנתב ל-OpenClaw agents עם sessions_spawn
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
        """טען את agents registry"""
        registry_path = Path("config/AGENTS_REGISTRY.json")
        if registry_path.exists():
            with open(registry_path) as f:
                data = json.load(f)
                return data.get("agents", {})
        return {}
    
    def classify_message_domain(self, message: str) -> Tuple[str, str, float]:
        """
        מזהה את ה-domain והagent המתאים
        Returns: (domain, agent_id, confidence)
        """
        msg_lower = message.lower()
        
        # Legal
        if any(word in msg_lower for word in ['חוזה', 'הסכם', 'משפטי', 'חוק', 'סיכון', 'legal']):
            return ("legal", "masha", 0.9)
        
        # Groups
        if any(word in msg_lower for word in ['קבוצה', 'whatsapp', 'הודעות', 'סיכום קבוצת', 'אלון']):
            return ("groups", "odya", 0.9)
        
        # Marketing  
        if any(word in msg_lower for word in ['villa', 'tiktok', 'marketing', 'larry', 'פרסום', 'שיווק']):
            return ("marketing", "tali", 0.9)
        
        # Research
        if any(word in msg_lower for word in ['חקר', 'בדק', 'מחקר', 'נתח', 'שוק', 'research']):
            return ("research", "tzofit", 0.9)
        
        # Fitness
        if any(word in msg_lower for word in ['שקלתי', 'אכלתי', 'קלוריות', 'חלבון', 'כושר', 'דיאטה']):
            return ("fitness", "dana", 0.9)
        
        # Automation
        if any(word in msg_lower for word in ['אוטומציה', 'תהליך', 'אינטגרציה', 'זרימה']):
            return ("automation", "eti", 0.9)
        
        # Default - לא מזהה domain ברור
        return ("general", None, 0.1)
    
    def dispatch_to_agent(self, message: str, sessions_spawn_func) -> Dict[str, Any]:
        """
        מנתב הודעה לagent המתאים דרך sessions_spawn
        """
        
        # שלב 1: Classification
        domain, agent_id, confidence = self.classify_message_domain(message)
        
        if not agent_id:
            return {
                "status": "error",
                "error": "לא זוהה domain ברור - נדרש agent ספציפי",
                "domain": domain,
                "confidence": confidence,
                "fallback_action": "handle_manually"
            }
        
        # שלב 2: Validation
        if agent_id not in self.agents_registry:
            return {
                "status": "error", 
                "error": f"Agent {agent_id} לא מוגדר ב-registry",
                "agent_id": agent_id,
                "domain": domain
            }
        
        agent_config = self.agents_registry[agent_id]
        
        # שלב 3: Sessions_spawn
        try:
            result = sessions_spawn_func(
                runtime="subagent",
                agentId=agent_config["agentId"],
                mode="run", 
                task=message,
                model=agent_config["defaultModel"],
                label=f"{agent_config['name']} - {domain} task"
            )
            
            return {
                "status": "success",
                "dispatch_method": "sessions_spawn",
                "agent_id": agent_id,
                "agent_name": agent_config["name"], 
                "domain": domain,
                "confidence": confidence,
                "sessions_spawn_result": result,
                "session_key": result.get("sessionKey", "unknown"),
                "run_id": result.get("runId", "unknown")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"sessions_spawn נכשל: {str(e)}",
                "agent_id": agent_id,
                "domain": domain,
                "fallback_required": True
            }
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """מחזיר סטטוס agent"""
        if agent_id not in self.agents_registry:
            return {"status": "not_found", "agent_id": agent_id}
        
        config = self.agents_registry[agent_id] 
        return {
            "status": "configured",
            "agent_id": agent_id,
            "name": config["name"],
            "domain": config["domain"],
            "risk_level": config["riskLevel"],
            "allowed_actions": config["allowedActions"]
        }
    
    def list_available_agents(self) -> Dict[str, Any]:
        """מחזיר רשימת כל הagents הזמינים"""
        return {
            "total": len(self.agents_registry),
            "agents": {
                agent_id: {
                    "name": config["name"],
                    "domain": config["domain"], 
                    "agentId": config["agentId"],
                    "risk_level": config["riskLevel"]
                }
                for agent_id, config in self.agents_registry.items()
            }
        }

# Global instance
dispatcher = RealAgentDispatcher()

def dispatch_message(message: str, sessions_spawn_func) -> Dict[str, Any]:
    """
    Entry point: מנתב הודעה לagent המתאים
    """
    return dispatcher.dispatch_to_agent(message, sessions_spawn_func)

if __name__ == "__main__":
    # Test mode
    test_messages = [
        "בדקי חוזה שכירות", 
        "סכמי הודעות קבוצת אלון",
        "צרי פרסום Villa Lithos לTikTok",
        "חקרי מחירי נדלן"
    ]
    
    for msg in test_messages:
        domain, agent, conf = dispatcher.classify_message_domain(msg)
        print(f"'{msg}' → {agent} ({domain}, {conf:.1f})")