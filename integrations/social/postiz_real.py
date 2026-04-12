#!/usr/bin/env python3
"""
Real Postiz Integration - Based on actual API documentation
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Postiz API configuration
POSTIZ_BASE_URL = os.getenv("POSTIZ_BASE_URL", "https://api.postiz.com/public/v1")
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY", "")

def check_connection() -> Dict[str, Any]:
    """Check Postiz API connection and get connected integrations"""
    
    if not POSTIZ_API_KEY:
        return {
            "connected": False,
            "status": "missing_api_key", 
            "errors": ["POSTIZ_API_KEY not configured"],
            "fix_hints": [
                "Get API key from Postiz: Settings > Developers > Public API",
                "Set POSTIZ_API_KEY environment variable"
            ]
        }
    
    try:
        headers = {
            "Authorization": POSTIZ_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Get connected integrations
        response = requests.get(
            f"{POSTIZ_BASE_URL}/integrations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            integrations = response.json()
            
            # Parse integrations by platform
            platforms = {}
            for integration in integrations:
                platform = integration.get("identifier")
                if platform not in platforms:
                    platforms[platform] = []
                
                platforms[platform].append({
                    "id": integration.get("id"),
                    "name": integration.get("name"),
                    "profile": integration.get("profile"),
                    "picture": integration.get("picture"),
                    "disabled": integration.get("disabled", False)
                })
            
            return {
                "connected": True,
                "status": "connected",
                "total_integrations": len(integrations),
                "platforms": platforms,
                "integrations": integrations,
                "api_version": "v1"
            }
        else:
            return {
                "connected": False,
                "status": "api_error",
                "errors": [f"API returned {response.status_code}: {response.text}"],
                "fix_hints": ["Check API key validity", "Verify Postiz API access"]
            }
            
    except requests.RequestException as e:
        return {
            "connected": False,
            "status": "connection_error",
            "errors": [f"Network error: {e}"],
            "fix_hints": ["Check internet connection", "Verify Postiz API URL"]
        }

def publish_villa_lithos_post(content: str, platforms: List[str] = None, 
                             image_paths: List[str] = None, 
                             schedule_time: str = None,
                             use_clean_images: bool = False,
                             skip_tiktok: bool = False) -> Dict[str, Any]:
    """
    Publish Villa Lithos post to specified platforms
    
    Args:
        content: Post content
        platforms: List of platforms (tiktok, instagram, facebook, pinterest)
        image_paths: List of image file paths to upload and attach
        schedule_time: ISO timestamp for scheduling (optional, publishes now if None)
    
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
    
    # Default platforms
    if not platforms:
        platforms = ["instagram", "facebook", "pinterest"] if skip_tiktok else ["tiktok", "instagram", "facebook"]
        
    # Filter out TikTok if skip_tiktok is True
    if skip_tiktok:
        platforms = [p for p in platforms if p != "tiktok"]
    
    # Get integrations for requested platforms
    available_integrations = connection_status["integrations"]
    platform_integrations = {}
    
    for platform in platforms:
        # Find integration for this platform
        integration = next((i for i in available_integrations 
                          if i.get("identifier") == platform and not i.get("disabled")), None)
        
        if integration:
            platform_integrations[platform] = integration
        else:
            return {
                "success": False,
                "error": f"No active {platform} integration found",
                "available_platforms": [i.get("identifier") for i in available_integrations]
            }
    
    try:
        # Step 1: Upload images if provided
        uploaded_images = []
        if image_paths:
            for image_path in image_paths:
                upload_result = upload_image(image_path)
                if upload_result["success"]:
                    uploaded_images.append({
                        "id": upload_result["id"],
                        "path": upload_result["path"]
                    })
                else:
                    return {
                        "success": False,
                        "error": f"Image upload failed: {upload_result['error']}"
                    }
        
        # Step 2: Build posts array for API
        posts = []
        for platform, integration in platform_integrations.items():
            
            # Platform-specific settings
            settings = {"__type": platform}
            
            if platform == "tiktok":
                # TikTok requires all these specific settings
                settings.update({
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "duet": True,
                    "stitch": True, 
                    "comment": True,
                    "autoAddMusic": "no",
                    "brand_content_toggle": False,
                    "brand_organic_toggle": False,
                    "content_posting_method": "DIRECT_POST"
                })
            elif platform == "instagram":
                settings.update({
                    "post_type": "post"  # or "story", "reel"
                })
            elif platform == "pinterest":
                settings.update({
                    "title": "Villa Lithos - Luxury Greek Villa",
                    "board": "Villa Lithos"
                })
            
            # Build post object
            post = {
                "integration": {"id": integration["id"]},
                "value": [{
                    "content": content,
                    "image": uploaded_images
                }],
                "settings": settings
            }
            
            posts.append(post)
        
        # Step 3: Create the post request
        post_data = {
            "type": "schedule" if schedule_time else "now",
            "date": schedule_time or datetime.now().isoformat(),
            "shortLink": False,
            "tags": [],
            "posts": posts
        }
        
        # Step 4: Send to Postiz API
        headers = {
            "Authorization": POSTIZ_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{POSTIZ_BASE_URL}/posts",
            headers=headers,
            json=post_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result_data = response.json()
            
            # Handle case where result_data might be a list
            if isinstance(result_data, list):
                result_data = result_data[0] if result_data else {}
            elif not isinstance(result_data, dict):
                result_data = {}
            
            post_id = result_data.get("id", "unknown")
            
            return {
                "success": True,
                "post_id": post_id,
                "postiz_url": f"https://platform.postiz.com/posts/{post_id}",
                "platforms": list(platform_integrations.keys()),
                "scheduled": schedule_time is not None,
                "status": "scheduled" if schedule_time else "published",
                "content": content,
                "images_uploaded": len(uploaded_images),
                "postiz_response": result_data
            }
        else:
            error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else {}
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

def upload_image(image_path: str) -> Dict[str, Any]:
    """Upload image to Postiz"""
    
    if not POSTIZ_API_KEY:
        return {"success": False, "error": "API key not configured"}
    
    file_path = Path(image_path)
    if not file_path.exists():
        return {"success": False, "error": f"Image file not found: {image_path}"}
    
    try:
        headers = {"Authorization": POSTIZ_API_KEY}
        
        with open(file_path, 'rb') as file:
            files = {"file": (file_path.name, file, "image/jpeg")}
            
            response = requests.post(
                f"{POSTIZ_BASE_URL}/upload",
                headers=headers,
                files=files,
                timeout=60
            )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                "success": True,
                "id": result.get("id"),
                "path": result.get("path"),
                "filename": result.get("filename", file_path.name)
            }
        else:
            return {
                "success": False,
                "error": f"Upload failed: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload error: {e}"
        }

def get_platform_info() -> Dict[str, Any]:
    """Get platform information and setup status"""
    
    connection_status = check_connection()
    
    return {
        "platform": "postiz", 
        "display_name": "Postiz Social Media Manager",
        "api_base": POSTIZ_BASE_URL,
        "connected": connection_status["connected"],
        "available_platforms": list(connection_status.get("platforms", {}).keys()) if connection_status["connected"] else [],
        "total_integrations": connection_status.get("total_integrations", 0),
        "supported_platforms": {
            "social": ["tiktok", "instagram", "facebook", "x", "linkedin", "threads", "mastodon", "bluesky"],
            "video": ["youtube", "tiktok"],
            "community": ["reddit", "discord", "slack"],
            "design": ["pinterest", "dribbble"],
            "blogging": ["medium", "devto", "hashnode", "wordpress"],
            "business": ["gmb", "listmonk"]
        },
        "features": [
            "Multi-platform publishing",
            "Image upload support",
            "Scheduled posting",
            "32 supported platforms",
            "Rate limit: 30 requests/hour"
        ],
        "villa_lithos_ready": connection_status["connected"] and "tiktok" in connection_status.get("platforms", {}),
        "setup_status": connection_status
    }

def main():
    """CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  postiz_real.py check")
        print("  postiz_real.py info")
        print("  postiz_real.py villa-post '<content>' [platforms_csv] [image_path]")
        print("  postiz_real.py upload <image_path>")
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
    
    elif command == "villa-post" and len(sys.argv) >= 3:
        content = sys.argv[2]
        platforms = sys.argv[3].split(',') if len(sys.argv) > 3 else ["tiktok", "instagram"]
        image_path = sys.argv[4] if len(sys.argv) > 4 else None
        image_paths = [image_path] if image_path else []
        
        result = publish_villa_lithos_post(content, platforms, image_paths)
        
        if result["success"]:
            print("✅ Villa Lithos post published!")
            print(f"   Post ID: {result['post_id']}")
            print(f"   Platforms: {', '.join(result['platforms'])}")
            print(f"   Status: {result['status']}")
            print(f"   URL: {result['postiz_url']}")
            if result['images_uploaded'] > 0:
                print(f"   Images: {result['images_uploaded']} uploaded")
        else:
            print("❌ Publishing failed:")
            print(f"   Error: {result['error']}")
            if result.get('details'):
                print(f"   Details: {result['details']}")
    
    elif command == "upload" and len(sys.argv) >= 3:
        image_path = sys.argv[2]
        result = upload_image(image_path)
        
        if result["success"]:
            print("✅ Image uploaded:")
            print(f"   ID: {result['id']}")
            print(f"   URL: {result['path']}")
        else:
            print(f"❌ Upload failed: {result['error']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()