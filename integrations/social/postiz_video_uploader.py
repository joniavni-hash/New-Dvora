#!/usr/bin/env python3
"""
Villa Lithos TikTok Video Uploader via Postiz
Upload video directly to TikTok using Postiz API with proper video settings
"""

import os
import requests
import json
from pathlib import Path

def upload_video_to_postiz(video_path, caption, api_key, integration_id):
    """Upload video to TikTok via Postiz API"""
    
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return False
    
    print(f"🎬 Uploading video: {video_path}")
    print(f"📝 Caption: {caption[:50]}...")
    
    # Step 1: Upload video file
    try:
        print("📤 Uploading video file...")
        
        with open(video_path, 'rb') as video_file:
            files = {
                'file': (Path(video_path).name, video_file, 'video/mp4')
            }
            
            headers = {
                'Authorization': api_key
            }
            
            upload_response = requests.post(
                'https://api.postiz.com/public/v1/upload',
                headers=headers,
                files=files,
                timeout=120
            )
            
        if upload_response.status_code not in [200, 201]:
            print(f"❌ Video upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
            
        upload_data = upload_response.json()
        video_id = upload_data.get('id')
        video_url = upload_data.get('path')
        
        print(f"✅ Video uploaded - ID: {video_id}")
        
    except Exception as e:
        print(f"❌ Video upload error: {e}")
        return False
    
    # Step 2: Create TikTok post with video
    try:
        print("🎯 Creating TikTok post...")
        
        from datetime import datetime
        
        post_data = {
            "type": "now",
            "date": datetime.now().isoformat(),
            "shortLink": False,
            "tags": [],
            "posts": [{
                "integration": {"id": integration_id},
                "value": [{
                    "content": caption,
                    "image": [],  # Required even for video
                    "video": [{
                        "id": video_id,
                        "path": video_url
                    }]
                }],
                "settings": {
                    "__type": "tiktok",
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "duet": True,
                    "stitch": True,
                    "comment": True,
                    "autoAddMusic": "no",
                    "brand_content_toggle": False,
                    "brand_organic_toggle": False,
                    "content_posting_method": "DIRECT_POST"
                }
            }]
        }
        
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        post_response = requests.post(
            'https://api.postiz.com/public/v1/posts',
            headers=headers,
            json=post_data,
            timeout=60
        )
        
        if post_response.status_code in [200, 201]:
            result = post_response.json()
            print("✅ TikTok post created successfully!")
            
            # Handle response format (might be list or dict)
            if isinstance(result, list):
                result = result[0] if result else {}
            
            post_id = result.get('postId', result.get('id', 'Unknown'))
            print(f"📱 Post ID: {post_id}")
            return True
        else:
            print(f"❌ Post creation failed: {post_response.status_code}")
            print(f"Response: {post_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Post creation error: {e}")
        return False

def main():
    print("🎬 Villa Lithos TikTok Video Uploader\\n")
    
    # Configuration
    video_path = "villa_slides_test/villa_tiktok_video.mp4"
    api_key = "YOUR_POSTIZ_API_KEY_HERE"
    tiktok_integration_id = "cmn4rugfx0e56pb0yn0tyvil3"
    
    caption = """Villa that costs LESS per person than a hotel room! 🏖️

When 22 friends split Villa Lithos in Porto Rafti:
✨ Private sea views & infinity pool
✨ 15 minutes from Athens airport 
✨ Luxury for LESS than a hotel!

Book your Greek paradise now! 🇬🇷

#VillaLithos #PortoRafti #Greece #GroupTravel #LuxuryVilla #Travel2026 #Paradise #VacationRental #AegeanSea #Luxury"""

    # Upload video
    success = upload_video_to_postiz(video_path, caption, api_key, tiktok_integration_id)
    
    if success:
        print("\\n🎉 Villa Lithos video uploaded to TikTok!")
        print("📱 Check: @dvorapa8")
        print("\\n💡 Note: TikTok may process the video before it goes live")
    else:
        print("\\n❌ Upload failed")

if __name__ == "__main__":
    main()