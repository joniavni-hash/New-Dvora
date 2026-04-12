#!/usr/bin/env python3
"""
Villa Media Manager - Google OAuth2 Integration
Uses existing GoG CLI credentials for Google Drive access
"""

import json
import requests
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class VillaMediaOAuth:
    """
    Villa media manager using OAuth2 credentials from GoG CLI
    """
    
    def __init__(self):
        self.workspace = Path("/home/jonia/.openclaw/workspace")
        self.gog_config_dir = Path("/home/jonia/.config/gogcli")
        self.credentials_file = self.gog_config_dir / "credentials.json"
        self.client_secret_file = self.gog_config_dir / "client_secret.json"
        
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        
        self._load_credentials()
    
    def _load_credentials(self):
        """Load OAuth2 credentials from GoG CLI config"""
        try:
            # Load client ID and secret
            if self.client_secret_file.exists():
                with open(self.client_secret_file, 'r') as f:
                    client_data = json.load(f)
                    self.client_id = client_data["installed"]["client_id"]
                    self.client_secret = client_data["installed"]["client_secret"]
            
            # Try to get access token from gog CLI
            self._get_access_token()
            
        except Exception as e:
            print(f"Failed to load credentials: {e}")
    
    def _get_access_token(self):
        """Get access token using gog CLI"""
        try:
            # Try gog CLI token command
            result = os.popen("gog auth status").read()
            if "authenticated" in result.lower():
                # Get token via gog CLI internal method
                token_result = os.popen("gog drive list --limit 1 2>&1").read()
                # This forces token refresh if needed
                self.access_token = "via_gog_cli"
            
        except Exception as e:
            print(f"Token acquisition failed: {e}")
    
    def list_drive_images(self, folder_id: str) -> Dict[str, Any]:
        """
        List images in Google Drive folder using gog CLI
        """
        
        try:
            # Use gog CLI to list files in folder
            cmd = f"gog drive list --parent '{folder_id}' --mime-type 'image/' --fields 'id,name,size,modifiedTime,thumbnailLink'"
            result = os.popen(cmd).read()
            
            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "error": f"GoG CLI error: {result}",
                    "fix_hints": [
                        "Run: gog auth login",
                        "Ensure Drive API is enabled",
                        "Check folder permissions"
                    ]
                }
            
            # Parse gog CLI output (assuming JSON-like format)
            # This is a simplified version - gog CLI might return different format
            images = {}
            lines = result.strip().split('\n')
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    try:
                        # Try to parse as tab-separated or JSON
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            file_id = parts[0]
                            file_name = parts[1]
                            images[file_id] = {
                                "name": file_name,
                                "size": 0,  # Will be populated by actual API call
                                "cached": False
                            }
                    except:
                        continue
            
            return {
                "success": True,
                "images": images,
                "total_count": len(images),
                "folder_id": folder_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list images: {e}"
            }
    
    def download_image_via_gog(self, file_id: str, output_dir: str) -> Dict[str, Any]:
        """
        Download image using gog CLI
        """
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Download via gog CLI
            cmd = f"gog drive download '{file_id}' --output-dir '{output_path}'"
            result = os.popen(cmd).read()
            
            if "downloaded" in result.lower():
                # Find the downloaded file
                downloaded_files = list(output_path.glob(f"*{file_id}*"))
                if not downloaded_files:
                    downloaded_files = list(output_path.glob("*"))
                
                if downloaded_files:
                    return {
                        "success": True,
                        "local_path": str(downloaded_files[0]),
                        "size": downloaded_files[0].stat().st_size
                    }
            
            return {
                "success": False,
                "error": f"Download failed: {result}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Download error: {e}"
            }

def main():
    """Quick test of OAuth integration"""
    
    print("🔧 Villa Media OAuth Integration Test")
    print("=" * 50)
    
    manager = VillaMediaOAuth()
    
    # Test folder ID
    folder_id = "1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI"
    
    print(f"Testing folder: {folder_id}")
    result = manager.list_drive_images(folder_id)
    
    if result["success"]:
        print(f"✅ Found {result['total_count']} images:")
        for file_id, info in list(result["images"].items())[:5]:  # Show first 5
            print(f"   📷 {info['name']} (ID: {file_id[:15]}...)")
    else:
        print(f"❌ Failed: {result['error']}")
        if "fix_hints" in result:
            print("Fix hints:")
            for hint in result["fix_hints"]:
                print(f"   • {hint}")

if __name__ == "__main__":
    main()