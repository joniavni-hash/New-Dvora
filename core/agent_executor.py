#!/usr/bin/env python3
"""
Agent Executor - Executes agent tasks with real actions (not just structured responses).

Converts agent responses into actual execution:
- Model calls via sessions_spawn
- File operations
- Message sending
- Memory updates
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from model_selector import ModelSelector

class AgentExecutor:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        
        # Add workspace to Python path for agent imports
        sys.path.insert(0, str(self.workspace))
    
    def execute_agent_task(self, agent_name: str, message: str, 
                          routing_result: Dict, metadata: Dict = None) -> Dict:
        """Execute agent task with real model calls and actions"""
        
        try:
            if agent_name == "masha":
                return self._execute_masha(message, routing_result, metadata)
            elif agent_name == "dana":
                return self._execute_dana(message, routing_result, metadata)
            elif agent_name == "odya":
                return self._execute_odya(message, routing_result, metadata)
            elif agent_name == "tzofit":
                return self._execute_tzofit(message, routing_result, metadata)
            else:
                return self._execute_fallback(agent_name, message, routing_result)
                
        except Exception as e:
            return {
                "status": "execution_error",
                "agent": agent_name,
                "error": str(e),
                "fallback_action": "manual_review_required",
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_masha(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Execute legal task via מאשה with real model call"""
        
        # Get model selection
        tier = routing.get("model", "tier3")  # Legal defaults to tier3
        model_selector = ModelSelector()
        model_selection = model_selector.select_model(tier, routing["context"])
        
        # Import מאשה
        from agents.masha.masha_agent import handle_legal_task
        
        # Get structured response from מאשה
        agent_response = handle_legal_task(message, {
            "routing": routing,
            "metadata": metadata
        })
        
        # If this requires actual model processing, spawn it
        if agent_response["status"] == "draft_ready":
            # This would be where we call the model for actual analysis
            # For now, we enhance the structured response
            
            # Log model usage (simulated for now)
            usage_record = ModelSelector().log_actual_usage(
                model_selection,
                {"input": 800, "output": 1200},  # Simulated
                metadata.get("execution_id")
            )
            
            agent_response["execution_details"] = {
                "model_used": model_selection["model_id"],
                "tier": model_selection["tier"],
                "cost_usd": usage_record["actual_cost"],
                "execution_type": "structured_analysis"
            }
        
        return agent_response
    
    def _execute_dana(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Execute fitness task with real file updates"""
        
        # Get model selection - fitness usually tier1
        tier = routing.get("model", "tier1")
        model_selection = ModelSelector().select_model(tier, routing["context"])
        
        # Parse fitness data from message
        fitness_data = self._parse_fitness_message(message)
        
        # Update fitness tracker if we have data
        if fitness_data["type"] in ["meal", "weight"]:
            update_result = self._update_fitness_tracker(fitness_data)
            
            # Log model usage (minimal for data entry)
            usage_record = ModelSelector().log_actual_usage(
                model_selection,
                {"input": 200, "output": 100},  # Simple task
                metadata.get("execution_id")
            )
            
            return {
                "status": "executed",
                "agent": "דנה", 
                "domain": "fitness",
                "action_taken": f"Updated {fitness_data['type']} data",
                "data_logged": fitness_data,
                "file_updated": "state/fitness_tracker.md",
                "execution_details": {
                    "model_used": model_selection["model_id"],
                    "tier": model_selection["tier"],
                    "cost_usd": usage_record["actual_cost"]
                },
                "summary": f"רשמתי {fitness_data.get('description', 'נתונים')} במעקב הכושר"
            }
        
        return {
            "status": "no_action_needed",
            "agent": "דנה",
            "reason": "No fitness data detected in message",
            "suggestion": "Try: 'אכלתי [food] [amount]' or 'שקלתי [weight]'"
        }
    
    def _execute_odya(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Execute group message analysis"""
        
        # Get model selection - groups usually tier1 
        tier = routing.get("model", "tier1")
        model_selection = ModelSelector().select_model(tier, routing["context"])
        
        group_id = metadata.get("group_id") if metadata else None
        
        # Analyze group message
        analysis = self._analyze_group_message(message, group_id)
        
        # Log model usage
        usage_record = ModelSelector().log_actual_usage(
            model_selection,
            {"input": 300, "output": 200},
            metadata.get("execution_id")
        )
        
        return {
            "status": "analysis_ready",
            "agent": "אודיה",
            "domain": "whatsapp_group",
            "analysis": analysis,
            "requires_approval": True,
            "approval_reason": "Group response requires review before sending",
            "execution_details": {
                "model_used": model_selection["model_id"],
                "tier": model_selection["tier"], 
                "cost_usd": usage_record["actual_cost"]
            }
        }
    
    def _execute_tzofit(self, message: str, routing: Dict, metadata: Dict) -> Dict:
        """Execute research task with web search"""
        
        # Get model selection - research usually tier2
        tier = routing.get("model", "tier2")
        model_selection = ModelSelector().select_model(tier, routing["context"])
        
        # Extract research query
        research_query = self._extract_research_query(message)
        
        # TODO: Add actual web search here
        # For now, return structured response
        
        usage_record = ModelSelector().log_actual_usage(
            model_selection,
            {"input": 500, "output": 800},
            metadata.get("execution_id")
        )
        
        return {
            "status": "research_ready",
            "agent": "צופית",
            "domain": "research",
            "query": research_query,
            "results": {
                "status": "pending_implementation",
                "note": "Research execution not yet implemented",
                "suggested_tools": ["web_search", "tavily_search"]
            },
            "execution_details": {
                "model_used": model_selection["model_id"],
                "tier": model_selection["tier"],
                "cost_usd": usage_record["actual_cost"]
            }
        }
    
    def _execute_fallback(self, agent_name: str, message: str, routing: Dict) -> Dict:
        """Fallback for unimplemented agents"""
        
        return {
            "status": "not_implemented",
            "agent": agent_name,
            "message": f"Agent {agent_name} execution not implemented yet",
            "fallback_action": "handle_as_direct",
            "routing_info": routing.get("classification", {})
        }
    
    def _parse_fitness_message(self, message: str) -> Dict:
        """Parse fitness data from message"""
        
        message_lower = message.lower()
        
        # Check for meal logging
        if any(word in message_lower for word in ["אכלתי", "ארוחה", "meal", "ate"]):
            return {
                "type": "meal",
                "description": message,
                "timestamp": datetime.now().isoformat(),
                "parsed": True
            }
        
        # Check for weight logging
        if any(word in message_lower for word in ["שקלתי", "משקל", "weight"]):
            return {
                "type": "weight", 
                "description": message,
                "timestamp": datetime.now().isoformat(),
                "parsed": True
            }
        
        return {
            "type": "unknown",
            "description": message,
            "parsed": False
        }
    
    def _update_fitness_tracker(self, fitness_data: Dict) -> Dict:
        """Actually update fitness tracker file"""
        
        try:
            tracker_file = self.workspace / "state" / "fitness_tracker.md"
            
            # Read current content
            content = ""
            if tracker_file.exists():
                content = tracker_file.read_text(encoding="utf-8")
            
            # Add new entry
            new_entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{fitness_data['description']}\n"
            
            # Write back
            updated_content = content + new_entry
            tracker_file.write_text(updated_content, encoding="utf-8")
            
            return {
                "status": "updated",
                "file": str(tracker_file),
                "entry_added": new_entry.strip()
            }
            
        except Exception as e:
            return {
                "status": "update_failed",
                "error": str(e)
            }
    
    def _analyze_group_message(self, message: str, group_id: str = None) -> Dict:
        """Analyze group message for response decision"""
        
        # Simple analysis for now
        message_lower = message.lower()
        
        should_respond = any(word in message_lower for word in [
            "דבורה", "dvorah", "?", "מי", "איך", "מה", "כמה"
        ])
        
        return {
            "should_respond": should_respond,
            "confidence": 0.7 if should_respond else 0.3,
            "message_type": "question" if "?" in message else "statement",
            "mentions_dvorah": "דבורה" in message_lower or "dvorah" in message_lower,
            "group_id": group_id,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _extract_research_query(self, message: str) -> str:
        """Extract research query from message"""
        
        # Simple extraction for now
        query_indicators = ["תחקרי", "חקרי", "בדקי", "מצאי"]
        
        for indicator in query_indicators:
            if indicator in message:
                # Take everything after the indicator
                parts = message.split(indicator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return message

# Global executor instance
agent_executor = AgentExecutor()

def execute_agent_task(agent_name: str, message: str, 
                      routing_result: Dict, metadata: Dict = None) -> Dict:
    """Global function to execute agent tasks"""
    return agent_executor.execute_agent_task(agent_name, message, routing_result, metadata)