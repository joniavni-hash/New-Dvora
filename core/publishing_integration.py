#!/usr/bin/env python3
"""
Publishing Integration - Connects publishing gateway with main system
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add workspace to path
workspace = Path(__file__).parent.parent
sys.path.append(str(workspace))

from core.publishing_gateway import PublishingGateway

class PublishingIntegration:
    def __init__(self, workspace_path: str = None):
        self.gateway = PublishingGateway(workspace_path)
    
    def handle_publishing_request(self, content: str, platforms: List[str], 
                                media_paths: List[str] = None, priority: str = "medium") -> Dict[str, Any]:
        """
        Handle publishing request from router/agent
        Called when marketing domain needs to publish content
        """
        
        # Create draft
        draft = self.gateway.create_draft(
            content=content,
            platforms=platforms,
            media_paths=media_paths or [],
            priority=priority
        )
        
        # Immediately validate
        validation = self.gateway.validate_draft(draft["id"])
        
        # Determine next steps based on validation
        if validation["overall_status"] == "valid":
            # Request approval
            approval_request = self.gateway.request_approval(draft["id"], approver="yoni")
            
            return {
                "status": "pending_approval",
                "draft_id": draft["id"],
                "validation": validation,
                "approval_request": approval_request,
                "message": f"Draft created and validated. Pending approval from yoni.",
                "next_steps": [
                    f"Review draft content: {content[:50]}...",
                    f"Platforms: {', '.join(platforms)}",
                    f"Use approve_publishing('{draft['id']}', True) to approve"
                ]
            }
        else:
            return {
                "status": "validation_failed",
                "draft_id": draft["id"],
                "validation": validation,
                "errors": validation["errors"],
                "message": "Publishing request failed validation",
                "fix_hints": self._generate_fix_hints(validation)
            }
    
    def approve_publishing(self, draft_id: str, approved: bool, notes: str = None) -> Dict[str, Any]:
        """Approve or reject a publishing draft"""
        
        result = self.gateway.approve_draft(draft_id, approved, "yoni", notes)
        
        if result.get("status") == "approved":
            # Auto-publish if approved
            publish_result = self.gateway.publish_draft(draft_id)
            
            return {
                "status": "published" if publish_result.get("overall_success") else "publish_failed",
                "draft_id": draft_id,
                "approval": result,
                "publish_result": publish_result,
                "message": "Content approved and published" if publish_result.get("overall_success") else "Content approved but publishing failed"
            }
        else:
            return {
                "status": "rejected",
                "draft_id": draft_id,
                "approval": result,
                "message": f"Publishing request rejected: {notes or 'No reason provided'}"
            }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all drafts pending approval"""
        
        drafts = self.gateway.list_drafts("pending_approval")
        
        formatted_drafts = []
        for draft in drafts:
            formatted_drafts.append({
                "draft_id": draft["id"],
                "content": draft["content"][:100] + "..." if len(draft["content"]) > 100 else draft["content"],
                "platforms": draft["platforms"],
                "created_at": draft["created_at"],
                "priority": draft["priority"],
                "has_media": len(draft["media_paths"]) > 0,
                "approval_requested_at": draft.get("approval_status", {}).get("requested_at")
            })
        
        return formatted_drafts
    
    def get_publishing_status(self) -> Dict[str, Any]:
        """Get current publishing system status"""
        
        stats = self.gateway.get_stats()
        pending = self.get_pending_approvals()
        
        # Check platform connections
        platform_status = {}
        for platform in ["instagram", "tiktok"]:
            try:
                sys.path.append(str(workspace / "integrations" / "social"))
                platform_module = __import__(platform)
                connection = platform_module.check_connection()
                platform_status[platform] = {
                    "connected": connection.get("connected", False),
                    "status": connection.get("status", "unknown"),
                    "account": connection.get("account_info", {}).get("username", "N/A")
                }
            except:
                platform_status[platform] = {
                    "connected": False,
                    "status": "module_error",
                    "account": "N/A"
                }
        
        return {
            "stats": stats,
            "pending_approvals": len(pending),
            "platform_connections": platform_status,
            "system_health": "healthy" if stats["queue_length"] < 50 else "overloaded"
        }
    
    def _generate_fix_hints(self, validation: Dict[str, Any]) -> List[str]:
        """Generate actionable fix hints from validation errors"""
        
        hints = []
        
        for error in validation.get("errors", []):
            if "not configured" in error:
                if "INSTAGRAM" in error:
                    hints.append("Configure Instagram: Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables")
                elif "TIKTOK" in error:
                    hints.append("Configure TikTok: Set TIKTOK_ACCESS_TOKEN environment variable")
            
            elif "too long" in error:
                hints.append("Shorten content to meet platform limits")
            
            elif "not found" in error:
                hints.append("Ensure all media files exist and are accessible")
            
            elif "format" in error:
                hints.append("Convert media to supported formats (JPG/PNG for images, MP4/MOV for videos)")
        
        # Platform-specific hints
        for platform, platform_result in validation.get("platforms", {}).items():
            if not platform_result.get("valid", True):
                for hint in platform_result.get("fix_hints", []):
                    hints.append(f"{platform}: {hint}")
        
        return hints
    
    def process_scheduled_publishing(self) -> Dict[str, Any]:
        """
        Process scheduled publishing (called by heartbeat or cron)
        Finds approved drafts and publishes them
        """
        
        # Get approved drafts
        approved_drafts = self.gateway.list_drafts("approved")
        
        if not approved_drafts:
            return {
                "status": "no_approved_drafts",
                "processed": 0
            }
        
        results = []
        published_count = 0
        failed_count = 0
        
        for draft in approved_drafts[:5]:  # Process up to 5 at a time
            try:
                publish_result = self.gateway.publish_draft(draft["id"])
                
                if publish_result.get("overall_success"):
                    published_count += 1
                else:
                    failed_count += 1
                
                results.append({
                    "draft_id": draft["id"],
                    "success": publish_result.get("overall_success"),
                    "platforms": draft["platforms"],
                    "results": publish_result.get("results", {})
                })
                
            except Exception as e:
                failed_count += 1
                results.append({
                    "draft_id": draft["id"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "status": "processed",
            "total_processed": len(results),
            "published": published_count,
            "failed": failed_count,
            "results": results
        }
    
    def create_villa_lithos_post(self, slide_content: str, image_path: str = None) -> Dict[str, Any]:
        """
        Create Villa Lithos marketing post (specialized function)
        Called by Tali agent for Villa marketing
        """
        
        platforms = ["instagram"]  # Start with Instagram
        media_paths = [image_path] if image_path else []
        
        # Add Villa Lithos branding
        branded_content = f"{slide_content}\n\n#VillaLithos #Greece #LuxuryVilla #PortoRafti"
        
        return self.handle_publishing_request(
            content=branded_content,
            platforms=platforms,
            media_paths=media_paths,
            priority="high"  # Villa content is high priority
        )

# Global instance
publishing_integration = PublishingIntegration()

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  publishing_integration.py status")
        print("  publishing_integration.py pending")
        print("  publishing_integration.py approve <draft_id> <true/false> [notes]")
        print("  publishing_integration.py create '<content>' <platforms> [media_path]")
        print("  publishing_integration.py process-scheduled")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        status = publishing_integration.get_publishing_status()
        print("📊 Publishing System Status:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif command == "pending":
        pending = publishing_integration.get_pending_approvals()
        print(f"📋 {len(pending)} pending approvals:")
        for draft in pending:
            print(f"  📝 {draft['draft_id']}: {draft['platforms']}")
            print(f"      {draft['content']}")
            print(f"      Priority: {draft['priority']}, Created: {draft['created_at'][:10]}")
            print()
    
    elif command == "approve" and len(sys.argv) >= 4:
        draft_id = sys.argv[2]
        approved = sys.argv[3].lower() == "true"
        notes = sys.argv[4] if len(sys.argv) > 4 else None
        
        result = publishing_integration.approve_publishing(draft_id, approved, notes)
        
        if result["status"] == "published":
            print(f"✅ Approved and published: {draft_id}")
        elif result["status"] == "publish_failed":
            print(f"✅ Approved but failed to publish: {draft_id}")
            print(f"   Error: {result.get('publish_result', {}).get('error', 'Unknown error')}")
        else:
            print(f"❌ Rejected: {draft_id}")
            print(f"   Reason: {notes or 'No reason provided'}")
    
    elif command == "create" and len(sys.argv) >= 4:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        media_path = sys.argv[4] if len(sys.argv) > 4 else None
        media_paths = [media_path] if media_path else []
        
        result = publishing_integration.handle_publishing_request(content, platforms, media_paths)
        
        print(f"📝 Publishing Request: {result['status']}")
        print(f"   Draft ID: {result['draft_id']}")
        
        if result["status"] == "pending_approval":
            print("   ✅ Validated successfully, pending approval")
        else:
            print("   ❌ Validation failed:")
            for error in result.get("errors", []):
                print(f"     • {error}")
    
    elif command == "process-scheduled":
        result = publishing_integration.process_scheduled_publishing()
        
        if result["status"] == "no_approved_drafts":
            print("📭 No approved drafts to process")
        else:
            print(f"🚀 Processed {result['total_processed']} drafts:")
            print(f"   ✅ Published: {result['published']}")
            print(f"   ❌ Failed: {result['failed']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()