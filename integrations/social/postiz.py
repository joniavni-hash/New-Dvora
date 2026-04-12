#!/usr/bin/env python3
"""
Postiz Integration - Simple social media publishing via Postiz API
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Postiz API configuration
POSTIZ_BASE_URL = os.getenv("POSTIZ_BASE_URL", "https://app.postiz.com")
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY", "")
POSTIZ_WORKSPACE_ID = os.getenv("POSTIZ_WORKSPACE_ID", "")

def check_connection() -> Dict[str, Any]:
    """Check Postiz API connection and workspace access"""
    
    if not POSTIZ_API_KEY:
        return {
            "connected": False,
            "status": "missing_api_key",
            "errors": ["POSTIZ_API_KEY not configured"],
            "fix_hints": [
                "Get API key from Postiz dashboard: Settings → API Keys",
                "Set POSTIZ_API_KEY environment variable",
                "Set POSTIZ_WORKSPACE_ID environment variable"
            ]
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {POSTIZ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test API connection by getting workspace info
        response = requests.get(
            f"{POSTIZ_BASE_URL}/api/workspaces",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            workspaces = response.json()
            
            # Find our workspace
            workspace = None
            if POSTIZ_WORKSPACE_ID:
                workspace = next((w for w in workspaces if w.get("id") == POSTIZ_WORKSPACE_ID), None)
            elif workspaces:
                workspace = workspaces[0]  # Use first workspace if ID not specified
            
            if workspace:
                # Get connected accounts for this workspace
                accounts_response = requests.get(
                    f"{POSTIZ_BASE_URL}/api/accounts",
                    headers=headers,
                    params={"workspace": workspace["id"]},
                    timeout=10
                )
                
                connected_accounts = []
                if accounts_response.status_code == 200:
                    accounts = accounts_response.json()
                    connected_accounts = [
                        {
                            "platform": acc.get("provider"),
                            "username": acc.get("username", acc.get("name", "Unknown")),
                            "status": "active" if acc.get("disabled", False) == False else "disabled"
                        }
                        for acc in accounts
                    ]
                
                return {
                    "connected": True,
                    "status": "connected",
                    "workspace": {
                        "id": workspace["id"],
                        "name": workspace.get("name", "Default"),
                        "connected_accounts": len(connected_accounts)
                    },
                    "accounts": connected_accounts,
                    "api_version": "v1"
                }
            else:
                return {
                    "connected": False,
                    "status": "workspace_not_found",
                    "errors": [f"Workspace {POSTIZ_WORKSPACE_ID} not found"],
                    "fix_hints": ["Check POSTIZ_WORKSPACE_ID", "Use first available workspace"]
                }
        else:
            return {
                "connected": False,
                "status": "api_error",
                "errors": [f"API returned {response.status_code}: {response.text}"],
                "fix_hints": ["Check API key validity", "Verify Postiz base URL"]
            }
            
    except requests.RequestException as e:
        return {
            "connected": False,
            "status": "connection_error",
            "errors": [f"Network error: {e}"],
            "fix_hints": ["Check internet connection", "Verify Postiz URL"]
        }

def validate_content(content: str, platforms: List[str], media_paths: List[str] = None) -> Dict[str, Any]:
    """Validate content for Postiz publishing"""
    
    validation = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Platform-specific validation
    for platform in platforms:
        if platform.lower() == "tiktok":
            if len(content) > 4000:
                validation["valid"] = False
                validation["errors"].append(f"TikTok caption too long: {len(content)} > 4000 characters")
            if not media_paths:
                validation["warnings"].append("TikTok posts typically require video content")
        
        elif platform.lower() == "instagram":
            if len(content) > 2200:
                validation["valid"] = False
                validation["errors"].append(f"Instagram caption too long: {len(content)} > 2200 characters")
            if not media_paths:
                validation["valid"] = False
                validation["errors"].append("Instagram posts require media")
        
        elif platform.lower() == "twitter":
            if len(content) > 280:
                validation["valid"] = False
                validation["errors"].append(f"Twitter text too long: {len(content)} > 280 characters")
    
    # Media validation
    if media_paths:
        for media_path in media_paths:
            file_path = Path(media_path)
            
            if not file_path.exists():
                validation["valid"] = False
                validation["errors"].append(f"Media file not found: {media_path}")
                continue
            
            file_size = file_path.stat().st_size
            file_extension = file_path.suffix.lower()
            
            # General size limits (Postiz handles platform-specific limits)
            if file_size > 100 * 1024 * 1024:  # 100MB
                validation["valid"] = False
                validation["errors"].append(f"Media file too large: {file_size} bytes")
            
            # Supported formats check
            if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi']:
                validation["warnings"].append(f"Potentially unsupported format: {file_extension}")
    
    return validation

def publish(content: str, platforms: List[str], media_paths: List[str] = None, 
           scheduled_time: str = None, draft_meta: Dict = None) -> Dict[str, Any]:
    """
    Publish content via Postiz to multiple platforms
    
    Args:
        content: Post content/caption
        platforms: List of platforms (tiktok, instagram, twitter, etc.)
        media_paths: List of media file paths
        scheduled_time: ISO timestamp for scheduled posting (optional)
        draft_meta: Additional metadata
    
    Returns:
        Dict with success status and platform results
    """
    
    # Check connection first
    connection_status = check_connection()
    if not connection_status["connected"]:
        return {
            "success": False,
            "error": "Not connected to Postiz",
            "details": connection_status
        }
    
    # Validate content
    validation = validate_content(content, platforms, media_paths)
    if not validation["valid"]:
        return {
            "success": False,
            "error": "Content validation failed",
            "validation_errors": validation["errors"]
        }
    
    try:
        # Prepare post data for Postiz API
        post_data = {
            "content": content,
            "platforms": platforms,
            "workspace": POSTIZ_WORKSPACE_ID or connection_status["workspace"]["id"]
        }
        
        # Add scheduling if specified
        if scheduled_time:
            post_data["scheduledAt"] = scheduled_time
        
        # Handle media upload if provided
        files = []
        if media_paths:
            for media_path in media_paths:
                if Path(media_path).exists():
                    files.append(('media', open(media_path, 'rb')))
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {POSTIZ_API_KEY}"
        }
        
        # Send to Postiz API
        if files:
            # Multipart request with files
            response = requests.post(
                f"{POSTIZ_BASE_URL}/api/posts",
                headers={"Authorization": f"Bearer {POSTIZ_API_KEY}"},
                data={k: v for k, v in post_data.items() if k != 'platforms'},
                files=[('platforms', p) for p in platforms] + files,
                timeout=60
            )
        else:
            # JSON request without files
            response = requests.post(
                f"{POSTIZ_BASE_URL}/api/posts",
                headers={**headers, "Content-Type": "application/json"},
                json=post_data,
                timeout=30
            )
        
        # Close file handles
        for _, file_handle in files:
            if hasattr(file_handle, 'close'):
                file_handle.close()
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            
            return {
                "success": True,
                "post_id": result_data.get("id"),
                "postiz_url": f"{POSTIZ_BASE_URL}/posts/{result_data.get('id')}",
                "platforms": platforms,
                "scheduled": scheduled_time is not None,
                "status": "scheduled" if scheduled_time else "published",
                "platform_results": result_data.get("results", {}),
                "postiz_response": result_data
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            return {
                "success": False,
                "error": f"Postiz API error: {response.status_code}",
                "details": error_data.get("message", response.text),
                "api_response": error_data
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Publishing failed: {e}"
        }

def get_post_status(post_id: str) -> Dict[str, Any]:
    """Get status of a published/scheduled post"""
    
    if not POSTIZ_API_KEY:
        return {"error": "API key not configured"}
    
    try:
        headers = {
            "Authorization": f"Bearer {POSTIZ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{POSTIZ_BASE_URL}/api/posts/{post_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            post_data = response.json()
            
            return {
                "success": True,
                "post_id": post_id,
                "status": post_data.get("status"),
                "platforms": post_data.get("platforms", []),
                "published_at": post_data.get("publishedAt"),
                "scheduled_at": post_data.get("scheduledAt"),
                "platform_results": post_data.get("results", {})
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get post status: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Status check failed: {e}"
        }

def get_connected_accounts() -> List[Dict[str, Any]]:
    """Get list of connected social media accounts"""
    
    connection_status = check_connection()
    if connection_status["connected"]:
        return connection_status.get("accounts", [])
    else:
        return []

def get_platform_info() -> Dict[str, Any]:
    """Get Postiz platform information and setup instructions"""
    
    return {
        "platform": "postiz",
        "display_name": "Postiz Social Media Manager",
        "supported_platforms": ["tiktok", "instagram", "twitter", "linkedin", "facebook", "youtube"],
        "features": [
            "Multi-platform publishing",
            "Content scheduling",
            "Media upload support", 
            "Analytics and insights",
            "Team collaboration",
            "Content calendar"
        ],
        "authentication": "api_key",
        "api_documentation": "https://docs.postiz.com/api",
        "setup_instructions": [
            "Sign up at https://app.postiz.com",
            "Connect your social media accounts",
            "Generate API key: Settings → API Keys → Create New Key",
            "Set environment variables: POSTIZ_API_KEY, POSTIZ_WORKSPACE_ID",
            "Optional: Set custom POSTIZ_BASE_URL for self-hosted instances"
        ],
        "pricing": {
            "free_tier": "1 workspace, 1 user, basic features",
            "pro_tier": "Multiple workspaces, team collaboration, advanced scheduling",
            "self_hosted": "Open source, unlimited usage"
        }
    }

def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  postiz.py check")
        print("  postiz.py info")
        print("  postiz.py accounts")
        print("  postiz.py publish '<content>' '<platforms_csv>' [media_path]")
        print("  postiz.py status <post_id>")
        print("  postiz.py validate '<content>' '<platforms_csv>' [media_path]")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        result = check_connection()
        print("🔍 Postiz Connection Status:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "info":
        info = get_platform_info()
        print("ℹ️ Postiz Platform Info:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif command == "accounts":
        accounts = get_connected_accounts()
        print("📱 Connected Accounts:")
        if accounts:
            for acc in accounts:
                print(f"  {acc['platform']}: @{acc['username']} ({acc['status']})")
        else:
            print("  No accounts connected or connection failed")
    
    elif command == "validate" and len(sys.argv) >= 4:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        media_path = sys.argv[4] if len(sys.argv) > 4 else None
        media_paths = [media_path] if media_path else []
        
        result = validate_content(content, platforms, media_paths)
        
        print("✅ Content Validation:")
        if result["valid"]:
            print("   Valid for publishing")
        else:
            print("   ❌ Validation failed:")
            for error in result["errors"]:
                print(f"     • {error}")
        
        if result["warnings"]:
            print("   ⚠️ Warnings:")
            for warning in result["warnings"]:
                print(f"     • {warning}")
    
    elif command == "publish" and len(sys.argv) >= 4:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',')
        media_path = sys.argv[4] if len(sys.argv) > 4 else None
        media_paths = [media_path] if media_path else []
        
        result = publish(content, platforms, media_paths)
        
        if result["success"]:
            print("✅ Published via Postiz:")
            print(f"   Post ID: {result.get('post_id')}")
            print(f"   Platforms: {', '.join(result.get('platforms', []))}")
            print(f"   Status: {result.get('status')}")
            print(f"   Postiz URL: {result.get('postiz_url')}")
        else:
            print("❌ Publishing failed:")
            print(f"   Error: {result['error']}")
            if result.get('details'):
                print(f"   Details: {result['details']}")
    
    elif command == "status" and len(sys.argv) >= 3:
        post_id = sys.argv[2]
        result = get_post_status(post_id)
        
        if result.get("success"):
            print(f"📊 Post Status ({post_id}):")
            print(f"   Status: {result['status']}")
            print(f"   Platforms: {', '.join(result['platforms'])}")
            print(f"   Published: {result.get('published_at', 'Not yet')}")
        else:
            print(f"❌ Failed to get status: {result.get('error')}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()