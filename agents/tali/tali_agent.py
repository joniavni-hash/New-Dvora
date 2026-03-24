#!/usr/bin/env python3
"""
טלי - Marketing Agent
מומחית שיווק דיגיטלי, TikTok, פרסום
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add workspace to path
workspace_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_path))

class TaliAgent:
    """טלי - סוכנת שיווק דיגיטלי"""
    
    def __init__(self):
        self.name = "טלי"
        self.domain = "marketing"
        self.skills = ["larry-marketing", "social-media", "content-creation", "tiktok-automation"]
        
    def execute_task(self, task: str, context: dict = None) -> dict:
        """בצע משימת שיווק"""
        
        print(f"🎬 {self.name} מתחילה עבודה: {task[:60]}...")
        
        # Analyze task
        task_lower = task.lower()
        
        if "villa lithos" in task_lower and "tiktok" in task_lower:
            return self._handle_villa_lithos_tiktok(task, context)
        elif "larry" in task_lower:
            return self._handle_larry_marketing(task, context)
        elif "social media" in task_lower:
            return self._handle_social_media(task, context)
        else:
            return self._handle_general_marketing(task, context)
    
    def _handle_villa_lithos_tiktok(self, task: str, context: dict) -> dict:
        """טפל בפרסום Villa Lithos לTikTok"""
        
        print("🏖️ מזהה: Villa Lithos TikTok campaign")
        
        # Import Larry skill
        try:
            import subprocess
            
            # Check if Larry skill exists
            larry_skill_path = workspace_path / "skills" / "larry-marketing"
            if not larry_skill_path.exists():
                return {
                    "status": "error",
                    "message": "Larry skill not found",
                    "agent": self.name
                }
            
            print("📚 Larry skill זמין - מתחילה יצירת תוכן...")
            
            # Use existing Villa Lithos automation
            automation_script = workspace_path / "integrations" / "social" / "tiktok_direct_photo_post.py"
            if automation_script.exists():
                print("🤖 מפעילה TikTok automation קיים...")
                
                result = subprocess.run(
                    ["python3", str(automation_script)],
                    cwd=str(workspace_path / "integrations" / "social"),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return {
                        "status": "success",
                        "message": "Villa Lithos TikTok campaign הופעל בהצלחה",
                        "agent": self.name,
                        "output": result.stdout,
                        "method": "existing_automation",
                        "platforms": ["tiktok"],
                        "content_type": "larry_slideshow"
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "TikTok automation נכשל",
                        "agent": self.name,
                        "error": result.stderr,
                        "output": result.stdout
                    }
            
            else:
                return {
                    "status": "error",
                    "message": "TikTok automation script לא נמצא",
                    "agent": self.name
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"שגיאה בביצוע: {str(e)}",
                "agent": self.name
            }
    
    def _handle_larry_marketing(self, task: str, context: dict) -> dict:
        """טפל במשימות Larry marketing"""
        
        return {
            "status": "success",
            "message": "Larry marketing method מזוהה",
            "agent": self.name,
            "recommendations": [
                "השתמש ב-6 slides עם hook structure",
                "DIRECT_POST עם autoAddMusic",
                "מעקב ביצועים אחרי פרסום"
            ]
        }
    
    def _handle_social_media(self, task: str, context: dict) -> dict:
        """טפל במשימות רשתות חברתיות כלליות"""
        
        return {
            "status": "success", 
            "message": "משימת רשתות חברתיות מזוהה",
            "agent": self.name,
            "capabilities": [
                "TikTok automation",
                "Instagram posts", 
                "Pinterest boards",
                "Facebook campaigns"
            ]
        }
    
    def _handle_general_marketing(self, task: str, context: dict) -> dict:
        """טפל במשימות שיווק כלליות"""
        
        return {
            "status": "success",
            "message": f"משימת שיווק כללית: {task[:100]}",
            "agent": self.name,
            "next_steps": [
                "ניתוח יעד ההודעה",
                "בחירת פלטפורמות מתאימות",
                "יצירת תוכן",
                "פרסום ומעקב"
            ]
        }
    
    def test(self) -> dict:
        """בדיקת זמינות"""
        return {
            "agent": self.name,
            "status": "available",
            "domain": self.domain,
            "skills": self.skills,
            "test_time": datetime.now().isoformat()
        }

def main():
    parser = argparse.ArgumentParser(description='טלי - Marketing Agent')
    parser.add_argument('--task', help='Marketing task')
    parser.add_argument('--context', help='Context JSON')
    parser.add_argument('--test', action='store_true', help='Test agent availability')
    
    args = parser.parse_args()
    
    tali = TaliAgent()
    
    if args.test:
        result = tali.test()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    if not args.task:
        print("❌ Task required when not testing", file=sys.stderr)
        sys.exit(1)
    
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            print(f"❌ Context JSON error: {e}", file=sys.stderr)
            sys.exit(1)
    
    result = tali.execute_task(args.task, context)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()