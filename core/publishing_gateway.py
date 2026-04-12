#!/usr/bin/env python3
"""
Publishing Gateway - Unified social media publishing with validation and approval flow
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

class PublishStatus(Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"

class PublishingGateway:
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or os.environ.get("DVORAH_WORKSPACE", 
                                                             Path.home() / ".openclaw" / "workspace"))
        self.queue_file = self.workspace / "state" / "publishing_queue.json"
        self.policies_file = self.workspace / "policies" / "PUBLISHING_POLICY.md"
        
        # Ensure directories exist
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load supported platforms
        self.platforms = self._load_platform_integrations()
        
        # Ensure queue exists
        self._ensure_queue_file()
    
    def _ensure_queue_file(self):
        """Ensure publishing queue file exists with valid structure"""
        if not self.queue_file.exists():
            default_queue = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "queue": [],
                "completed": [],
                "stats": {
                    "total_published": 0,
                    "total_failed": 0,
                    "platforms": {}
                }
            }
            self._save_queue(default_queue)
        
        # Validate existing file
        try:
            self._load_queue()
        except (json.JSONDecodeError, KeyError):
            print("Warning: corrupted queue file, recreating")
            self._ensure_queue_file()
    
    def _load_queue(self) -> Dict[str, Any]:
        """Load publishing queue from file"""
        with open(self.queue_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_queue(self, queue_data: Dict[str, Any]):
        """Save publishing queue to file"""
        queue_data["updated"] = datetime.now().isoformat()
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)
    
    def _load_platform_integrations(self) -> Dict[str, Any]:
        """Load available platform integrations"""
        integrations_dir = self.workspace / "integrations" / "social"
        platforms = {}
        
        # Check for platform modules
        platform_files = {
            "tiktok": integrations_dir / "tiktok.py",
            "instagram": integrations_dir / "instagram.py", 
            "facebook": integrations_dir / "facebook.py",
            "twitter": integrations_dir / "twitter.py"
        }
        
        for platform, file_path in platform_files.items():
            platforms[platform] = {
                "available": file_path.exists(),
                "module_path": str(file_path),
                "connected": False,  # Will be checked during validation
                "last_check": None
            }
        
        return platforms
    
    def create_draft(self, content: str, platforms: List[str], media_paths: List[str] = None,
                    scheduled_time: str = None, priority: str = "medium") -> Dict[str, Any]:
        """
        Create a new publishing draft
        
        Args:
            content: Text content to publish
            platforms: List of platforms to publish to ['tiktok', 'instagram', etc.]
            media_paths: List of media file paths
            scheduled_time: ISO timestamp for scheduled publishing
            priority: 'low', 'medium', 'high'
        """
        
        # Generate unique draft ID
        draft_id = f"draft_{int(time.time())}_{hash(content) % 10000}"
        
        draft = {
            "id": draft_id,
            "content": content,
            "platforms": platforms,
            "media_paths": media_paths or [],
            "scheduled_time": scheduled_time,
            "priority": priority,
            "status": PublishStatus.DRAFT.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "validation_results": {},
            "approval_status": None,
            "publish_results": {},
            "errors": []
        }
        
        # Add to queue
        queue_data = self._load_queue()
        queue_data["queue"].append(draft)
        self._save_queue(queue_data)
        
        return draft
    
    def validate_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Validate draft for publishing readiness
        Checks OAuth, scopes, media validity, content guidelines
        """
        
        queue_data = self._load_queue()
        draft = self._find_draft_by_id(queue_data, draft_id)
        
        if not draft:
            return {"error": f"Draft {draft_id} not found"}
        
        validation_results = {
            "overall_status": "pending",
            "platforms": {},
            "media": {},
            "content": {},
            "errors": [],
            "warnings": []
        }
        
        # Validate each platform
        for platform in draft["platforms"]:
            platform_result = self._validate_platform(platform, draft)
            validation_results["platforms"][platform] = platform_result
            
            if not platform_result["valid"]:
                validation_results["errors"].extend(platform_result.get("errors", []))
        
        # Validate media files
        if draft["media_paths"]:
            media_result = self._validate_media(draft["media_paths"])
            validation_results["media"] = media_result
            
            if not media_result["valid"]:
                validation_results["errors"].extend(media_result.get("errors", []))
        
        # Validate content
        content_result = self._validate_content(draft["content"], draft["platforms"])
        validation_results["content"] = content_result
        
        if not content_result["valid"]:
            validation_results["errors"].extend(content_result.get("errors", []))
        
        # Overall validation status
        validation_results["overall_status"] = "valid" if not validation_results["errors"] else "invalid"
        
        # Update draft
        draft["validation_results"] = validation_results
        draft["status"] = PublishStatus.VALIDATED.value if validation_results["overall_status"] == "valid" else PublishStatus.DRAFT.value
        draft["updated_at"] = datetime.now().isoformat()
        
        self._save_queue(queue_data)
        
        return validation_results
    
    def _validate_platform(self, platform: str, draft: Dict) -> Dict[str, Any]:
        """Validate specific platform requirements"""
        
        if platform not in self.platforms:
            return {
                "valid": False,
                "errors": [f"Platform {platform} not supported"],
                "connection_status": "unsupported"
            }
        
        platform_info = self.platforms[platform]
        
        if not platform_info["available"]:
            return {
                "valid": False,
                "errors": [f"Platform {platform} integration not installed"],
                "connection_status": "not_installed",
                "fix_hint": f"Install integration at {platform_info['module_path']}"
            }
        
        # Try to load and check platform module
        try:
            # Import the platform module dynamically
            import sys
            sys.path.append(str(self.workspace / "integrations" / "social"))
            
            platform_module = __import__(platform)
            
            # Check if platform has required methods
            required_methods = ["check_connection", "validate_content", "publish"]
            missing_methods = [method for method in required_methods 
                             if not hasattr(platform_module, method)]
            
            if missing_methods:
                return {
                    "valid": False,
                    "errors": [f"Platform {platform} missing methods: {missing_methods}"],
                    "connection_status": "incomplete"
                }
            
            # Check actual connection
            connection_result = platform_module.check_connection()
            
            return {
                "valid": connection_result.get("connected", False),
                "connection_status": connection_result.get("status", "unknown"),
                "account_info": connection_result.get("account_info", {}),
                "scopes": connection_result.get("scopes", []),
                "errors": connection_result.get("errors", []),
                "fix_hints": connection_result.get("fix_hints", [])
            }
            
        except ImportError as e:
            return {
                "valid": False,
                "errors": [f"Cannot load {platform} module: {e}"],
                "connection_status": "import_error",
                "fix_hint": f"Check {platform}.py implementation"
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Platform {platform} validation error: {e}"],
                "connection_status": "error"
            }
    
    def _validate_media(self, media_paths: List[str]) -> Dict[str, Any]:
        """Validate media files"""
        
        results = {
            "valid": True,
            "files": {},
            "errors": [],
            "total_size": 0
        }
        
        for media_path in media_paths:
            file_path = Path(media_path)
            
            file_result = {
                "exists": file_path.exists(),
                "size": 0,
                "type": None,
                "valid": False
            }
            
            if file_path.exists():
                file_result["size"] = file_path.stat().st_size
                file_result["type"] = file_path.suffix.lower()
                
                # Check file type
                supported_types = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webp']
                if file_result["type"] in supported_types:
                    file_result["valid"] = True
                else:
                    file_result["valid"] = False
                    results["errors"].append(f"Unsupported file type: {file_result['type']}")
                
                # Check file size (100MB limit)
                if file_result["size"] > 100 * 1024 * 1024:
                    file_result["valid"] = False
                    results["errors"].append(f"File too large: {file_result['size']} bytes")
                
                results["total_size"] += file_result["size"]
            else:
                file_result["valid"] = False
                results["errors"].append(f"File not found: {media_path}")
            
            results["files"][media_path] = file_result
            
            if not file_result["valid"]:
                results["valid"] = False
        
        return results
    
    def _validate_content(self, content: str, platforms: List[str]) -> Dict[str, Any]:
        """Validate content against platform guidelines"""
        
        results = {
            "valid": True,
            "length": len(content),
            "platforms": {},
            "errors": [],
            "warnings": []
        }
        
        # Platform-specific content limits
        platform_limits = {
            "twitter": 280,
            "instagram": 2200,
            "facebook": 63206,
            "tiktok": 4000
        }
        
        for platform in platforms:
            platform_result = {"valid": True, "issues": []}
            
            # Check length limits
            if platform in platform_limits:
                limit = platform_limits[platform]
                if len(content) > limit:
                    platform_result["valid"] = False
                    platform_result["issues"].append(f"Content too long: {len(content)} > {limit}")
                    results["errors"].append(f"{platform}: Content exceeds {limit} character limit")
            
            # Check for prohibited content (basic)
            prohibited_words = ["spam", "fake", "scam"]  # Extend as needed
            for word in prohibited_words:
                if word.lower() in content.lower():
                    platform_result["issues"].append(f"Contains prohibited word: {word}")
                    results["warnings"].append(f"{platform}: Content contains '{word}'")
            
            results["platforms"][platform] = platform_result
            
            if not platform_result["valid"]:
                results["valid"] = False
        
        return results
    
    def request_approval(self, draft_id: str, approver: str = "yoni") -> Dict[str, Any]:
        """Request approval for validated draft"""
        
        queue_data = self._load_queue()
        draft = self._find_draft_by_id(queue_data, draft_id)
        
        if not draft:
            return {"error": f"Draft {draft_id} not found"}
        
        if draft["status"] != PublishStatus.VALIDATED.value:
            return {"error": f"Draft must be validated before approval request"}
        
        # Update draft status
        draft["status"] = PublishStatus.PENDING_APPROVAL.value
        draft["approval_status"] = {
            "requested_at": datetime.now().isoformat(),
            "approver": approver,
            "status": "pending"
        }
        draft["updated_at"] = datetime.now().isoformat()
        
        self._save_queue(queue_data)
        
        # In real system, would send notification to approver
        return {
            "status": "approval_requested",
            "draft_id": draft_id,
            "approver": approver,
            "message": f"Approval requested from {approver} for draft {draft_id}"
        }
    
    def approve_draft(self, draft_id: str, approved: bool, approver: str, notes: str = None) -> Dict[str, Any]:
        """Approve or reject a draft"""
        
        queue_data = self._load_queue()
        draft = self._find_draft_by_id(queue_data, draft_id)
        
        if not draft:
            return {"error": f"Draft {draft_id} not found"}
        
        if draft["status"] != PublishStatus.PENDING_APPROVAL.value:
            return {"error": f"Draft not pending approval"}
        
        # Update approval status
        draft["approval_status"]["status"] = "approved" if approved else "rejected"
        draft["approval_status"]["approved_by"] = approver
        draft["approval_status"]["approved_at"] = datetime.now().isoformat()
        draft["approval_status"]["notes"] = notes
        
        draft["status"] = PublishStatus.APPROVED.value if approved else PublishStatus.REJECTED.value
        draft["updated_at"] = datetime.now().isoformat()
        
        self._save_queue(queue_data)
        
        return {
            "status": "approved" if approved else "rejected",
            "draft_id": draft_id,
            "approver": approver,
            "notes": notes
        }
    
    def publish_draft(self, draft_id: str) -> Dict[str, Any]:
        """Publish approved draft to all specified platforms"""
        
        queue_data = self._load_queue()
        draft = self._find_draft_by_id(queue_data, draft_id)
        
        if not draft:
            return {"error": f"Draft {draft_id} not found"}
        
        if draft["status"] != PublishStatus.APPROVED.value:
            return {"error": f"Draft must be approved before publishing"}
        
        # Publish to each platform
        publish_results = {}
        overall_success = True
        
        for platform in draft["platforms"]:
            try:
                platform_result = self._publish_to_platform(platform, draft)
                publish_results[platform] = platform_result
                
                if not platform_result.get("success", False):
                    overall_success = False
                    
            except Exception as e:
                publish_results[platform] = {
                    "success": False,
                    "error": str(e),
                    "published_at": datetime.now().isoformat()
                }
                overall_success = False
        
        # Update draft status
        draft["publish_results"] = publish_results
        draft["status"] = PublishStatus.PUBLISHED.value if overall_success else PublishStatus.FAILED.value
        draft["updated_at"] = datetime.now().isoformat()
        
        # Move to completed
        queue_data["queue"] = [d for d in queue_data["queue"] if d["id"] != draft_id]
        queue_data["completed"].append(draft)
        
        # Update stats
        if overall_success:
            queue_data["stats"]["total_published"] += 1
        else:
            queue_data["stats"]["total_failed"] += 1
        
        for platform in draft["platforms"]:
            if platform not in queue_data["stats"]["platforms"]:
                queue_data["stats"]["platforms"][platform] = {"published": 0, "failed": 0}
            
            if publish_results.get(platform, {}).get("success", False):
                queue_data["stats"]["platforms"][platform]["published"] += 1
            else:
                queue_data["stats"]["platforms"][platform]["failed"] += 1
        
        self._save_queue(queue_data)
        
        return {
            "status": "published" if overall_success else "failed",
            "draft_id": draft_id,
            "results": publish_results,
            "overall_success": overall_success
        }
    
    def _publish_to_platform(self, platform: str, draft: Dict) -> Dict[str, Any]:
        """Publish to specific platform"""
        
        try:
            import sys
            sys.path.append(str(self.workspace / "integrations" / "social"))
            
            platform_module = __import__(platform)
            
            # Call platform publish method
            result = platform_module.publish(
                content=draft["content"],
                media_paths=draft["media_paths"],
                draft_meta=draft
            )
            
            return {
                "success": result.get("success", False),
                "post_id": result.get("post_id"),
                "post_url": result.get("post_url"),
                "published_at": datetime.now().isoformat(),
                "platform_response": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "published_at": datetime.now().isoformat()
            }
    
    def _find_draft_by_id(self, queue_data: Dict, draft_id: str) -> Optional[Dict]:
        """Find draft by ID in queue"""
        for draft in queue_data["queue"]:
            if draft["id"] == draft_id:
                return draft
        return None
    
    def list_drafts(self, status: str = None) -> List[Dict[str, Any]]:
        """List drafts, optionally filtered by status"""
        queue_data = self._load_queue()
        drafts = queue_data["queue"]
        
        if status:
            drafts = [d for d in drafts if d["status"] == status]
        
        return drafts
    
    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get specific draft by ID"""
        queue_data = self._load_queue()
        return self._find_draft_by_id(queue_data, draft_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get publishing statistics"""
        queue_data = self._load_queue()
        
        # Add current queue stats
        current_stats = {
            "queue_length": len(queue_data["queue"]),
            "pending_approval": len([d for d in queue_data["queue"] 
                                   if d["status"] == PublishStatus.PENDING_APPROVAL.value]),
            "ready_to_publish": len([d for d in queue_data["queue"] 
                                   if d["status"] == PublishStatus.APPROVED.value])
        }
        
        return {
            **queue_data["stats"],
            **current_stats
        }

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  publishing_gateway.py create '<content>' <platforms> [media_path]")
        print("  publishing_gateway.py validate <draft_id>")
        print("  publishing_gateway.py approve <draft_id> <true/false> [notes]")
        print("  publishing_gateway.py publish <draft_id>")
        print("  publishing_gateway.py list [status]")
        print("  publishing_gateway.py stats")
        return
    
    gateway = PublishingGateway()
    command = sys.argv[1]
    
    if command == "create" and len(sys.argv) >= 4:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        media_path = sys.argv[4] if len(sys.argv) > 4 else None
        media_paths = [media_path] if media_path else []
        
        draft = gateway.create_draft(content, platforms, media_paths)
        print(f"📝 Draft created: {draft['id']}")
        print(f"   Content: {content[:50]}...")
        print(f"   Platforms: {', '.join(platforms)}")
    
    elif command == "validate" and len(sys.argv) > 2:
        draft_id = sys.argv[2]
        result = gateway.validate_draft(draft_id)
        
        print(f"🔍 Validation for {draft_id}:")
        print(f"   Status: {result['overall_status']}")
        
        if result["errors"]:
            print("   ❌ Errors:")
            for error in result["errors"]:
                print(f"     • {error}")
        
        for platform, platform_result in result.get("platforms", {}).items():
            status = "✅" if platform_result["valid"] else "❌"
            print(f"   {status} {platform}: {platform_result.get('connection_status', 'unknown')}")
    
    elif command == "approve" and len(sys.argv) >= 4:
        draft_id = sys.argv[2]
        approved = sys.argv[3].lower() == "true"
        notes = sys.argv[4] if len(sys.argv) > 4 else None
        
        result = gateway.approve_draft(draft_id, approved, "cli_user", notes)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            status = "✅ Approved" if approved else "❌ Rejected"
            print(f"{status}: {draft_id}")
    
    elif command == "publish" and len(sys.argv) > 2:
        draft_id = sys.argv[2]
        result = gateway.publish_draft(draft_id)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            status = "✅ Published" if result["overall_success"] else "❌ Failed"
            print(f"{status}: {draft_id}")
            
            for platform, platform_result in result["results"].items():
                platform_status = "✅" if platform_result["success"] else "❌"
                print(f"   {platform_status} {platform}")
    
    elif command == "list":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        drafts = gateway.list_drafts(status_filter)
        
        print(f"📋 {len(drafts)} drafts:")
        for draft in drafts:
            platforms = ', '.join(draft['platforms'])
            print(f"   {draft['id']}: {draft['status']} [{platforms}]")
            print(f"      {draft['content'][:60]}...")
    
    elif command == "stats":
        stats = gateway.get_stats()
        print("📊 Publishing Statistics:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        print(f"❌ Unknown command or missing arguments")

if __name__ == "__main__":
    main()