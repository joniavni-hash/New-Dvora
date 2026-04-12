#!/usr/bin/env python3
"""
TikTok Publishing Integration
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# TikTok API configuration (placeholder - real values needed)
TIKTOK_API_BASE = "https://open-api.tiktok.com"
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

def check_connection() -> Dict[str, Any]:
    """Check TikTok API connection and permissions"""
    
    if not TIKTOK_ACCESS_TOKEN:
        return {
            "connected": False,
            "status": "missing_credentials",
            "errors": ["TIKTOK_ACCESS_TOKEN not configured"],
            "fix_hints": [
                "Set TIKTOK_ACCESS_TOKEN environment variable",
                "Complete TikTok for Developers app setup", 
                "Obtain access token via OAuth2 flow"
            ]
        }
    
    try:
        # Test API connection
        headers = {
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get user info to test connection
        response = requests.get(
            f"{TIKTOK_API_BASE}/v2/user/info/",
            headers=headers,
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "connected": True,
                "status": "connected",
                "account_info": {
                    "display_name": user_data.get("data", {}).get("user", {}).get("display_name", "Unknown"),
                    "open_id": user_data.get("data", {}).get("user", {}).get("open_id"),
                    "avatar_url": user_data.get("data", {}).get("user", {}).get("avatar_url")
                },
                "scopes": ["user.info.basic", "video.publish"],  # Required scopes
                "api_version": "v2"
            }
        else:
            return {
                "connected": False,
                "status": "api_error",
                "errors": [f"API returned {response.status_code}: {response.text}"],
                "fix_hints": ["Check access token validity", "Verify app permissions"]
            }
            
    except requests.RequestException as e:
        return {
            "connected": False,
            "status": "connection_error", 
            "errors": [f"Network error: {e}"],
            "fix_hints": ["Check internet connection", "Verify TikTok API endpoint"]
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "errors": [f"Unexpected error: {e}"]
        }

def validate_content(content: str, media_paths: List[str] = None) -> Dict[str, Any]:
    """Validate content for TikTok publishing"""
    
    validation = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Content length validation
    if len(content) > 4000:
        validation["valid"] = False
        validation["errors"].append(f"Caption too long: {len(content)} > 4000 characters")
    
    # Media validation
    if media_paths:
        for media_path in media_paths:
            file_path = Path(media_path)
            
            if not file_path.exists():
                validation["valid"] = False
                validation["errors"].append(f"Media file not found: {media_path}")
                continue
            
            # Check file size (2GB limit for TikTok)
            file_size = file_path.stat().st_size
            if file_size > 2 * 1024 * 1024 * 1024:
                validation["valid"] = False
                validation["errors"].append(f"Video file too large: {file_size} bytes")
            
            # Check file format
            supported_formats = ['.mp4', '.mov', '.avi', '.webm']
            if file_path.suffix.lower() not in supported_formats:
                validation["valid"] = False
                validation["errors"].append(f"Unsupported video format: {file_path.suffix}")
    else:
        validation["warnings"].append("No media provided - TikTok posts typically require video content")
    
    # Content guidelines check (basic)
    prohibited_keywords = ["spam", "fake", "scam", "bot"]
    for keyword in prohibited_keywords:
        if keyword.lower() in content.lower():
            validation["warnings"].append(f"Content contains potentially problematic word: '{keyword}'")
    
    return validation

def publish(content: str, media_paths: List[str] = None, draft_meta: Dict = None) -> Dict[str, Any]:
    """
    Publish content to TikTok
    
    Note: This is a simplified implementation. Real TikTok publishing requires:
    1. Video upload to TikTok's media servers
    2. Creating a post with the uploaded media
    3. Handling TikTok's specific video processing pipeline
    """
    
    # Check connection first
    connection_status = check_connection()
    if not connection_status["connected"]:
        return {
            "success": False,
            "error": "Not connected to TikTok",
            "details": connection_status
        }
    
    # Validate content
    validation = validate_content(content, media_paths)
    if not validation["valid"]:
        return {
            "success": False,
            "error": "Content validation failed",
            "validation_errors": validation["errors"]
        }
    
    try:
        # Step 1: Upload media (if provided)
        media_id = None
        if media_paths:
            media_result = _upload_media(media_paths[0])  # TikTok typically takes one video
            if not media_result["success"]:
                return media_result
            media_id = media_result["media_id"]
        
        # Step 2: Create post
        post_data = {
            "post_info": {
                "title": content,
                "privacy_level": "SELF_ONLY",  # Start with private for safety
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            }
        }
        
        if media_id:
            post_data["source_info"] = {
                "source": "PULL_FROM_URL",  # or FILE_UPLOAD
                "video_url": media_id  # This would be the uploaded video URL/ID
            }
        
        headers = {
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Create post via TikTok API
        response = requests.post(
            f"{TIKTOK_API_BASE}/v2/post/publish/",
            headers=headers,
            json=post_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            
            return {
                "success": True,
                "post_id": result_data.get("data", {}).get("publish_id"),
                "post_url": f"https://www.tiktok.com/@{connection_status['account_info']['display_name']}/video/{result_data.get('data', {}).get('publish_id')}",
                "status": "published",
                "platform_response": result_data
            }
        else:
            return {
                "success": False,
                "error": f"TikTok API error: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Publishing failed: {e}"
        }

def _upload_media(media_path: str) -> Dict[str, Any]:
    """
    Upload media to TikTok (placeholder implementation)
    
    Real implementation would:
    1. Get upload URL from TikTok
    2. Upload video file in chunks
    3. Return media ID for posting
    """
    
    try:
        # This is a placeholder - real implementation needed
        # TikTok requires a complex multi-step upload process
        
        file_path = Path(media_path)
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Media file not found: {media_path}"
            }
        
        # In real implementation, this would:
        # 1. Call /v2/post/publish/video/init/ to get upload URL
        # 2. Upload video in chunks
        # 3. Call /v2/post/publish/video/upload/ to complete upload
        # 4. Return media_id for use in post creation
        
        # For now, return placeholder success
        return {
            "success": True,
            "media_id": f"placeholder_media_{int(os.path.getmtime(media_path))}",
            "upload_status": "completed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Media upload failed: {e}"
        }

def get_platform_info() -> Dict[str, Any]:
    """Get TikTok platform information and requirements"""
    return {
        "platform": "tiktok",
        "display_name": "TikTok",
        "content_types": ["video"],
        "max_video_size": 2 * 1024 * 1024 * 1024,  # 2GB
        "max_caption_length": 4000,
        "supported_formats": [".mp4", ".mov", ".avi", ".webm"],
        "video_requirements": {
            "min_duration": 1,  # seconds
            "max_duration": 180,  # 3 minutes
            "aspect_ratios": ["9:16", "1:1", "16:9"],
            "recommended_resolution": "1080x1920"
        },
        "authentication": "oauth2",
        "scopes_required": ["user.info.basic", "video.publish"],
        "api_documentation": "https://developers.tiktok.com/doc/",
        "setup_instructions": [
            "Create TikTok for Developers account",
            "Create app and get client_key/client_secret", 
            "Complete OAuth2 flow to get access_token",
            "Set environment variables: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_ACCESS_TOKEN"
        ]
    }

def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  tiktok.py check        # Check connection")
        print("  tiktok.py info         # Get platform info")
        print("  tiktok.py validate '<content>' [media_path]")
        print("  tiktok.py publish '<content>' [media_path]")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        result = check_connection()
        print("🔍 TikTok Connection Status:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "info":
        info = get_platform_info()
        print("ℹ️ TikTok Platform Info:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif command == "validate" and len(sys.argv) >= 3:
        content = sys.argv[2]
        media_path = sys.argv[3] if len(sys.argv) > 3 else None
        media_paths = [media_path] if media_path else []
        
        result = validate_content(content, media_paths)
        
        print("✅ Content Validation:")
        if result["valid"]:
            print("   Valid for TikTok publishing")
        else:
            print("   ❌ Validation failed:")
            for error in result["errors"]:
                print(f"     • {error}")
        
        if result["warnings"]:
            print("   ⚠️ Warnings:")
            for warning in result["warnings"]:
                print(f"     • {warning}")
    
    elif command == "publish" and len(sys.argv) >= 3:
        content = sys.argv[2] 
        media_path = sys.argv[3] if len(sys.argv) > 3 else None
        media_paths = [media_path] if media_path else []
        
        result = publish(content, media_paths)
        
        if result["success"]:
            print("✅ Published to TikTok:")
            print(f"   Post ID: {result.get('post_id')}")
            print(f"   URL: {result.get('post_url')}")
        else:
            print("❌ Publishing failed:")
            print(f"   Error: {result['error']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()