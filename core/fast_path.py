#!/usr/bin/env python3
"""
Fast Path System - Speed and cost optimization for common requests
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

class FastPathRouter:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.cache_dir = self.workspace / "cache" / "fast_path"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "status_queries": 300,      # 5 minutes
            "simple_responses": 1800,   # 30 minutes  
            "system_info": 3600,        # 1 hour
            "integration_status": 900   # 15 minutes
        }
        
        # Load fast path patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns that can be handled via fast path"""
        
        # L0: Instant cache responses (no model needed)
        self.l0_patterns = [
            r"(?:מה ה)?סטטוס(?:\?)?$",
            r"(?:איך )?עובד(?:\?)?$", 
            r"מה קורה(?:\?)?$",
            r"תקין(?:\?)?$",
            r"בריא(?:\?)?$"
        ]
        
        # L1: Simple queries (tier1 model, minimal context)
        self.l1_patterns = [
            r"(?:מה ה)?שעה(?:\?)?$",
            r"(?:איזה )?תאריך(?:\?)?$",
            r"(?:איזה )?יום(?:\?)?$",
            r"תודה$|thanks?$|אוקי$|ok$",
            r"שלום$|היי$|hello$|בוקר טוב$",
            r"(?:מה ה)?מזג אוויר(?:\?)?$",
            r"כמה הזמן(?:\?)?$"
        ]
        
        # Common status queries that can use cached data
        self.status_patterns = [
            r"(?:מה ה)?משימות(?:\?)?$",
            r"(?:מה ה)?פתוח(?:\?)?$", 
            r"(?:איך ה)?מיילים(?:\?)?$",
            r"(?:מה עם ה)?קבוצות(?:\?)?$"
        ]
    
    def classify_request(self, message: str, channel: str = "direct") -> Dict[str, Any]:
        """
        Classify request for fast path routing
        
        Returns:
            level: "L0", "L1", "L2" 
            confidence: 0.0-1.0
            reason: why this level was chosen
            cache_key: for caching if applicable
        """
        
        message_clean = message.strip().lower()
        
        # L0: Instant responses from cache
        for pattern in self.l0_patterns:
            import re
            if re.search(pattern, message_clean):
                return {
                    "level": "L0",
                    "confidence": 0.95,
                    "reason": "status_query",
                    "cache_key": self._generate_cache_key("status", message_clean),
                    "estimated_cost": 0.0,
                    "estimated_time_ms": 10
                }
        
        # L1: Simple queries
        for pattern in self.l1_patterns:
            import re
            if re.search(pattern, message_clean):
                return {
                    "level": "L1", 
                    "confidence": 0.9,
                    "reason": "simple_query",
                    "cache_key": self._generate_cache_key("simple", message_clean),
                    "estimated_cost": 0.001,  # tier1 model
                    "estimated_time_ms": 200
                }
        
        # Check for status patterns that can use cached data
        for pattern in self.status_patterns:
            import re
            if re.search(pattern, message_clean):
                return {
                    "level": "L1",
                    "confidence": 0.85,
                    "reason": "status_from_cache",
                    "cache_key": self._generate_cache_key("status", pattern),
                    "estimated_cost": 0.002,
                    "estimated_time_ms": 150
                }
        
        # Check message length and complexity
        if len(message) < 50 and channel == "direct":
            # Short direct messages are likely simple
            return {
                "level": "L1",
                "confidence": 0.7,
                "reason": "short_message", 
                "cache_key": None,
                "estimated_cost": 0.003,
                "estimated_time_ms": 300
            }
        
        # Default to full system (L2)
        return {
            "level": "L2",
            "confidence": 1.0,
            "reason": "complex_query",
            "cache_key": None,
            "estimated_cost": 0.015,  # Current average
            "estimated_time_ms": 1500
        }
    
    def _generate_cache_key(self, category: str, content: str) -> str:
        """Generate cache key for content"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        return f"{category}_{content_hash}"
    
    def handle_l0_request(self, message: str, cache_key: str) -> Optional[Dict[str, Any]]:
        """Handle L0 (instant) requests from cache"""
        
        # Check cache first
        cached_response = self._get_cached_response(cache_key, "status_queries")
        if cached_response:
            return {
                "success": True,
                "response": cached_response["response"],
                "source": "cache",
                "cache_age_seconds": (datetime.now() - datetime.fromisoformat(cached_response["timestamp"])).total_seconds()
            }
        
        # Generate fresh response for common status queries
        message_lower = message.lower().strip()
        
        if any(word in message_lower for word in ["סטטוס", "תקין", "בריא", "עובד"]):
            response = self._generate_status_response()
            self._cache_response(cache_key, response, "status_queries")
            return {
                "success": True,
                "response": response,
                "source": "generated"
            }
        
        return None
    
    def handle_l1_request(self, message: str, cache_key: str = None) -> Dict[str, Any]:
        """Handle L1 (fast) requests with minimal processing"""
        
        # Check cache if key provided
        if cache_key:
            cached_response = self._get_cached_response(cache_key, "simple_responses")
            if cached_response:
                return {
                    "success": True,
                    "response": cached_response["response"],
                    "source": "cache",
                    "processing_time_ms": 5
                }
        
        message_lower = message.lower().strip()
        
        # Time/date queries
        if any(word in message_lower for word in ["שעה", "תאריך", "יום", "זמן"]):
            response = self._handle_time_query(message_lower)
            if cache_key:
                self._cache_response(cache_key, response, "simple_responses")
            return {
                "success": True,
                "response": response,
                "source": "fast_path",
                "processing_time_ms": 15
            }
        
        # Greetings
        if any(word in message_lower for word in ["שלום", "היי", "hello", "בוקר טוב"]):
            response = "שלום! איך אני יכולה לעזור?"
            return {
                "success": True,
                "response": response,
                "source": "fast_path", 
                "processing_time_ms": 2
            }
        
        # Acknowledgments
        if any(word in message_lower for word in ["תודה", "thanks", "אוקי", "ok"]):
            response = "בשמחה! 😊"
            return {
                "success": True,
                "response": response,
                "source": "fast_path",
                "processing_time_ms": 2
            }
        
        # Status queries from cached data
        if any(word in message_lower for word in ["משימות", "פתוח", "מיילים"]):
            response = self._handle_status_query(message_lower)
            return {
                "success": True,
                "response": response,
                "source": "cached_data",
                "processing_time_ms": 50
            }
        
        # Fallback to minimal model call
        return {
            "success": False,
            "reason": "needs_model",
            "suggested_tier": "tier1"
        }
    
    def _generate_status_response(self) -> str:
        """Generate system status response from cached data"""
        
        try:
            # Quick health check without expensive operations
            current_time = datetime.now().strftime("%H:%M")
            
            # Check integration status from cache
            integrations_healthy = self._quick_integration_check()
            
            # Check queue lengths
            queue_status = self._quick_queue_check()
            
            status_emoji = "✅" if integrations_healthy and queue_status["healthy"] else "⚠️"
            
            response = f"{status_emoji} המערכת פעילה ({current_time})\n"
            
            if integrations_healthy:
                response += "🔗 חיבורים תקינים\n"
            else:
                response += "🟡 חלק מהחיבורים דורשים תשומת לב\n"
            
            if queue_status["pending"] > 0:
                response += f"📋 {queue_status['pending']} משימות בתור"
            else:
                response += "✨ אין משימות ממתינות"
            
            return response.strip()
            
        except Exception as e:
            return f"⚠️ בעיה בבדיקת סטטוס: {str(e)[:50]}"
    
    def _quick_integration_check(self) -> bool:
        """Quick integration health check from cache"""
        
        try:
            cache_file = self.cache_dir / "integration_status.json"
            
            if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 900:  # 15 minutes
                with open(cache_file, 'r') as f:
                    status = json.load(f)
                    return status.get("healthy_count", 0) >= status.get("total_count", 1) // 2
            
            # Fallback: assume healthy if no recent data
            return True
            
        except:
            return True
    
    def _quick_queue_check(self) -> Dict[str, Any]:
        """Quick queue status check"""
        
        try:
            # Check publishing queue
            publishing_queue = self.workspace / "state" / "publishing_queue.json"
            pending_count = 0
            
            if publishing_queue.exists():
                with open(publishing_queue, 'r') as f:
                    queue_data = json.load(f)
                    pending_count = len(queue_data.get("queue", []))
            
            # Check open tasks
            open_tasks = self.workspace / "state" / "OPEN_TASKS.md"
            urgent_tasks = 0
            
            if open_tasks.exists():
                content = open_tasks.read_text()
                urgent_tasks = content.count("🔴")
            
            total_pending = pending_count + urgent_tasks
            
            return {
                "pending": total_pending,
                "healthy": total_pending < 10,
                "publishing_queue": pending_count,
                "urgent_tasks": urgent_tasks
            }
            
        except:
            return {"pending": 0, "healthy": True, "publishing_queue": 0, "urgent_tasks": 0}
    
    def _handle_time_query(self, message: str) -> str:
        """Handle time/date queries"""
        
        now = datetime.now()
        
        if "שעה" in message or "זמן" in message:
            return f"🕐 השעה {now.strftime('%H:%M')}"
        
        elif "תאריך" in message:
            hebrew_date = now.strftime("%d.%m.%Y")
            return f"📅 התאריך היום {hebrew_date}"
        
        elif "יום" in message:
            days = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
            day_name = days[now.weekday()]
            return f"📆 היום יום {day_name}"
        
        else:
            return f"🕐 {now.strftime('%H:%M')} | 📅 {now.strftime('%d.%m.%Y')}"
    
    def _handle_status_query(self, message: str) -> str:
        """Handle status queries from cached data"""
        
        try:
            if "משימות" in message or "פתוח" in message:
                return self._get_tasks_summary()
            
            elif "מיילים" in message:
                return self._get_email_summary()
            
            elif "קבוצות" in message:
                return self._get_groups_summary()
            
            else:
                return "אני יכולה לבדוק משימות, מיילים או קבוצות. מה מעניין אותך?"
                
        except Exception as e:
            return f"⚠️ בעיה בשליפת נתונים: {str(e)[:50]}"
    
    def _get_tasks_summary(self) -> str:
        """Get quick tasks summary from file"""
        
        try:
            tasks_file = self.workspace / "state" / "OPEN_TASKS.md"
            
            if not tasks_file.exists():
                return "📋 אין קובץ משימות זמין"
            
            content = tasks_file.read_text()
            
            # Count by priority
            red_count = content.count("🔴")
            yellow_count = content.count("🟡")
            green_count = content.count("🟢")
            
            if red_count == 0 and yellow_count == 0 and green_count == 0:
                return "✨ אין משימות פתוחות"
            
            summary = "📋 משימות פתוחות:\n"
            if red_count > 0:
                summary += f"🔴 דחופות: {red_count}\n"
            if yellow_count > 0:
                summary += f"🟡 חשובות: {yellow_count}\n"
            if green_count > 0:
                summary += f"🟢 שוטפות: {green_count}"
            
            return summary.strip()
            
        except Exception as e:
            return f"⚠️ לא הצלחתי לקרוא משימות: {str(e)[:30]}"
    
    def _get_email_summary(self) -> str:
        """Get quick email summary (placeholder)"""
        
        # In real implementation, would check recent email activity
        return "📧 בדיקת מיילים דורשת חיבור מלא\nהאם לבדוק עכשיו?"
    
    def _get_groups_summary(self) -> str:
        """Get quick groups summary"""
        
        try:
            groups_dir = self.workspace / "state" / "groups"
            
            if not groups_dir.exists():
                return "📱 אין נתוני קבוצות זמינים"
            
            group_files = list(groups_dir.glob("*.json"))
            
            if not group_files:
                return "📱 אין קבוצות רשומות"
            
            active_today = 0
            total_groups = len(group_files)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            for group_file in group_files:
                try:
                    with open(group_file, 'r') as f:
                        data = json.load(f)
                        last_activity = data.get("last_activity", "")
                        if today in last_activity:
                            active_today += 1
                except:
                    continue
            
            return f"📱 {total_groups} קבוצות רשומות\n🔥 {active_today} פעילות היום"
            
        except Exception as e:
            return f"⚠️ לא הצלחתי לקרוא נתוני קבוצות: {str(e)[:30]}"
    
    def _get_cached_response(self, cache_key: str, category: str) -> Optional[Dict[str, Any]]:
        """Get response from cache if valid"""
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check TTL
            cached_time = datetime.fromisoformat(cached["timestamp"])
            ttl_seconds = self.cache_ttl.get(category, 1800)
            
            if (datetime.now() - cached_time).total_seconds() < ttl_seconds:
                return cached
            else:
                # Clean up expired cache
                cache_file.unlink()
                return None
                
        except (json.JSONDecodeError, KeyError, ValueError):
            # Clean up corrupted cache
            cache_file.unlink()
            return None
    
    def _cache_response(self, cache_key: str, response: str, category: str):
        """Cache response with timestamp"""
        
        cache_data = {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "category": category
        }
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except:
            pass  # Don't fail if caching doesn't work
    
    def get_fast_path_stats(self) -> Dict[str, Any]:
        """Get fast path usage statistics"""
        
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            
            stats = {
                "total_cached_responses": len(cache_files),
                "cache_categories": {},
                "cache_directory_size_kb": sum(f.stat().st_size for f in cache_files) / 1024
            }
            
            # Count by category
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        category = data.get("category", "unknown")
                        stats["cache_categories"][category] = stats["cache_categories"].get(category, 0) + 1
                except:
                    continue
            
            return stats
            
        except Exception as e:
            return {"error": str(e), "total_cached_responses": 0}
    
    def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old cache files"""
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    if datetime.fromtimestamp(cache_file.stat().st_mtime) < cutoff_time:
                        cache_file.unlink()
                        cleaned += 1
                except:
                    continue
            
            return {"cleaned_files": cleaned}
            
        except Exception as e:
            return {"error": str(e), "cleaned_files": 0}

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  fast_path.py classify '<message>' [channel]")
        print("  fast_path.py handle '<message>' [level]") 
        print("  fast_path.py stats")
        print("  fast_path.py cleanup [hours]")
        return
    
    fast_path = FastPathRouter()
    command = sys.argv[1]
    
    if command == "classify" and len(sys.argv) >= 3:
        message = sys.argv[2]
        channel = sys.argv[3] if len(sys.argv) > 3 else "direct"
        
        result = fast_path.classify_request(message, channel)
        print(f"🔍 Classification for: '{message}'")
        print(f"   Level: {result['level']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reason: {result['reason']}")
        print(f"   Estimated cost: ${result['estimated_cost']:.4f}")
        print(f"   Estimated time: {result['estimated_time_ms']}ms")
    
    elif command == "handle" and len(sys.argv) >= 3:
        message = sys.argv[2]
        level = sys.argv[3] if len(sys.argv) > 3 else None
        
        # Classify first if level not specified
        if not level:
            classification = fast_path.classify_request(message)
            level = classification["level"]
        
        start_time = time.time()
        
        if level == "L0":
            classification = fast_path.classify_request(message)
            result = fast_path.handle_l0_request(message, classification.get("cache_key"))
        elif level == "L1":
            classification = fast_path.classify_request(message)
            result = fast_path.handle_l1_request(message, classification.get("cache_key"))
        else:
            result = {"success": False, "reason": "L2 requires full system"}
        
        processing_time = (time.time() - start_time) * 1000
        
        print(f"⚡ Fast path handling ({level}):")
        print(f"   Processing time: {processing_time:.1f}ms")
        
        if result and result.get("success"):
            print(f"   Response: {result['response']}")
            print(f"   Source: {result.get('source', 'generated')}")
        else:
            print(f"   Failed: {result.get('reason', 'unknown') if result else 'no result'}")
    
    elif command == "stats":
        stats = fast_path.get_fast_path_stats()
        print("📊 Fast Path Statistics:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif command == "cleanup":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        result = fast_path.cleanup_cache(hours)
        print(f"🧹 Cache cleanup (older than {hours}h):")
        print(f"   Cleaned files: {result.get('cleaned_files', 0)}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()