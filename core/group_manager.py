#!/usr/bin/env python3
"""
Group Manager - Professional group conversation tracking and state management
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class GroupManager:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.groups_dir = self.workspace / "state" / "groups"
        self.groups_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_group_file(self, group_id: str) -> Path:
        """Get path to group state file"""
        # Sanitize group_id for filename
        safe_id = "".join(c for c in group_id if c.isalnum() or c in "._-")
        return self.groups_dir / f"{safe_id}.json"
    
    def _load_group_state(self, group_id: str) -> Dict[str, Any]:
        """Load group state from file"""
        group_file = self._get_group_file(group_id)
        
        if not group_file.exists():
            # Create default state for new group
            default_state = {
                "group_id": group_id,
                "group_name": f"Group {group_id[:8]}",
                "created_at": datetime.now().isoformat(),
                "last_activity": None,
                "last_summary": None,
                "message_count": 0,
                "open_items": [],
                "frequent_participants": [],
                "summary_count": 0,
                "reply_stats": {
                    "total_replies_today": 0,
                    "helpful_replies": 0,
                    "irrelevant_replies": 0,
                    "avg_response_time_sec": 0,
                    "last_reset": datetime.now().strftime("%Y-%m-%d")
                },
                "extraction_stats": {
                    "total_actions_extracted": 0,
                    "high_confidence_actions": 0,
                    "tasks_added_to_open": 0,
                    "last_extraction": None
                }
            }
            self._save_group_state(group_id, default_state)
            return default_state
        
        try:
            with open(group_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Warning: corrupted group state for {group_id}, recreating")
            return self._load_group_state(group_id)  # Recursive call to create default
    
    def _save_group_state(self, group_id: str, state: Dict[str, Any]):
        """Save group state to file"""
        group_file = self._get_group_file(group_id)
        state["updated_at"] = datetime.now().isoformat()
        
        with open(group_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def update_group_info(self, group_id: str, name: str = None, participants: List[str] = None):
        """Update basic group information"""
        state = self._load_group_state(group_id)
        
        if name:
            state["group_name"] = name
        
        if participants:
            # Update frequent participants (keep top 10)
            current_participants = state.get("frequent_participants", [])
            
            # Add new participants
            for participant in participants:
                if participant not in current_participants:
                    current_participants.append(participant)
            
            # Keep only the most frequent (simple approach: most recent)
            state["frequent_participants"] = current_participants[-10:]
        
        self._save_group_state(group_id, state)
        return state
    
    def record_activity(self, group_id: str, message_count: int = 1):
        """Record activity in group"""
        state = self._load_group_state(group_id)
        
        state["last_activity"] = datetime.now().isoformat()
        state["message_count"] = state.get("message_count", 0) + message_count
        
        self._save_group_state(group_id, state)
        return state
    
    def add_open_item(self, group_id: str, item: str, owner: str = None, deadline: str = None):
        """Add an open item that needs follow-up"""
        state = self._load_group_state(group_id)
        
        open_item = {
            "item": item,
            "owner": owner,
            "added_at": datetime.now().isoformat(),
            "deadline": deadline,
            "status": "open"
        }
        
        # Avoid duplicates
        for existing in state.get("open_items", []):
            if existing["item"].lower() == item.lower():
                return state  # Already exists
        
        if "open_items" not in state:
            state["open_items"] = []
        
        state["open_items"].append(open_item)
        
        # Keep only the 20 most recent open items
        state["open_items"] = state["open_items"][-20:]
        
        self._save_group_state(group_id, state)
        return state
    
    def close_item(self, group_id: str, item_text: str):
        """Mark an open item as closed"""
        state = self._load_group_state(group_id)
        
        for item in state.get("open_items", []):
            if item_text.lower() in item["item"].lower():
                item["status"] = "closed"
                item["closed_at"] = datetime.now().isoformat()
                break
        
        self._save_group_state(group_id, state)
        return state
    
    def record_summary(self, group_id: str, summary_data: Dict[str, Any]):
        """Record that a summary was created"""
        state = self._load_group_state(group_id)
        
        state["last_summary"] = datetime.now().isoformat()
        state["summary_count"] = state.get("summary_count", 0) + 1
        
        # Store summary metadata
        if "recent_summaries" not in state:
            state["recent_summaries"] = []
        
        summary_meta = {
            "timestamp": datetime.now().isoformat(),
            "message_count": summary_data.get("message_count", 0),
            "decisions_count": len(summary_data.get("decisions", [])),
            "tasks_count": len(summary_data.get("tasks", [])),
            "open_items_count": len(summary_data.get("open_items", []))
        }
        
        state["recent_summaries"].append(summary_meta)
        
        # Keep only last 10 summaries
        state["recent_summaries"] = state["recent_summaries"][-10:]
        
        self._save_group_state(group_id, state)
        return state
    
    def record_reply(self, group_id: str, helpful: bool = True, response_time_sec: int = 0):
        """Record a reply from Odya"""
        state = self._load_group_state(group_id)
        
        # Reset daily stats if needed
        today = datetime.now().strftime("%Y-%m-%d")
        if state["reply_stats"]["last_reset"] != today:
            state["reply_stats"] = {
                "total_replies_today": 0,
                "helpful_replies": 0,
                "irrelevant_replies": 0,
                "avg_response_time_sec": 0,
                "last_reset": today
            }
        
        # Update stats
        stats = state["reply_stats"]
        stats["total_replies_today"] += 1
        
        if helpful:
            stats["helpful_replies"] += 1
        else:
            stats["irrelevant_replies"] += 1
        
        # Update average response time
        if response_time_sec > 0:
            current_avg = stats["avg_response_time_sec"]
            total_replies = stats["total_replies_today"]
            new_avg = ((current_avg * (total_replies - 1)) + response_time_sec) / total_replies
            stats["avg_response_time_sec"] = round(new_avg, 1)
        
        self._save_group_state(group_id, state)
        return state
    
    def record_extraction(self, group_id: str, actions_extracted: int, high_confidence: int, tasks_added: int):
        """Record action extraction results"""
        state = self._load_group_state(group_id)
        
        stats = state["extraction_stats"]
        stats["total_actions_extracted"] += actions_extracted
        stats["high_confidence_actions"] += high_confidence
        stats["tasks_added_to_open"] += tasks_added
        stats["last_extraction"] = datetime.now().isoformat()
        
        self._save_group_state(group_id, state)
        return state
    
    def get_group_context(self, group_id: str) -> str:
        """Get formatted context for this group to include in prompts"""
        state = self._load_group_state(group_id)
        
        context = f"קבוצה: {state['group_name']}\n"
        
        # Recent activity
        if state.get("last_activity"):
            last_activity = datetime.fromisoformat(state["last_activity"])
            hours_ago = (datetime.now() - last_activity).total_seconds() / 3600
            if hours_ago < 24:
                context += f"פעילות אחרונה: לפני {hours_ago:.1f} שעות\n"
        
        # Open items
        open_items = [item for item in state.get("open_items", []) if item.get("status") == "open"]
        if open_items:
            context += "\nפריטים פתוחים מסיכומים קודמים:\n"
            for item in open_items[-5:]:  # Last 5
                owner_part = f" ← {item['owner']}" if item.get("owner") else ""
                context += f"- {item['item']}{owner_part}\n"
        
        # Frequent participants
        if state.get("frequent_participants"):
            participants = ", ".join(state["frequent_participants"][-5:])
            context += f"\nמשתתפים פעילים: {participants}\n"
        
        # Summary stats
        if state.get("summary_count", 0) > 0:
            context += f"\nסה״כ סיכומים: {state['summary_count']}\n"
        
        return context.strip()
    
    def list_groups(self) -> List[Dict[str, Any]]:
        """List all tracked groups with summary info"""
        groups = []
        
        for group_file in self.groups_dir.glob("*.json"):
            try:
                with open(group_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                groups.append({
                    "group_id": state.get("group_id"),
                    "group_name": state.get("group_name"),
                    "last_activity": state.get("last_activity"),
                    "message_count": state.get("message_count", 0),
                    "summary_count": state.get("summary_count", 0),
                    "open_items": len([i for i in state.get("open_items", []) 
                                     if i.get("status") == "open"])
                })
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        # Sort by last activity
        groups.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
        return groups
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old data from group states"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for group_file in self.groups_dir.glob("*.json"):
            try:
                state = self._load_group_state(group_file.stem)
                
                # Clean old open items
                if "open_items" in state:
                    state["open_items"] = [
                        item for item in state["open_items"]
                        if datetime.fromisoformat(item["added_at"]) > cutoff_date
                    ]
                
                # Clean old summary metadata
                if "recent_summaries" in state:
                    state["recent_summaries"] = [
                        summary for summary in state["recent_summaries"]
                        if datetime.fromisoformat(summary["timestamp"]) > cutoff_date
                    ]
                
                self._save_group_state(group_file.stem, state)
                
            except Exception as e:
                print(f"Error cleaning up {group_file}: {e}")

# Global instance
group_manager = GroupManager()

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  group_manager.py list                              # List all groups")
        print("  group_manager.py info <group_id>                   # Get group info")
        print("  group_manager.py context <group_id>                # Get group context")
        print("  group_manager.py add-item <group_id> '<item>'      # Add open item")
        print("  group_manager.py close-item <group_id> '<item>'    # Close item")
        print("  group_manager.py cleanup [days]                    # Cleanup old data")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        groups = group_manager.list_groups()
        print(f"📋 {len(groups)} tracked groups:")
        for group in groups:
            activity = "never" if not group["last_activity"] else group["last_activity"][:10]
            print(f"  🏢 {group['group_name']} ({group['group_id'][:8]}...)")
            print(f"      📊 {group['message_count']} messages, {group['summary_count']} summaries")
            print(f"      📅 Last: {activity}, Open items: {group['open_items']}")
            print()
    
    elif command == "info" and len(sys.argv) > 2:
        group_id = sys.argv[2]
        state = group_manager._load_group_state(group_id)
        print(f"📊 Group Info: {state['group_name']}")
        print(json.dumps(state, indent=2, ensure_ascii=False))
    
    elif command == "context" and len(sys.argv) > 2:
        group_id = sys.argv[2]
        context = group_manager.get_group_context(group_id)
        print("📝 Group Context:")
        print(context)
    
    elif command == "add-item" and len(sys.argv) > 3:
        group_id = sys.argv[2]
        item = sys.argv[3]
        owner = sys.argv[4] if len(sys.argv) > 4 else None
        group_manager.add_open_item(group_id, item, owner)
        print(f"✅ Added open item: {item}")
    
    elif command == "close-item" and len(sys.argv) > 3:
        group_id = sys.argv[2]
        item = sys.argv[3]
        group_manager.close_item(group_id, item)
        print(f"✅ Closed item: {item}")
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        group_manager.cleanup_old_data(days)
        print(f"✅ Cleaned up data older than {days} days")
    
    else:
        print("❌ Unknown command or missing arguments")

if __name__ == "__main__":
    main()