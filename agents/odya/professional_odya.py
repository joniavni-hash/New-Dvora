#!/usr/bin/env python3
"""
Professional Odya - Structured group conversation handler with 3 operation modes
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Add workspace to path
workspace = Path(__file__).parent.parent.parent
sys.path.append(str(workspace))

from core.group_manager import GroupManager

class ProfessionalOdya:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or workspace)
        self.group_manager = GroupManager(str(self.workspace))
        
        # Load formatting specifications
        self._load_formats()
    
    def _load_formats(self):
        """Load group format specifications from markdown files"""
        agents_dir = self.workspace / "agents" / "odya"
        
        # Load summary format
        summary_file = agents_dir / "GROUP_SUMMARY_FORMATS.md"
        self.summary_format = summary_file.read_text() if summary_file.exists() else ""
        
        # Load action extraction format
        action_file = agents_dir / "GROUP_ACTION_EXTRACTION.md"
        self.action_format = action_file.read_text() if action_file.exists() else ""
        
        # Load reply policy
        reply_file = agents_dir / "GROUP_REPLY_POLICY.md"
        self.reply_policy = reply_file.read_text() if reply_file.exists() else ""
    
    def should_reply_to_group(self, messages: List[Dict], group_id: str) -> Tuple[bool, str]:
        """
        Determine if Odya should reply to the current group conversation
        Returns: (should_reply, reason)
        """
        if not messages:
            return False, "no_messages"
        
        latest_message = messages[-1] if messages else {}
        message_text = latest_message.get("body", "").strip()
        
        # Check for direct mentions
        if any(mention in message_text.lower() for mention in ["@דבורה", "דבורה", "@odya"]):
            return True, "direct_mention"
        
        # Check for questions that Odya might know
        question_patterns = [
            r"מתי.+\?",  # When questions
            r"מי.+\?",   # Who questions  
            r"כמה.+\?",  # How much questions
            r"איפה.+\?", # Where questions
            r"מה.+(החלטה|הסכים|נקבע).+\?" # Decision questions
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, message_text):
                return True, "information_request"
        
        # Check for requests for action
        action_patterns = [
            r"תוסיפי?.+למשימות",
            r"תזכירי?.+ל",
            r"תעדכני?.+ש",
            r"תבדקי?.+עם"
        ]
        
        for pattern in action_patterns:
            if re.search(pattern, message_text):
                return True, "action_request"
        
        # Check if group is too active (>5 messages in 10 minutes)
        if len(messages) >= 5:
            recent_messages = 0
            now = datetime.now()
            for msg in reversed(messages):
                msg_time = self._parse_timestamp(msg.get("timestamp"))
                if msg_time and (now - msg_time).total_seconds() < 600:  # 10 minutes
                    recent_messages += 1
                else:
                    break
            
            if recent_messages >= 5:
                return False, "too_active"
        
        return False, "no_trigger"
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if not timestamp_str:
            return None
        
        try:
            # Try common formats
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", 
                "%Y-%m-%dT%H:%M:%S",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            return None
        except:
            return None
    
    def extract_actions(self, messages: List[Dict], group_id: str) -> List[Dict[str, Any]]:
        """
        Extract actionable items from group messages using structured approach
        """
        actions = []
        
        # Action detection patterns
        action_patterns = [
            r"(.+) (אבדוק|אטפל|אכין|אכתוב|אשלח|אתקשר|אעשה) (.+)",
            r"(.+) (תבדוק|תטפל|תכין|תכתוב|תשלח|תתקשר|תעשה) (.+)", 
            r"(.+) (יבדוק|יטפל|יכין|יכתוב|ישלח|יתקשר|יעשה) (.+)",
            r"(אני )?אקח על (.+)",
            r"(.+) צריך לטפל ב(.+)",
            r"מי יכול ל(.+)\?"
        ]
        
        for msg in messages:
            message_text = msg.get("body", "")
            sender = msg.get("sender", {}).get("name", "לא ידוע")
            timestamp = msg.get("timestamp", "")
            
            for pattern in action_patterns:
                matches = re.finditer(pattern, message_text, re.IGNORECASE)
                
                for match in matches:
                    # Extract action components
                    groups = match.groups()
                    
                    if len(groups) >= 2:
                        potential_owner = groups[0].strip() if groups[0] else sender
                        action_verb = groups[1] if len(groups) > 1 else ""
                        action_object = groups[2] if len(groups) > 2 else groups[1]
                        
                        # Determine confidence based on pattern clarity
                        confidence = self._calculate_confidence(match.group(0), sender, potential_owner)
                        
                        if confidence >= 0.5:  # Only extract if reasonably confident
                            # Look for deadline in message
                            deadline, deadline_type = self._extract_deadline(message_text)
                            
                            action = {
                                "action": f"{action_verb} {action_object}".strip(),
                                "owner": self._normalize_owner(potential_owner, sender),
                                "owner_confidence": confidence,
                                "deadline": deadline,
                                "deadline_type": deadline_type,
                                "context": match.group(0),
                                "message_timestamp": timestamp,
                                "priority": self._determine_priority(message_text, deadline),
                                "status": "new"
                            }
                            
                            actions.append(action)
        
        # Record extraction stats
        high_confidence = len([a for a in actions if a["owner_confidence"] >= 0.7])
        self.group_manager.record_extraction(group_id, len(actions), high_confidence, 0)
        
        return actions
    
    def _calculate_confidence(self, match_text: str, sender: str, potential_owner: str) -> float:
        """Calculate confidence score for action extraction"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for first-person commitments
        if any(word in match_text.lower() for word in ["אני", "אקח", "אבדוק", "אטפל"]):
            confidence += 0.3
        
        # Higher confidence for specific assignments
        if potential_owner != sender and potential_owner not in ["מישהו", "מי"]:
            confidence += 0.2
        
        # Lower confidence for questions
        if "?" in match_text:
            confidence -= 0.2
        
        # Lower confidence for conditional statements  
        if any(word in match_text.lower() for word in ["אם", "אולי", "נראה לי"]):
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _extract_deadline(self, message_text: str) -> Tuple[Optional[str], str]:
        """Extract deadline from message text"""
        deadline_patterns = [
            (r"עד (יום )?(ראשון|שני|שלישי|רביעי|חמישי|שישי|שבת)", "explicit"),
            (r"עד מחר", "explicit"),
            (r"עד (\d{1,2}[./]\d{1,2})", "explicit"),
            (r"עד סוף השבוע", "explicit"),
            (r"תוך (\d+) ימים", "relative"),
            (r"לפני הפגישה", "conditional"),
        ]
        
        for pattern, deadline_type in deadline_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                return match.group(0), deadline_type
        
        return None, "none"
    
    def _normalize_owner(self, potential_owner: str, sender: str) -> str:
        """Normalize owner name"""
        # Handle first-person references
        if potential_owner.lower() in ["אני", "אקח", "אבצע"]:
            return sender
        
        # Handle generic references
        if potential_owner.lower() in ["מישהו", "מי שיכול", "אחד מכם"]:
            return "TBD"
        
        return potential_owner.strip()
    
    def _determine_priority(self, message_text: str, deadline: Optional[str]) -> str:
        """Determine task priority"""
        # High priority indicators
        if any(word in message_text.lower() for word in ["דחוף", "מיידי", "היום", "עכשיו"]):
            return "high"
        
        # Medium priority if has deadline
        if deadline:
            return "medium"
        
        return "low"
    
    def create_group_summary(self, messages: List[Dict], group_id: str, 
                           group_name: str = None) -> Dict[str, Any]:
        """
        Create structured group summary following professional format
        """
        if not messages:
            return {"error": "No messages to summarize"}
        
        # Update group activity
        self.group_manager.record_activity(group_id, len(messages))
        if group_name:
            self.group_manager.update_group_info(group_id, group_name)
        
        # Get group context for better summaries
        group_context = self.group_manager.get_group_context(group_id)
        
        # Extract key components
        decisions = self._extract_decisions(messages)
        tasks = self.extract_actions(messages, group_id)
        participants = self._extract_participants(messages)
        main_topic = self._identify_main_topic(messages)
        open_items = self._identify_open_items(messages)
        
        # Update group manager with new data
        for participant in participants:
            self.group_manager.update_group_info(group_id, participants=[participant])
        
        for item in open_items:
            self.group_manager.add_open_item(group_id, item["item"], item.get("owner"))
        
        # Create structured summary
        time_range = self._calculate_time_range(messages)
        
        summary = {
            "group_id": group_id,
            "group_name": group_name or f"Group {group_id[:8]}",
            "timestamp": datetime.now().isoformat(),
            "time_range": time_range,
            "message_count": len(messages),
            "main_topic": main_topic,
            "decisions": decisions,
            "tasks": tasks,
            "open_items": open_items,
            "participants": participants,
            "group_context": group_context,
            "dvorah_actions": self._identify_dvorah_actions(messages, tasks)
        }
        
        # Record summary in group manager
        self.group_manager.record_summary(group_id, summary)
        
        return summary
    
    def _extract_decisions(self, messages: List[Dict]) -> List[Dict[str, str]]:
        """Extract decisions from messages"""
        decisions = []
        decision_patterns = [
            r"החלטנו ש(.+)",
            r"(.+) החליט ש(.+)",
            r"נקבע ש(.+)",
            r"הסכמנו ש(.+)"
        ]
        
        for msg in messages:
            message_text = msg.get("body", "")
            sender = msg.get("sender", {}).get("name", "")
            
            for pattern in decision_patterns:
                matches = re.finditer(pattern, message_text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1) if "החליט" not in pattern else match.group(2)
                    decider = match.group(1) if "החליט" in pattern else "הקבוצה"
                    
                    decisions.append({
                        "decision": decision_text.strip(),
                        "decided_by": decider,
                        "timestamp": msg.get("timestamp", "")
                    })
        
        return decisions
    
    def _extract_participants(self, messages: List[Dict]) -> List[str]:
        """Extract active participants from messages"""
        participants = set()
        
        for msg in messages:
            sender_name = msg.get("sender", {}).get("name")
            if sender_name and sender_name not in ["דבורה", "Dvorah", "Bot"]:
                participants.add(sender_name)
        
        return list(participants)
    
    def _identify_main_topic(self, messages: List[Dict]) -> str:
        """Identify the main topic of conversation"""
        # Simple keyword frequency approach
        all_text = " ".join([msg.get("body", "") for msg in messages])
        
        # Common topic keywords
        topic_keywords = {
            "פגישה": "תיאום פגישות",
            "פרויקט": "ניהול פרויקט", 
            "תקציב": "נושאים כספיים",
            "שיווק": "פעילות שיווקית",
            "לקוח": "שירות לקוחות",
            "מועד": "תכנון לוחות זמנים"
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in all_text:
                return topic
        
        # Fallback: use first few words of first substantive message
        for msg in messages:
            body = msg.get("body", "").strip()
            if body and len(body) > 10:
                words = body.split()[:5]
                return " ".join(words) + "..."
        
        return "דיון כללי"
    
    def _identify_open_items(self, messages: List[Dict]) -> List[Dict[str, str]]:
        """Identify items that remain open for follow-up"""
        open_items = []
        
        # Look for unresolved questions and issues
        open_patterns = [
            r"עדיין (צריך|חייב) ל(.+)",
            r"נותר לבדוק (.+)",
            r"מה עם (.+)\?",
            r"לא הוחלט על (.+)"
        ]
        
        for msg in messages:
            message_text = msg.get("body", "")
            
            for pattern in open_patterns:
                matches = re.finditer(pattern, message_text, re.IGNORECASE)
                for match in matches:
                    item_text = match.group(1) if "צריך" in match.group(0) else match.group(1)
                    
                    open_items.append({
                        "item": item_text.strip(),
                        "mentioned_by": msg.get("sender", {}).get("name", ""),
                        "timestamp": msg.get("timestamp", "")
                    })
        
        return open_items
    
    def _identify_dvorah_actions(self, messages: List[Dict], tasks: List[Dict]) -> List[str]:
        """Identify actions that Dvorah needs to take"""
        dvorah_actions = []
        
        # Look for explicit requests to Dvorah
        for msg in messages:
            message_text = msg.get("body", "")
            if any(name in message_text for name in ["דבורה", "Dvorah"]):
                # Extract action requests
                if "תזכיר" in message_text:
                    dvorah_actions.append("הוספת תזכורת לפי הודעה")
                elif "תוסיף" in message_text:
                    dvorah_actions.append("הוספת פריט למשימות")
                elif "תבדוק" in message_text:
                    dvorah_actions.append("בדיקה ודיווח חזרה")
        
        # Add high-confidence tasks to tracking
        high_conf_tasks = [t for t in tasks if t.get("owner_confidence", 0) >= 0.7]
        if high_conf_tasks:
            dvorah_actions.append(f"מעקב אחרי {len(high_conf_tasks)} משימות שחולצו")
        
        return dvorah_actions if dvorah_actions else ["אין פעולה נדרשת"]
    
    def _calculate_time_range(self, messages: List[Dict]) -> str:
        """Calculate time range of conversation"""
        if not messages:
            return "לא ידוע"
        
        timestamps = [self._parse_timestamp(msg.get("timestamp", "")) for msg in messages]
        timestamps = [t for t in timestamps if t is not None]
        
        if not timestamps:
            return "לא ידוע"
        
        earliest = min(timestamps)
        latest = max(timestamps)
        duration = latest - earliest
        
        hours = duration.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(duration.total_seconds() / 60)} דקות"
        elif hours < 24:
            return f"{hours:.1f} שעות"
        else:
            days = duration.days
            return f"{days} ימים"
    
    def format_summary_for_output(self, summary: Dict[str, Any]) -> str:
        """Format summary according to professional structure"""
        formatted = f"""📋 סיכום קבוצה — {summary['group_name']} | {summary['timestamp'][:10]}
⏰ תקופה: {summary['message_count']} הודעות מ-{summary['time_range']}

🎯 **נושא עיקרי:**
{summary['main_topic']}

✅ **החלטות:**"""
        
        if summary['decisions']:
            for decision in summary['decisions']:
                formatted += f"\n- {decision['decision']} ← {decision['decided_by']}"
        else:
            formatted += "\n- לא נתקבלו החלטות"
        
        formatted += "\n\n📋 **משימות:**"
        if summary['tasks']:
            for task in summary['tasks']:
                confidence_indicator = "⭐" if task.get('owner_confidence', 0) >= 0.8 else ""
                deadline_part = f" | {task['deadline']}" if task.get('deadline') else ""
                formatted += f"\n- [ ] {task['action']} ← {task['owner']}{confidence_indicator}{deadline_part}"
        else:
            formatted += "\n- לא נוצרו משימות"
        
        formatted += "\n\n🔴 **דורש מעקב מדבורה:**"
        for action in summary['dvorah_actions']:
            formatted += f"\n- {action}"
        
        formatted += "\n\n⚠️ **נותר פתוח:**"
        if summary['open_items']:
            for item in summary['open_items']:
                formatted += f"\n- {item['item']}"
        else:
            formatted += "\n- כל הנושאים נסגרו"
        
        formatted += f"\n\n👥 **משתתפים פעילים:**\n{', '.join(summary['participants'])}"
        
        return formatted

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  professional_odya.py test-summary    # Test summary creation")
        print("  professional_odya.py test-actions    # Test action extraction")
        print("  professional_odya.py test-reply      # Test reply logic")
        return
    
    command = sys.argv[1]
    odya = ProfessionalOdya()
    
    if command == "test-summary":
        # Test with sample messages
        test_messages = [
            {
                "sender": {"name": "יוני"},
                "body": "בואו נדון על הפרויקט החדש",
                "timestamp": "2026-03-24T14:00:00"
            },
            {
                "sender": {"name": "מתן"},
                "body": "אני אבדוק את התקציב עד מחר",
                "timestamp": "2026-03-24T14:05:00"
            },
            {
                "sender": {"name": "יוני"},
                "body": "החלטנו שנתחיל בתחילת השבוע הבא",
                "timestamp": "2026-03-24T14:10:00"
            }
        ]
        
        summary = odya.create_group_summary(test_messages, "test_group", "צוות פיתוח")
        formatted = odya.format_summary_for_output(summary)
        print("📋 Test Summary:")
        print(formatted)
    
    elif command == "test-actions":
        test_messages = [
            {"sender": {"name": "יוני"}, "body": "מתן תבדוק את המחירים עד יום חמישי", "timestamp": "2026-03-24T14:00:00"},
            {"sender": {"name": "שרה"}, "body": "אני אכין את המצגת לפגישה", "timestamp": "2026-03-24T14:05:00"},
            {"sender": {"name": "דני"}, "body": "מישהו צריך לטפל בנושא הביטוח", "timestamp": "2026-03-24T14:10:00"}
        ]
        
        actions = odya.extract_actions(test_messages, "test_group")
        print("⚙️ Extracted Actions:")
        for action in actions:
            print(f"  • {action['action']} ← {action['owner']} (confidence: {action['owner_confidence']:.2f})")
    
    elif command == "test-reply":
        test_messages = [
            {"sender": {"name": "יוני"}, "body": "@דבורה מתי הפגישה מחר?", "timestamp": "2026-03-24T14:00:00"}
        ]
        
        should_reply, reason = odya.should_reply_to_group(test_messages, "test_group")
        print(f"🤖 Should reply: {should_reply} (reason: {reason})")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()