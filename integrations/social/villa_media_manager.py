#!/usr/bin/env python3
"""
Villa Lithos Media Manager - Google Drive Integration for Social Posts
Only approved images from specific Google Drive folder get used for posting
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Google Drive API configuration
GOOGLE_DRIVE_API_KEY = os.getenv("GOOGLE_DRIVE_API_KEY", "")
VILLA_DRIVE_FOLDER_ID = os.getenv("VILLA_DRIVE_FOLDER_ID", "")

class VillaMediaManager:
    """
    Manages Villa Lithos media from Google Drive for social posting
    - Lists approved images from specific Drive folder
    - Downloads and uploads to Postiz
    - Tracks which images are used for which posts
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace = Path(workspace_path or "/home/ubuntu/.openclaw/workspace")
        self.media_cache = self.workspace / "cache" / "villa_media"
        self.media_cache.mkdir(parents=True, exist_ok=True)
        self.usage_log = self.workspace / "state" / "villa_media_usage.json"
        
    def list_approved_images(self) -> Dict[str, Any]:
        """
        List all images in the Villa Lithos Google Drive folder
        Returns: {image_id: {name, thumbnail, download_url, size, modified}}
        """
        
        if not GOOGLE_DRIVE_API_KEY:
            return {
                "success": False,
                "error": "Google Drive API key not configured",
                "setup_steps": [
                    "Go to Google Cloud Console",
                    "Enable Google Drive API", 
                    "Create API key with Drive permissions",
                    "Set GOOGLE_DRIVE_API_KEY environment variable"
                ]
            }
            
        if not VILLA_DRIVE_FOLDER_ID:
            return {
                "success": False,
                "error": "Villa Drive folder ID not configured",
                "setup_steps": [
                    "Share the Villa Lithos photos folder with 'Anyone with link can view'",
                    "Copy folder ID from URL: drive.google.com/drive/folders/[FOLDER_ID]",
                    "Set VILLA_DRIVE_FOLDER_ID environment variable"
                ]
            }
        
        try:
            # List files in the Villa folder
            url = f"https://www.googleapis.com/drive/v3/files"
            params = {
                "key": GOOGLE_DRIVE_API_KEY,
                "q": f"parents in '{VILLA_DRIVE_FOLDER_ID}' and mimeType contains 'image/'",
                "fields": "files(id,name,thumbnailLink,size,modifiedTime,webContentLink)",
                "orderBy": "modifiedTime desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                images = {}
                
                for file in data.get("files", []):
                    images[file["id"]] = {
                        "name": file.get("name"),
                        "thumbnail": file.get("thumbnailLink"),
                        "download_url": file.get("webContentLink"),
                        "size": int(file.get("size", 0)),
                        "modified": file.get("modifiedTime"),
                        "cached": self._is_cached(file["id"])
                    }
                
                return {
                    "success": True,
                    "images": images,
                    "total_count": len(images),
                    "folder_id": VILLA_DRIVE_FOLDER_ID
                }
            else:
                return {
                    "success": False,
                    "error": f"Google Drive API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list Drive images: {e}"
            }
    
    def download_image(self, image_id: str, image_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download image from Google Drive to local cache
        Returns: {success, local_path, size}
        """
        
        try:
            cache_path = self.media_cache / f"{image_id}_{image_info['name']}"
            
            # Skip if already cached
            if cache_path.exists():
                return {
                    "success": True,
                    "local_path": str(cache_path),
                    "size": cache_path.stat().st_size,
                    "cached": True
                }
            
            # Download from Google Drive
            download_url = image_info["download_url"]
            response = requests.get(download_url, timeout=60)
            
            if response.status_code == 200:
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "local_path": str(cache_path),
                    "size": len(response.content),
                    "cached": False
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Download error: {e}"
            }
    
    def upload_to_postiz(self, image_path: str) -> Dict[str, Any]:
        """
        Upload image from local cache to Postiz CDN
        Returns: {success, postiz_id, postiz_url}
        """
        
        # Import Postiz functionality
        try:
            from integrations.social.postiz_real import upload_image
            return upload_image(image_path)
        except ImportError:
            return {
                "success": False,
                "error": "Postiz integration not available"
            }
    
    def prepare_images_for_post(self, selected_image_ids: List[str]) -> Dict[str, Any]:
        """
        Prepare specific images for social posting
        1. List approved images from Drive
        2. Download selected images
        3. Upload to Postiz
        4. Return Postiz image objects for posting
        """
        
        # Step 1: Get available images
        available = self.list_approved_images()
        if not available["success"]:
            return available
        
        images = available["images"]
        postiz_images = []
        
        # Step 2-3: Process each selected image
        for image_id in selected_image_ids:
            if image_id not in images:
                return {
                    "success": False,
                    "error": f"Image {image_id} not found in Drive folder",
                    "available_images": list(images.keys())
                }
            
            image_info = images[image_id]
            
            # Download from Drive
            download_result = self.download_image(image_id, image_info)
            if not download_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to download {image_info['name']}: {download_result['error']}"
                }
            
            # Upload to Postiz
            postiz_result = self.upload_to_postiz(download_result["local_path"])
            if not postiz_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to upload {image_info['name']} to Postiz: {postiz_result['error']}"
                }
            
            # Add to results
            postiz_images.append({
                "id": postiz_result["id"],
                "path": postiz_result["path"], 
                "drive_id": image_id,
                "name": image_info["name"]
            })
        
        # Step 4: Log usage
        self._log_usage(selected_image_ids, postiz_images)
        
        return {
            "success": True,
            "postiz_images": postiz_images,
            "total_uploaded": len(postiz_images)
        }
    
    def _is_cached(self, image_id: str) -> bool:
        """Check if image is already in local cache"""
        cache_files = list(self.media_cache.glob(f"{image_id}_*"))
        return len(cache_files) > 0
    
    def _log_usage(self, drive_image_ids: List[str], postiz_images: List[Dict[str, Any]]):
        """Log which images were used for which posts"""
        
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "drive_images": drive_image_ids,
            "postiz_uploads": postiz_images
        }
        
        # Load existing log
        usage_log = []
        if self.usage_log.exists():
            try:
                with open(self.usage_log, 'r', encoding='utf-8') as f:
                    usage_log = json.load(f)
            except:
                pass
        
        # Add new entry
        usage_log.append(usage_entry)
        
        # Keep only last 100 entries
        usage_log = usage_log[-100:]
        
        # Save back
        with open(self.usage_log, 'w', encoding='utf-8') as f:
            json.dump(usage_log, f, indent=2, ensure_ascii=False)

def main():
    """CLI interface for Villa media management"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  villa_media_manager.py list")  
        print("  villa_media_manager.py prepare <image_id1> <image_id2> ...")
        print("  villa_media_manager.py setup")
        return
    
    manager = VillaMediaManager()
    command = sys.argv[1]
    
    if command == "list":
        result = manager.list_approved_images()
        
        if result["success"]:
            print("📂 Villa Lithos Images in Google Drive:")
            print(f"   Folder: {result['folder_id']}")
            print(f"   Total: {result['total_count']} images\n")
            
            for img_id, info in result["images"].items():
                cached = "📁" if info["cached"] else "☁️"
                size_mb = info["size"] / (1024*1024) if info["size"] > 0 else 0
                print(f"   {cached} {info['name']}")
                print(f"      ID: {img_id}")
                print(f"      Size: {size_mb:.1f} MB")
                print(f"      Modified: {info['modified']}")
                print()
        else:
            print("❌ Failed to list images:")
            print(f"   Error: {result['error']}")
            if "setup_steps" in result:
                print("   Setup steps:")
                for step in result["setup_steps"]:
                    print(f"     • {step}")
    
    elif command == "prepare" and len(sys.argv) > 2:
        image_ids = sys.argv[2:]
        result = manager.prepare_images_for_post(image_ids)
        
        if result["success"]:
            print(f"✅ Prepared {result['total_uploaded']} images for posting:")
            for img in result["postiz_images"]:
                print(f"   📷 {img['name']}")
                print(f"      Postiz ID: {img['id']}")
                print(f"      URL: {img['path']}")
                print()
        else:
            print("❌ Failed to prepare images:")
            print(f"   Error: {result['error']}")
    
    elif command == "setup":
        print("🔧 Villa Media Manager Setup:")
        print()
        print("1. Google Drive API Key:")
        if GOOGLE_DRIVE_API_KEY:
            print("   ✅ Configured")
        else:
            print("   ❌ Not configured")
            print("   Steps:")
            print("   • Go to Google Cloud Console")
            print("   • Enable Google Drive API")
            print("   • Create API key")
            print("   • export GOOGLE_DRIVE_API_KEY='your_key_here'")
        print()
        
        print("2. Villa Folder ID:")
        if VILLA_DRIVE_FOLDER_ID:
            print(f"   ✅ Configured: {VILLA_DRIVE_FOLDER_ID}")
        else:
            print("   ❌ Not configured")
            print("   Steps:")
            print("   • Share Villa photos folder: 'Anyone with link can view'")
            print("   • Copy folder ID from URL")
            print("   • export VILLA_DRIVE_FOLDER_ID='folder_id_here'")
        print()
        
        print("3. Test connection:")
        if GOOGLE_DRIVE_API_KEY and VILLA_DRIVE_FOLDER_ID:
            result = manager.list_approved_images()
            if result["success"]:
                print(f"   ✅ Connection working - {result['total_count']} images found")
            else:
                print(f"   ❌ Connection failed: {result['error']}")
        else:
            print("   ⏸️ Configure API key and folder ID first")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()