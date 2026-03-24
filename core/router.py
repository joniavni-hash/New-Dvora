#!/usr/bin/env python3
"""
Smart Router - Routes messages to appropriate domain agents with context loading.

Replaces the manual classification in AGENTS.md with automatic:
1. Message classification
2. Integration detection
3. Context loading 
4. Agent routing
5. Connection validation (NEW)
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from typing import Dict, List, Optional, Tuple
from context_guard import safe_read_file, context_status

class Router:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.registry = IntegrationRegistry(str(self.workspace))
        
        # Integration health monitoring
        try:
            from core.integration_health import IntegrationHealthMonitor
            self.health_monitor = IntegrationHealthMonitor(str(self.workspace))
        except ImportError:
            self.health_monitor = None
        
        # Classification patterns
        self.patterns = {
            "legal": [
                r"חוזה|הסכם|contract|legal",
                r"משפטי|דין|law|clause",
                r"סיכום.{0,10}חוזה|contract.{0,10}review",
                r"סעיף|תנאי|terms|condition"
            ],
            "fitness": [
                r"אכלתי|ארוחה|meal|ate",
                r"שקילה|משקל|weight|שקלתי",
                r"קלוריות|קק\"ל|calories|kcal",
                r"דיאטה|diet|תזונה|nutrition"
            ],
            "whatsapp_group": [
                r"group_message",
                r"שלום.*קבוצה|hello.*group"
            ],
            "research": [
                r"תחקרי|חקרי|research|investigate",
                r"בדקי|check|מצאי|find|חפשי",
                r"מה.*עם|what.*about|השוק|market",
                r"איך.*עובד|how.*works|ניתוח|analysis"
            ],
            "marketing": [
                r"פוסט|post|תוכן|content",
                r"טיקטוק|tiktok|instagram|social",
                r"שיווק|marketing|פרסום|advertising",
                r"וילה|villa|lithos|ליתוס"
            ],
            "automation": [
                r"סטטוס.*מערכת|system.*status|health.*check",
                r"בריאות.*מערכת|system.*health",
                r"מצב.*מערכת|system.*state",
                r"אוטומציה|automation|monitor"
            ],
            "scheduling": [
                r"מתי|when|תזכיר|remind",
                r"פגישה|meeting|appointment",
                r"יומן|calendar|schedule"
            ]
        }
    
    def classify_message(self, message: str, channel: str = None, 
                        group_id: str = None) -> Dict:
        """Classify message to determine domain and agent"""
        
        # Channel-based classification
        if channel == "whatsapp" and group_id:
            return {
                "domain": "whatsapp_group",
                "confidence": 0.9,
                "agent": "odya",
                "reason": f"WhatsApp group message (channel={channel}, group={group_id})"
            }
        
        # Content-based classification
        message_lower = message.lower()
        scores = {}
        
        for domain, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                scores[domain] = score / len(patterns)  # Normalize
        
        # Return highest scoring domain
        if scores:
            best_domain = max(scores, key=scores.get)
            confidence = min(scores[best_domain] * 2, 1.0)  # Scale to 0-1
            
            agent_map = {
                "legal": "masha",
                "fitness": "dana", 
                "whatsapp_group": "odya",
                "research": "tzofit",
                "scheduling": "eti",
                "marketing": "tali",
                "automation": "eti"
            }
            
            return {
                "domain": best_domain,
                "confidence": confidence,
                "agent": agent_map.get(best_domain, "direct"),
                "reason": f"Pattern match: {best_domain} (score: {scores[best_domain]:.2f})"
            }
        
        # Fallback to general
        return {
            "domain": "general",
            "confidence": 0.3,
            "agent": "direct",
            "reason": "No specific pattern matched - general routing"
        }
    
    def load_context(self, domain: str, message: str, 
                    channel: str = None, group_id: str = None) -> Dict:
        """Load relevant context files for domain"""
        
        context = {
            "files_loaded": [],
            "integrations_activated": [],
            "context_size": 0,
            "truncated": False
        }
        
        # Always load essentials
        essentials = ["IDENTITY.md", "SOUL.md", "USER.md"]
        for file in essentials:
            content = safe_read_file(file)
            if content and not content.startswith("[ERROR"):
                context["files_loaded"].append(file)
        
        # Load domain-specific context
        integration_files = self.registry.get_required_files(domain)
        for file in integration_files:
            content = safe_read_file(file, max_lines=100)  # Limit large files
            if content and not content.startswith("[ERROR"):
                context["files_loaded"].append(file)
                if "[TRUNCATED" in content:
                    context["truncated"] = True
        
        # Check context status
        status = context_status()
        context["context_size"] = status["chars"]
        
        if status["status"] == "warning":
            context["warning"] = "Approaching context limit"
        elif status["status"] == "critical":
            context["error"] = "Context limit exceeded - files truncated"
        
        return context
    
    def route_message(self, message: str, channel: str = None, 
                     group_id: str = None) -> Dict:
        """Main routing function - classify message and prepare context"""
        
        # Step 1: Classify
        classification = self.classify_message(message, channel, group_id)
        
        # Step 2: Load context
        context = self.load_context(classification["domain"], message, 
                                  channel, group_id)
        
        # Step 3: Select model tier
        model_tier = self._select_model_tier(classification["domain"], 
                                           classification["confidence"])
        
        return {
            "classification": classification,
            "context": context,
            "model": model_tier,
            "routing_decision": {
                "action": "route_to_agent" if classification["agent"] != "direct" else "handle_direct",
                "agent": classification["agent"],
                "domain": classification["domain"]
            },
            "metadata": {
                "channel": channel,
                "group_id": group_id,
                "message_length": len(message),
                "timestamp": "2026-03-24T07:54:00"
            }
        }
    
    def _select_model_tier(self, domain: str, confidence: float) -> str:
        """Select appropriate model tier based on domain and confidence"""
        
        # Domain-based model selection
        domain_tiers = {
            "legal": "tier3",  # Always use Opus for legal
            "whatsapp_group": "tier1",  # Usually simple
            "fitness": "tier1",  # Mostly data entry
            "research": "tier2",  # Needs analysis capability
            "marketing": "tier2",  # Creative content needs good model
            "automation": "tier1",  # System status is straightforward
            "scheduling": "tier1",  # Simple logic
            "general": "tier2"  # Default to mid-tier
        }
        
        base_tier = domain_tiers.get(domain, "tier2")
        
        # Don't downgrade marketing and research - they need good models
        if domain in ["marketing", "research"]:
            return base_tier
        
        # Adjust based on confidence for other domains
        if confidence < 0.5 and base_tier == "tier1":
            return "tier2"  # Uncertain simple tasks -> mid tier
        elif confidence > 0.8 and base_tier == "tier2":
            return "tier1"  # High confidence mid tasks -> cheap tier
        
        return base_tier

# Integration with existing system
class IntegrationRegistry:
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        registry_file = self.workspace / "core" / "integration_registry.json"
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception:
            # Fallback minimal config
            self.config = {"integrations": {}, "rules": {}}
    
    def get_required_files(self, domain: str) -> List[str]:
        """Get files required for a domain"""
        integration = self.config.get("integrations", {}).get(domain, {})
        return integration.get("required_files", [])
    
    def get_capabilities(self, domain: str) -> List[str]:
        """Get capabilities available for a domain"""
        integration = self.config.get("integrations", {}).get(domain, {})
        return integration.get("capabilities", [])

# Global router instance
router = Router()

def route_message(message: str, channel: str = None, group_id: str = None) -> Dict:
    """Global routing function - called by execution pipeline"""
    return router.route_message(message, channel, group_id)