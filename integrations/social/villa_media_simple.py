#!/usr/bin/env python3
"""
Villa Media Simple - Direct Google Drive access for shared folders
Uses public folder sharing instead of API
"""

import requests
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class VillaMediaSimple:
    """
    Simple Villa media manager using public Google Drive folder
    """
    
    def __init__(self):
        self.folder_url = "https://drive.google.com/drive/folders/1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI"
        self.workspace = Path("/home/jonia/.openclaw/workspace")
        self.cache_dir = self.workspace / "cache" / "villa_media"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def list_images_html_scraping(self) -> Dict[str, Any]:
        """
        Get list of images by scraping the public Google Drive folder page
        """
        try:
            # Get the public folder page
            response = requests.get(self.folder_url, timeout=15)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to access folder: {response.status_code}",
                    "fix_hints": [
                        "Make sure folder is shared as 'Anyone with the link can view'",
                        "Check folder URL is correct"
                    ]
                }
            
            # Extract file information from HTML
            html = response.text
            images = {}
            
            # Look for JSON data in the HTML (Google Drive embeds file info)
            # This is a simplified version - the actual extraction would be more complex
            
            # Try to find file IDs and names in the HTML
            # Google Drive pages contain file info in various script tags
            file_pattern = r'"([a-zA-Z0-9_-]{28,})".*?"([^"]+\.(?:jpg|jpeg|png|gif|webp))"'
            matches = re.findall(file_pattern, html, re.IGNORECASE)
            
            for i, (file_id, filename) in enumerate(matches[:20]):  # Limit to first 20 matches
                if len(file_id) > 20:  # Valid Google Drive file ID
                    images[file_id] = {
                        "name": filename,
                        "download_url": f"https://drive.google.com/uc?export=download&id={file_id}",
                        "thumbnail": f"https://drive.google.com/thumbnail?id={file_id}&sz=w400",
                        "size": 0  # Unknown from HTML
                    }
            
            if not images:
                # Fallback: try different pattern or manual file IDs
                # For now, return known structure
                return {
                    "success": True,
                    "images": {},
                    "total_count": 0,
                    "message": "No images found in HTML parsing. Manual file IDs may be needed.",
                    "folder_accessible": True
                }
            
            return {
                "success": True,
                "images": images,
                "total_count": len(images),
                "method": "html_scraping"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"HTML scraping failed: {e}"
            }
    
    def test_manual_file_ids(self) -> Dict[str, Any]:
        """
        Test access to files with manual file IDs
        You need to provide specific file IDs from the Google Drive folder
        """
        
        # These would be actual file IDs from your Villa Lithos folder
        # You can get them by:
        # 1. Right-click image in Drive → "Get link" 
        # 2. Extract ID from URL: drive.google.com/file/d/[FILE_ID]/view
        
        test_files = {
            # "1ABC123DEF456": "villa-pool.jpg",
            # "1XYZ789GHI012": "villa-exterior.jpg",
            # Add your actual file IDs here
        }
        
        working_files = {}
        
        for file_id, filename in test_files.items():
            try:
                # Test if file is accessible
                test_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w200"
                response = requests.head(test_url, timeout=10)
                
                if response.status_code == 200:
                    working_files[file_id] = {
                        "name": filename,
                        "download_url": f"https://drive.google.com/uc?export=download&id={file_id}",
                        "thumbnail": test_url,
                        "accessible": True
                    }
            except:
                pass
        
        return {
            "success": True,
            "working_files": working_files,
            "total_accessible": len(working_files),
            "instructions": [
                "To add more files:",
                "1. Right-click image in Google Drive",
                "2. Choose 'Get link'", 
                "3. Extract file ID from URL",
                "4. Add to test_files dictionary in this function"
            ]
        }
    
    def download_image(self, file_id: str, filename: str) -> Dict[str, Any]:
        """
        Download image from Google Drive using public sharing
        """
        try:
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            response = requests.get(download_url, timeout=60)
            
            if response.status_code == 200:
                # Save to cache
                cache_path = self.cache_dir / f"{file_id}_{filename}"
                
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "local_path": str(cache_path),
                    "size": len(response.content),
                    "file_id": file_id
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed: {response.status_code}",
                    "file_id": file_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Download error: {e}",
                "file_id": file_id
            }

def main():
    """Test the simple Villa media manager"""
    
    print("🏖️ Villa Media Simple - Testing Google Drive Access")
    print("=" * 60)
    
    manager = VillaMediaSimple()
    
    print("1. Testing HTML scraping approach:")
    result1 = manager.list_images_html_scraping()
    
    if result1["success"]:
        print(f"   ✅ Found {result1['total_count']} images via HTML scraping")
        for file_id, info in list(result1["images"].items())[:3]:
            print(f"   📷 {info['name']} (ID: {file_id[:15]}...)")
    else:
        print(f"   ❌ HTML scraping failed: {result1['error']}")
    
    print()
    print("2. Testing manual file IDs:")
    result2 = manager.test_manual_file_ids()
    
    if result2["success"]:
        if result2["working_files"]:
            print(f"   ✅ {result2['total_accessible']} files accessible")
            for file_id, info in result2["working_files"].items():
                print(f"   📷 {info['name']} - accessible")
        else:
            print("   ⚠️ No manual file IDs configured")
            print("   Instructions:")
            for instruction in result2["instructions"]:
                print(f"     • {instruction}")
    
    print()
    print("🎯 Next Steps:")
    print("   1. If HTML scraping worked → use those file IDs")
    print("   2. If not → manually add file IDs from Google Drive")
    print("   3. Test download with: manager.download_image(file_id, filename)")

if __name__ == "__main__":
    main()