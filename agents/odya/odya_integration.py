#!/usr/bin/env python3
"""
Odya Integration - Connects professional Odya with the main system
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add workspace to path  
workspace = Path(__file__).parent.parent.parent
sys.path.append(str(workspace))

from agents.odya.professional_odya import ProfessionalOdya
from core.group_manager import GroupManager

class OdyaIntegration:
    def __init__(self, workspace_path: str = None):
        self.odya = ProfessionalOdya(workspace_path)
        self.group_manager = GroupManager(workspace_path)
    
    def handle_group_message(self, message: str, group_id: str, group_name: str = None,
                           sender: str = None, timestamp: str = None) -> Dict[str, Any]:
        """
        Handle a single group message and decide action
        Called by the router for whatsapp_group domain
        """
        
        # Create message structure
        msg_data = {
            "sender": {"name": sender or "Unknown"},
            "body": message,
            "timestamp": timestamp or ""
        }
        
        # Record activity
        self.group_manager.record_activity(group_id, 1)
        
        # Check if should reply
        should_reply, reason = self.odya.should_reply_to_group([msg_data], group_id)
        
        result = {
            "status": "processed",
            "group_id": group_id,
            "group_name": group_name,
            "message_recorded": True,
            "should_reply": should_reply,
            "reply_reason": reason,
            "reply_message": None,
            "actions_extracted": [],
            "dvorah_tasks": []
        }
        
        # If should reply, generate response
        if should_reply:
            reply_start_time = self._get_current_timestamp()
            
            # Generate contextual reply (simplified for now)
            if reason == "direct_mention":
                result["reply_message"] = "אני כאן, איך אני יכולה לעזור?"
            elif reason == "information_request":
                result["reply_message"] = "אבדוק ואחזור אליכם"
            elif reason == "action_request":
                result["reply_message"] = "✅ נרשם"
            
            # Record reply metrics
            response_time = self._get_current_timestamp() - reply_start_time
            self.group_manager.record_reply(group_id, helpful=True, response_time_sec=response_time)
        
        # Extract actions even if not replying
        actions = self.odya.extract_actions([msg_data], group_id)
        result["actions_extracted"] = actions
        
        # Add high-confidence actions to OPEN_TASKS
        high_conf_actions = [a for a in actions if a.get("owner_confidence", 0) >= 0.7]
        result["dvorah_tasks"] = self._convert_to_dvorah_tasks(high_conf_actions, group_name)
        
        return result
    
    def create_daily_summary(self, group_id: str, messages: List[Dict] = None,
                           days_back: int = 1, group_name: str = None) -> Dict[str, Any]:
        """
        Create daily summary for group (called by heartbeat)
        """
        
        if not messages:
            # In real implementation, fetch messages from WhatsApp API
            # For now, return empty summary
            return {
                "status": "no_messages",
                "group_id": group_id,
                "message": "אין הודעות חדשות לסיכום"
            }
        
        # Create professional summary
        summary = self.odya.create_group_summary(messages, group_id, group_name)
        
        # Format for output
        formatted_summary = self.odya.format_summary_for_output(summary)
        
        return {
            "status": "summary_created",
            "group_id": group_id,
            "group_name": group_name or summary.get("group_name"),
            "formatted_summary": formatted_summary,
            "raw_summary": summary,
            "should_send_to_target_group": len(summary.get("decisions", [])) > 0 or 
                                         len(summary.get("tasks", [])) > 0,
            "dvorah_actions": summary.get("dvorah_actions", [])
        }
    
    def _convert_to_dvorah_tasks(self, actions: List[Dict], group_name: str = None) -> List[Dict]:
        """Convert extracted actions to Dvorah task format"""
        tasks = []
        
        for action in actions:
            task = {
                "name": f"{action['action']} — {action['owner']}",
                "content": action['action'],
                "source": f"קבוצת {group_name or 'Unknown'}",
                "owner": action['owner'],
                "priority": "🟡" if action.get('priority') == 'medium' else "🟢",
                "deadline": action.get('deadline'),
                "confidence": action.get('owner_confidence', 0),
                "followup": "כל 3 ימים"
            }
            tasks.append(task)
        
        return tasks
    
    def _get_current_timestamp(self) -> int:
        """Get current timestamp in seconds"""
        import time
        return int(time.time())
    
    def get_group_stats(self, group_id: str = None) -> Dict[str, Any]:
        """Get statistics for group(s)"""
        if group_id:
            state = self.group_manager._load_group_state(group_id)
            return {
                "group_id": group_id,
                "group_name": state.get("group_name"),
                "message_count": state.get("message_count", 0),
                "summary_count": state.get("summary_count", 0),
                "open_items": len([i for i in state.get("open_items", []) 
                                 if i.get("status") == "open"]),
                "last_activity": state.get("last_activity"),
                "reply_stats": state.get("reply_stats", {}),
                "extraction_stats": state.get("extraction_stats", {})
            }
        else:
            groups = self.group_manager.list_groups()
            return {
                "total_groups": len(groups),
                "active_groups": len([g for g in groups if g.get("last_activity")]),
                "total_messages": sum(g.get("message_count", 0) for g in groups),
                "total_summaries": sum(g.get("summary_count", 0) for g in groups),
                "groups": groups
            }

# Heartbeat integration functions
def process_group_messages_for_summary(group_id: str, days: int = 1) -> Optional[str]:
    """
    Process group messages for daily summary (called from HEARTBEAT.md)
    Returns formatted summary or None if no activity
    """
    try:
        integration = OdyaIntegration()
        
        # In real implementation, this would fetch actual messages
        # For now, simulate with group manager data
        group_state = integration.group_manager._load_group_state(group_id)
        
        if not group_state.get("last_activity"):
            return None
        
        # Check if activity was recent enough
        from datetime import datetime, timedelta
        last_activity = datetime.fromisoformat(group_state["last_activity"])
        if datetime.now() - last_activity > timedelta(days=days):
            return None
        
        # Create summary (with empty messages for now - in real system would fetch actual)
        result = integration.create_daily_summary(group_id, messages=[], days_back=days, 
                                                group_name=group_state.get("group_name"))
        
        if result["status"] == "no_messages":
            return None
        
        return result["formatted_summary"]
        
    except Exception as e:
        print(f"Error processing group {group_id}: {e}")
        return None

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  odya_integration.py handle-message <group_id> '<message>' [sender]")
        print("  odya_integration.py daily-summary <group_id> [days_back]")
        print("  odya_integration.py stats [group_id]")
        return
    
    command = sys.argv[1]
    integration = OdyaIntegration()
    
    if command == "handle-message" and len(sys.argv) >= 4:
        group_id = sys.argv[2]
        message = sys.argv[3]
        sender = sys.argv[4] if len(sys.argv) > 4 else "Test User"
        
        result = integration.handle_group_message(message, group_id, sender=sender)
        
        print("📱 Group Message Handling:")
        print(f"  Should reply: {result['should_reply']} ({result['reply_reason']})")
        if result['reply_message']:
            print(f"  Reply: {result['reply_message']}")
        print(f"  Actions extracted: {len(result['actions_extracted'])}")
        print(f"  Dvorah tasks: {len(result['dvorah_tasks'])}")
        
        for task in result['dvorah_tasks']:
            print(f"    • {task['name']}")
    
    elif command == "daily-summary" and len(sys.argv) >= 3:
        group_id = sys.argv[2]
        days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        # Test with sample messages
        test_messages = [
            {"sender": {"name": "יוני"}, "body": "איך הולכת העבודה על הפרויקט?", "timestamp": "2026-03-24T14:00:00"},
            {"sender": {"name": "מתן"}, "body": "אני אסיים את הדוח עד מחר", "timestamp": "2026-03-24T14:15:00"},
            {"sender": {"name": "שרה"}, "body": "החלטנו לדחות את הפגישה לשבוע הבא", "timestamp": "2026-03-24T14:30:00"}
        ]
        
        result = integration.create_daily_summary(group_id, test_messages, days_back, "צוות בדיקה")
        
        if result["status"] == "summary_created":
            print("📋 Daily Summary Created:")
            print(result["formatted_summary"])
        else:
            print(f"📭 {result['message']}")
    
    elif command == "stats":
        group_id = sys.argv[2] if len(sys.argv) > 2 else None
        stats = integration.get_group_stats(group_id)
        
        print("📊 Group Statistics:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        print(f"❌ Unknown command or missing arguments")

if __name__ == "__main__":
    main()