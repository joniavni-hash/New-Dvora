#!/usr/bin/env python3
"""
Instagram Publishing Integration via Meta Graph API
"""

import json
import os
import requests
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Instagram API configuration
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

def check_connection() -> Dict[str, Any]:
    """Check Instagram API connection and permissions"""
    
    if not INSTAGRAM_ACCESS_TOKEN:
        return {
            "connected": False,
            "status": "missing_credentials",
            "errors": ["INSTAGRAM_ACCESS_TOKEN not configured"],
            "fix_hints": [
                "Set INSTAGRAM_ACCESS_TOKEN environment variable",
                "Complete Meta for Developers app setup",
                "Connect Instagram Business Account",
                "Generate long-lived access token"
            ]
        }
    
    if not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        return {
            "connected": False,
            "status": "missing_account_id",
            "errors": ["INSTAGRAM_BUSINESS_ACCOUNT_ID not configured"],
            "fix_hints": [
                "Set INSTAGRAM_BUSINESS_ACCOUNT_ID environment variable",
                "Get account ID from Graph API Explorer",
                "Ensure account is Instagram Business Account"
            ]
        }
    
    try:
        # Test API connection and permissions
        params = {
            "fields": "id,username,account_type,media_count",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.get(
            f"{GRAPH_API_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            account_data = response.json()
            
            # Check if it's a business account
            if account_data.get("account_type") != "BUSINESS":
                return {
                    "connected": False,
                    "status": "invalid_account_type",
                    "errors": ["Account must be Instagram Business Account"],
                    "fix_hints": ["Convert to Instagram Business Account in app settings"]
                }
            
            return {
                "connected": True,
                "status": "connected",
                "account_info": {
                    "username": account_data.get("username"),
                    "account_id": account_data.get("id"),
                    "account_type": account_data.get("account_type"),
                    "media_count": account_data.get("media_count", 0)
                },
                "scopes": ["instagram_basic", "instagram_content_publish", "pages_read_engagement"],
                "api_version": "v19.0"
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            return {
                "connected": False,
                "status": "api_error",
                "errors": [f"API returned {response.status_code}: {error_data.get('error', {}).get('message', response.text)}"],
                "fix_hints": ["Check access token validity", "Verify account permissions", "Check token expiration"]
            }
            
    except requests.RequestException as e:
        return {
            "connected": False,
            "status": "connection_error",
            "errors": [f"Network error: {e}"],
            "fix_hints": ["Check internet connection", "Verify Facebook Graph API endpoint"]
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "errors": [f"Unexpected error: {e}"]
        }

def validate_content(content: str, media_paths: List[str] = None) -> Dict[str, Any]:
    """Validate content for Instagram publishing"""
    
    validation = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Content length validation
    if len(content) > 2200:
        validation["valid"] = False
        validation["errors"].append(f"Caption too long: {len(content)} > 2200 characters")
    
    # Media validation
    if not media_paths:
        validation["valid"] = False
        validation["errors"].append("Instagram posts require at least one media file")
    else:
        for media_path in media_paths:
            file_path = Path(media_path)
            
            if not file_path.exists():
                validation["valid"] = False
                validation["errors"].append(f"Media file not found: {media_path}")
                continue
            
            file_extension = file_path.suffix.lower()
            file_size = file_path.stat().st_size
            
            # Check file format
            if file_extension in ['.jpg', '.jpeg', '.png']:
                # Image validation
                if file_size > 8 * 1024 * 1024:  # 8MB limit for images
                    validation["valid"] = False
                    validation["errors"].append(f"Image file too large: {file_size} bytes > 8MB")
                    
            elif file_extension in ['.mp4', '.mov']:
                # Video validation
                if file_size > 100 * 1024 * 1024:  # 100MB limit for videos
                    validation["valid"] = False
                    validation["errors"].append(f"Video file too large: {file_size} bytes > 100MB")
            else:
                validation["valid"] = False
                validation["errors"].append(f"Unsupported file format: {file_extension}")
        
        # Check number of media files
        if len(media_paths) > 10:
            validation["valid"] = False
            validation["errors"].append(f"Too many media files: {len(media_paths)} > 10 (carousel limit)")
    
    # Hashtag validation
    hashtag_count = content.count('#')
    if hashtag_count > 30:
        validation["warnings"].append(f"Many hashtags detected ({hashtag_count}). Instagram recommends 3-5 relevant hashtags.")
    
    return validation

def publish(content: str, media_paths: List[str] = None, draft_meta: Dict = None) -> Dict[str, Any]:
    """
    Publish content to Instagram
    
    Instagram publishing is a 2-step process:
    1. Create media container (upload media + caption)
    2. Publish the container
    """
    
    # Check connection first
    connection_status = check_connection()
    if not connection_status["connected"]:
        return {
            "success": False,
            "error": "Not connected to Instagram",
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
        # Step 1: Create media container(s)
        if len(media_paths) == 1:
            # Single media post
            container_result = _create_media_container(content, media_paths[0])
        else:
            # Carousel post (multiple media)
            container_result = _create_carousel_container(content, media_paths)
        
        if not container_result["success"]:
            return container_result
        
        container_id = container_result["container_id"]
        
        # Step 2: Publish the container
        publish_result = _publish_container(container_id)
        
        if publish_result["success"]:
            return {
                "success": True,
                "post_id": publish_result["post_id"],
                "post_url": f"https://www.instagram.com/p/{publish_result['post_id']}/",
                "container_id": container_id,
                "status": "published",
                "platform_response": publish_result
            }
        else:
            return publish_result
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Publishing failed: {e}"
        }

def _create_media_container(caption: str, media_path: str) -> Dict[str, Any]:
    """Create single media container"""
    
    try:
        file_path = Path(media_path)
        file_extension = file_path.suffix.lower()
        
        # Upload media and get URL (simplified - real implementation would upload to Meta's servers)
        # For now, we'll assume media is already accessible via URL
        media_url = f"file://{file_path.absolute()}"  # Placeholder - needs real URL
        
        # Create container
        container_data = {
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        if file_extension in ['.jpg', '.jpeg', '.png']:
            container_data["image_url"] = media_url
        elif file_extension in ['.mp4', '.mov']:
            container_data["video_url"] = media_url
            container_data["media_type"] = "VIDEO"
        
        response = requests.post(
            f"{GRAPH_API_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media",
            data=container_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            return {
                "success": True,
                "container_id": result_data.get("id")
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            return {
                "success": False,
                "error": f"Container creation failed: {response.status_code}",
                "details": error_data.get("error", {}).get("message", response.text)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Media container creation failed: {e}"
        }

def _create_carousel_container(caption: str, media_paths: List[str]) -> Dict[str, Any]:
    """Create carousel media container"""
    
    try:
        # Create individual containers for each media
        child_containers = []
        
        for media_path in media_paths:
            child_result = _create_media_container("", media_path)  # No caption for child containers
            if not child_result["success"]:
                return child_result
            child_containers.append(child_result["container_id"])
        
        # Create carousel container
        carousel_data = {
            "caption": caption,
            "media_type": "CAROUSEL",
            "children": ",".join(child_containers),
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.post(
            f"{GRAPH_API_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media",
            data=carousel_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            return {
                "success": True,
                "container_id": result_data.get("id"),
                "child_containers": child_containers
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            return {
                "success": False,
                "error": f"Carousel creation failed: {response.status_code}",
                "details": error_data.get("error", {}).get("message", response.text)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Carousel container creation failed: {e}"
        }

def _publish_container(container_id: str) -> Dict[str, Any]:
    """Publish media container to Instagram"""
    
    try:
        publish_data = {
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        
        response = requests.post(
            f"{GRAPH_API_BASE}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish",
            data=publish_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            return {
                "success": True,
                "post_id": result_data.get("id"),
                "published_at": time.time()
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            return {
                "success": False,
                "error": f"Publishing failed: {response.status_code}",
                "details": error_data.get("error", {}).get("message", response.text)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Container publishing failed: {e}"
        }

def get_platform_info() -> Dict[str, Any]:
    """Get Instagram platform information and requirements"""
    return {
        "platform": "instagram",
        "display_name": "Instagram",
        "content_types": ["image", "video", "carousel"],
        "max_image_size": 8 * 1024 * 1024,  # 8MB
        "max_video_size": 100 * 1024 * 1024,  # 100MB  
        "max_caption_length": 2200,
        "max_carousel_items": 10,
        "supported_image_formats": [".jpg", ".jpeg", ".png"],
        "supported_video_formats": [".mp4", ".mov"],
        "image_requirements": {
            "min_resolution": "320x320",
            "max_resolution": "1440x1440", 
            "aspect_ratios": ["1:1", "4:5", "1.91:1"]
        },
        "video_requirements": {
            "min_duration": 3,  # seconds
            "max_duration": 60,  # 1 minute for feed videos
            "aspect_ratios": ["4:5", "1:1", "9:16"],
            "recommended_resolution": "1080x1080"
        },
        "authentication": "facebook_oauth2",
        "scopes_required": ["instagram_basic", "instagram_content_publish", "pages_read_engagement"],
        "api_documentation": "https://developers.facebook.com/docs/instagram-api/",
        "setup_instructions": [
            "Create Facebook for Developers account",
            "Create app and add Instagram Basic Display product",
            "Configure Instagram Business Account",
            "Generate long-lived access token",
            "Set environment variables: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID"
        ]
    }

def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  instagram.py check        # Check connection")
        print("  instagram.py info         # Get platform info") 
        print("  instagram.py validate '<content>' <media_path1> [media_path2...]")
        print("  instagram.py publish '<content>' <media_path1> [media_path2...]")
        return
    
    command = sys.argv[1]
    
    if command == "check":
        result = check_connection()
        print("🔍 Instagram Connection Status:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "info":
        info = get_platform_info()
        print("ℹ️ Instagram Platform Info:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    
    elif command == "validate" and len(sys.argv) >= 4:
        content = sys.argv[2]
        media_paths = sys.argv[3:]
        
        result = validate_content(content, media_paths)
        
        print("✅ Content Validation:")
        if result["valid"]:
            print("   Valid for Instagram publishing")
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
        media_paths = sys.argv[3:]
        
        result = publish(content, media_paths)
        
        if result["success"]:
            print("✅ Published to Instagram:")
            print(f"   Post ID: {result.get('post_id')}")
            print(f"   URL: {result.get('post_url')}")
        else:
            print("❌ Publishing failed:")
            print(f"   Error: {result['error']}")
            if result.get('details'):
                print(f"   Details: {result['details']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()