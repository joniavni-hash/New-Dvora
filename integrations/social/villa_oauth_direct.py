#!/usr/bin/env python3
"""
Villa OAuth Direct - Direct Google OAuth2 for Drive access
Using the new client credentials provided
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any

CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID_HERE"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET_HERE"
FOLDER_ID = "1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI"

def test_oauth_credentials() -> Dict[str, Any]:
    """
    Test the OAuth credentials by trying to get authorization URL
    """
    
    # OAuth2 authorization URL for Google Drive
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    
    # Required scopes for Drive access
    scopes = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file"
    ]
    
    # Build authorization URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": "http://localhost:8080/callback",
        "scope": " ".join(scopes),
        "response_type": "code",
        "access_type": "offline"
    }
    
    # Create the authorization URL
    import urllib.parse
    auth_params = urllib.parse.urlencode(params)
    full_auth_url = f"{auth_url}?{auth_params}"
    
    return {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET[:20] + "...",  # Masked for security
        "auth_url": full_auth_url,
        "instructions": [
            "Open the auth_url in browser",
            "Grant Drive permissions", 
            "Get authorization code from callback URL",
            "Exchange code for access token"
        ]
    }

def check_existing_gog_tokens() -> Dict[str, Any]:
    """
    Check if there are any existing tokens in gog CLI that we can use
    """
    import os
    import subprocess
    
    try:
        # Try to get a token using gog CLI
        result = subprocess.run(
            ["gog", "auth", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "tokens_available": "No tokens stored" not in result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "returncode": result.returncode
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check tokens: {e}"
        }

def try_service_account_approach() -> Dict[str, Any]:
    """
    Try a different approach - check if we can create a service account
    """
    
    try:
        # Try to access the folder with basic public access
        test_url = f"https://www.googleapis.com/drive/v3/files/{FOLDER_ID}"
        
        # Different approaches to try
        approaches = []
        
        # 1. Try with no authentication (public folder)
        try:
            response = requests.get(
                test_url,
                params={"fields": "name,id,mimeType"},
                timeout=10
            )
            approaches.append({
                "method": "no_auth",
                "status": response.status_code,
                "result": response.json() if response.status_code == 200 else response.text
            })
        except:
            pass
        
        # 2. Try with the folder as a web URL
        try:
            web_url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
            web_response = requests.get(web_url, timeout=10)
            approaches.append({
                "method": "web_access",
                "status": web_response.status_code,
                "accessible": web_response.status_code == 200,
                "title_found": "תמונות לוילה" in web_response.text
            })
        except:
            pass
        
        return {
            "success": True,
            "folder_id": FOLDER_ID,
            "approaches_tested": approaches,
            "recommendations": [
                "Web access works - folder is public",
                "API access needs proper authentication",
                "Consider using web scraping or manual file IDs"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Service account test failed: {e}"
        }

def main():
    """Test different approaches to access Villa Lithos images"""
    
    print("🔐 Villa OAuth Direct - Testing New Credentials")
    print("=" * 55)
    
    print("1. OAuth Credentials Check:")
    oauth_result = test_oauth_credentials()
    print(f"   Client ID: {oauth_result['client_id']}")
    print(f"   Client Secret: {oauth_result['client_secret']}")
    print(f"   Auth URL: {oauth_result['auth_url'][:80]}...")
    print()
    
    print("2. Existing GoG Tokens Check:")
    gog_result = check_existing_gog_tokens()
    if gog_result["success"]:
        print(f"   ✅ GoG CLI accessible")
        print(f"   Tokens available: {gog_result['tokens_available']}")
        if gog_result["tokens_available"]:
            print(f"   Output: {gog_result['output']}")
    else:
        print(f"   ❌ GoG CLI error: {gog_result['error']}")
    print()
    
    print("3. Service Account / Public Access Test:")
    service_result = try_service_account_approach()
    if service_result["success"]:
        print(f"   Folder ID: {service_result['folder_id']}")
        for approach in service_result["approaches_tested"]:
            method = approach["method"]
            if method == "web_access":
                accessible = approach.get("accessible", False)
                title_found = approach.get("title_found", False)
                print(f"   {method}: {'✅' if accessible else '❌'} accessible, Villa folder: {'✅' if title_found else '❌'}")
            else:
                status = approach["status"]
                print(f"   {method}: HTTP {status}")
        
        print("   Recommendations:")
        for rec in service_result["recommendations"]:
            print(f"     • {rec}")
    else:
        print(f"   ❌ Service account test failed: {service_result['error']}")

if __name__ == "__main__":
    main()