#!/usr/bin/env python3
"""
Villa Lithos TikTok Video Creator - Full Automation
Creates video from slides + uploads directly to TikTok with music
"""

import os
import json
import subprocess
from pathlib import Path
from tiktok_uploader.upload import upload_video
from tiktok_uploader.auth import AuthBackend

def create_video_from_slides(slides_dir, output_video_path):
    """Convert slideshow images to video using ffmpeg"""
    
    slides_pattern = f"{slides_dir}/final-%02d.png"
    
    # Create video from slides (3 seconds per slide, with fade transitions)
    ffmpeg_cmd = [
        'ffmpeg', '-y',  # -y to overwrite output file
        '-framerate', '1/3',  # 3 seconds per image 
        '-i', slides_pattern,  # input pattern
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30',  # TikTok format
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-t', '15',  # 15 seconds total (5 slides × 3 seconds)
        output_video_path
    ]
    
    print(f"🎬 Creating video: {output_video_path}")
    
    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Video created successfully!")
            return True
        else:
            print(f"❌ ffmpeg error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Video creation timeout")
        return False
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return False

def upload_to_tiktok_direct(video_path, description, cookies_path=None):
    """Upload video directly to TikTok using tiktok-uploader"""
    
    if not cookies_path or not Path(cookies_path).exists():
        print("❌ TikTok cookies required for upload")
        print("💡 To get cookies:")
        print("1. Install 'Get cookies.txt' Chrome extension")
        print("2. Login to TikTok in browser")
        print("3. Use extension to save cookies.txt")
        print("4. Place cookies.txt in integrations/social/")
        return False
    
    try:
        print("🚀 Uploading to TikTok...")
        
        # Create auth backend with cookies
        auth = AuthBackend(cookies=cookies_path)
        
        # Upload video
        result = upload_video(
            path=video_path,
            description=description,
            cookies=cookies_path,
            # TikTok-specific options
            comment=True,  # Allow comments
            stitch=True,   # Allow stitch
            duet=True,     # Allow duet
        )
        
        if result:
            print("✅ Video uploaded to TikTok successfully!")
            return True
        else:
            print("❌ Upload failed")
            return False
            
    except Exception as e:
        print(f"❌ TikTok upload error: {e}")
        return False

def main():
    print("🎬 Villa Lithos TikTok Video Creator\\n")
    
    slides_dir = "villa_slides_test"
    video_path = "villa_slides_test/villa_lithos_tiktok.mp4"
    cookies_path = "integrations/social/cookies.txt"
    
    # Check if slides exist
    slides = list(Path(slides_dir).glob("final-*.png"))
    if len(slides) < 5:
        print("❌ Need 5 slides. Create slides first:")
        print("cd villa_slides_test && node add_overlay.js")
        return
    
    print(f"📸 Found {len(slides)} slides")
    
    # Step 1: Create video from slides
    if not create_video_from_slides(slides_dir, video_path):
        print("❌ Failed to create video")
        return
    
    # Check video was created
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return
    
    video_size = Path(video_path).stat().st_size / (1024*1024)  # MB
    print(f"📹 Video created: {video_size:.1f} MB")
    
    # Step 2: Upload to TikTok
    description = """Villa that costs LESS per person than a hotel room! 🏖️

When 22 friends split Villa Lithos in Porto Rafti:
✨ Private sea views & infinity pool
✨ 15 minutes from Athens airport 
✨ Luxury for LESS than a hotel!

Book your Greek paradise now! 🇬🇷

#VillaLithos #PortoRafti #Greece #GroupTravel #LuxuryVilla #Travel2026 #Paradise #VacationRental #AegeanSea"""

    success = upload_to_tiktok_direct(video_path, description, cookies_path)
    
    if success:
        print("\\n🎉 Villa Lithos video uploaded to TikTok!")
        print("🎵 TikTok will automatically suggest trending music")
        print("📱 Check your TikTok account: @dvorapa8")
    else:
        print("\\n❌ Upload failed. Check cookies and try again.")
    
    # Cleanup
    if Path(video_path).exists() and success:
        print(f"📹 Video saved: {video_path}")

if __name__ == "__main__":
    main()