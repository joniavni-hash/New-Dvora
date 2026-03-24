#!/usr/bin/env python3
"""
Postiz Publishing Integration - Connects Publishing Gateway with Postiz
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add workspace to path
workspace = Path(__file__).parent.parent.parent
sys.path.append(str(workspace))

try:
    from integrations.social.postiz import check_connection, validate_content, publish, get_post_status
    from core.publishing_gateway import PublishingGateway
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class PostizPublishingIntegration:
    """
    Seamless integration between Publishing Gateway and Postiz
    Provides simplified multi-platform publishing with approval workflow
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or workspace)
        self.gateway = PublishingGateway(workspace_path)
    
    def create_villa_lithos_post(self, content: str, platforms: List[str], 
                               media_paths: List[str] = None) -> Dict[str, Any]:
        """
        Create Villa Lithos marketing post via Postiz
        Simplified workflow: Content → Validation → Postiz Publishing
        """
        
        # Add Villa Lithos branding
        branded_content = self._add_villa_branding(content)
        
        # Step 1: Check Postiz connection
        connection_status = check_connection()
        if not connection_status["connected"]:
            return {
                "success": False,
                "error": "Postiz not connected",
                "connection_status": connection_status,
                "fix_instructions": connection_status.get("fix_hints", [])
            }
        
        # Step 2: Validate content for target platforms
        validation = validate_content(branded_content, platforms, media_paths)
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Content validation failed",
                "validation_errors": validation["errors"],
                "warnings": validation.get("warnings", [])
            }
        
        # Step 3: Create draft in Publishing Gateway (for audit trail)
        draft = self.gateway.create_draft(
            content=branded_content,
            platforms=platforms,
            media_paths=media_paths or [],
            priority="high"
        )
        
        # Step 4: Auto-approve for Villa Lithos (trusted content)
        approval = self.gateway.approve_draft(
            draft["id"], 
            approved=True, 
            approver="system", 
            notes="Villa Lithos marketing content - auto-approved"
        )
        
        # Step 5: Publish via Postiz
        publish_result = publish(
            content=branded_content,
            platforms=platforms,
            media_paths=media_paths,
            draft_meta={"draft_id": draft["id"], "brand": "villa_lithos"}
        )
        
        # Step 6: Update gateway with results
        self.gateway._update_publish_results(draft["id"], {
            "postiz": publish_result
        })
        
        if publish_result["success"]:
            return {
                "success": True,
                "draft_id": draft["id"],
                "postiz_post_id": publish_result["post_id"],
                "postiz_url": publish_result["postiz_url"],
                "platforms": platforms,
                "status": publish_result["status"],
                "branded_content": branded_content,
                "message": f"Villa Lithos post published to {len(platforms)} platforms"
            }
        else:
            return {
                "success": False,
                "draft_id": draft["id"],
                "error": "Postiz publishing failed",
                "postiz_error": publish_result["error"],
                "details": publish_result.get("details")
            }
    
    def create_scheduled_post(self, content: str, platforms: List[str], 
                            scheduled_time: str, media_paths: List[str] = None) -> Dict[str, Any]:
        """
        Create scheduled post via Postiz with Publishing Gateway approval workflow
        """
        
        # Step 1: Create draft
        draft = self.gateway.create_draft(
            content=content,
            platforms=platforms,
            media_paths=media_paths or [],
            scheduled_time=scheduled_time
        )
        
        # Step 2: Validate
        validation = self.gateway.validate_draft(draft["id"])
        if validation["overall_status"] != "valid":
            return {
                "success": False,
                "error": "Validation failed",
                "validation": validation
            }
        
        # Step 3: Request approval (required for scheduled posts)
        approval_request = self.gateway.request_approval(draft["id"], approver="yoni")
        
        return {
            "success": True,
            "draft_id": draft["id"],
            "status": "pending_approval",
            "scheduled_for": scheduled_time,
            "platforms": platforms,
            "message": "Scheduled post created, pending approval",
            "approval_request": approval_request
        }
    
    def approve_and_schedule(self, draft_id: str, approved: bool, notes: str = None) -> Dict[str, Any]:
        """
        Approve draft and schedule via Postiz
        """
        
        # Approve in gateway
        approval = self.gateway.approve_draft(draft_id, approved, "yoni", notes)
        
        if not approved or approval.get("status") != "approved":
            return {
                "success": False,
                "status": "rejected",
                "message": f"Draft rejected: {notes or 'No reason provided'}"
            }
        
        # Get draft details
        draft = self.gateway.get_draft(draft_id)
        if not draft:
            return {
                "success": False,
                "error": "Draft not found"
            }
        
        # Schedule via Postiz
        publish_result = publish(
            content=draft["content"],
            platforms=draft["platforms"],
            media_paths=draft["media_paths"],
            scheduled_time=draft.get("scheduled_time"),
            draft_meta={"draft_id": draft_id}
        )
        
        # Update gateway results
        self.gateway._update_publish_results(draft_id, {
            "postiz": publish_result
        })
        
        if publish_result["success"]:
            return {
                "success": True,
                "draft_id": draft_id,
                "postiz_post_id": publish_result["post_id"],
                "status": "scheduled",
                "message": "Post approved and scheduled successfully"
            }
        else:
            return {
                "success": False,
                "error": "Scheduling failed",
                "postiz_error": publish_result["error"]
            }
    
    def get_publishing_status(self) -> Dict[str, Any]:
        """
        Get comprehensive publishing status (Gateway + Postiz)
        """
        
        # Get Gateway stats
        gateway_stats = self.gateway.get_stats()
        
        # Check Postiz connection
        postiz_status = check_connection()
        
        # Get connected accounts
        connected_accounts = []
        if postiz_status["connected"]:
            connected_accounts = postiz_status.get("accounts", [])
        
        return {
            "gateway": {
                "queue_length": gateway_stats["queue_length"],
                "pending_approval": gateway_stats["pending_approval"],
                "ready_to_publish": gateway_stats["ready_to_publish"]
            },
            "postiz": {
                "connected": postiz_status["connected"],
                "status": postiz_status["status"],
                "workspace": postiz_status.get("workspace", {}),
                "connected_platforms": len(connected_accounts),
                "accounts": connected_accounts
            },
            "overall_health": "healthy" if (
                gateway_stats["queue_length"] < 50 and 
                postiz_status["connected"]
            ) else "needs_attention"
        }
    
    def track_post_performance(self, postiz_post_id: str) -> Dict[str, Any]:
        """
        Track performance of published post
        """
        
        status = get_post_status(postiz_post_id)
        
        if status.get("success"):
            return {
                "success": True,
                "post_id": postiz_post_id,
                "status": status["status"],
                "platforms": status["platforms"],
                "published_at": status.get("published_at"),
                "platform_results": status.get("platform_results", {}),
                "performance_summary": self._analyze_performance(status.get("platform_results", {}))
            }
        else:
            return {
                "success": False,
                "error": status.get("error"),
                "post_id": postiz_post_id
            }
    
    def _add_villa_branding(self, content: str) -> str:
        """Add Villa Lithos branding to content"""
        
        # Add hashtags if not present
        villa_hashtags = ["#VillaLithos", "#PortoRafti", "#Greece", "#LuxuryVilla"]
        
        for hashtag in villa_hashtags:
            if hashtag not in content:
                content += f" {hashtag}"
        
        return content.strip()
    
    def _analyze_performance(self, platform_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across platforms"""
        
        summary = {
            "total_platforms": len(platform_results),
            "successful_publishes": 0,
            "failed_publishes": 0,
            "engagement_summary": {}
        }
        
        for platform, result in platform_results.items():
            if result.get("success", False):
                summary["successful_publishes"] += 1
                
                # Extract engagement data if available
                if "engagement" in result:
                    summary["engagement_summary"][platform] = result["engagement"]
            else:
                summary["failed_publishes"] += 1
        
        summary["success_rate"] = (
            summary["successful_publishes"] / summary["total_platforms"] * 100
            if summary["total_platforms"] > 0 else 0
        )
        
        return summary

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  postiz_integration.py villa-post '<content>' '<platforms_csv>' [media_path]")
        print("  postiz_integration.py schedule '<content>' '<platforms_csv>' '<scheduled_time>' [media_path]")  
        print("  postiz_integration.py approve <draft_id> <true/false> [notes]")
        print("  postiz_integration.py status")
        print("  postiz_integration.py track <postiz_post_id>")
        return
    
    integration = PostizPublishingIntegration()
    command = sys.argv[1]
    
    if command == "villa-post" and len(sys.argv) >= 4:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        media_path = sys.argv[4] if len(sys.argv) > 4 else None
        media_paths = [media_path] if media_path else []
        
        result = integration.create_villa_lithos_post(content, platforms, media_paths)
        
        if result["success"]:
            print("✅ Villa Lithos post published:")
            print(f"   Draft ID: {result['draft_id']}")
            print(f"   Postiz ID: {result['postiz_post_id']}")
            print(f"   Platforms: {', '.join(result['platforms'])}")
            print(f"   URL: {result['postiz_url']}")
        else:
            print("❌ Publishing failed:")
            print(f"   Error: {result['error']}")
            
            if "fix_instructions" in result:
                print("   Fix instructions:")
                for instruction in result["fix_instructions"]:
                    print(f"     • {instruction}")
    
    elif command == "schedule" and len(sys.argv) >= 5:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        scheduled_time = sys.argv[4]
        media_path = sys.argv[5] if len(sys.argv) > 5 else None
        media_paths = [media_path] if media_path else []
        
        result = integration.create_scheduled_post(content, platforms, scheduled_time, media_paths)
        
        if result["success"]:
            print("📅 Scheduled post created:")
            print(f"   Draft ID: {result['draft_id']}")
            print(f"   Scheduled for: {result['scheduled_for']}")
            print(f"   Status: {result['status']}")
        else:
            print("❌ Scheduling failed:")
            print(f"   Error: {result['error']}")
    
    elif command == "approve" and len(sys.argv) >= 4:
        draft_id = sys.argv[2]
        approved = sys.argv[3].lower() == "true"
        notes = sys.argv[4] if len(sys.argv) > 4 else None
        
        result = integration.approve_and_schedule(draft_id, approved, notes)
        
        if result["success"]:
            print(f"✅ Draft approved and scheduled: {draft_id}")
            print(f"   Postiz ID: {result.get('postiz_post_id')}")
        else:
            print(f"❌ Approval failed: {result['message']}")
    
    elif command == "status":
        status = integration.get_publishing_status()
        
        print("📊 Publishing Integration Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif command == "track" and len(sys.argv) >= 3:
        post_id = sys.argv[2]
        result = integration.track_post_performance(post_id)
        
        if result["success"]:
            print(f"📈 Post Performance ({post_id}):")
            print(f"   Status: {result['status']}")
            print(f"   Platforms: {', '.join(result['platforms'])}")
            print(f"   Success rate: {result['performance_summary']['success_rate']:.1f}%")
        else:
            print(f"❌ Tracking failed: {result['error']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()