#!/usr/bin/env python3
"""
Villa Lithos TikTok Browser Automation
Direct browser automation to upload slideshow to TikTok with music
"""

import os
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests

def setup_chrome_driver(headless=False):
    """Setup Chrome driver with proper options for TikTok"""
    
    chrome_options = Options()
    
    # Essential options for TikTok
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent to avoid detection
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    if headless:
        chrome_options.add_argument('--headless')
    
    try:
        # Auto-download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ Failed to setup Chrome driver: {e}")
        return None

def create_simple_video_from_slides(slides_dir, output_path):
    """Create a simple video using Python (without ffmpeg)"""
    
    try:
        from PIL import Image
        import imageio
        import numpy as np
        
        slides = sorted(Path(slides_dir).glob("final-*.png"))
        if len(slides) == 0:
            print("❌ No slides found")
            return False
        
        print(f"📸 Creating video from {len(slides)} slides...")
        
        # Read and resize images
        frames = []
        for slide_path in slides:
            img = Image.open(slide_path)
            
            # Resize to TikTok format (1080x1920)
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            img_array = np.array(img)
            
            # Add each slide for 3 seconds at 10fps = 30 frames
            for _ in range(30):
                frames.append(img_array)
        
        # Save as MP4
        imageio.mimsave(output_path, frames, fps=10, codec='libx264')
        
        print(f"✅ Video created: {output_path}")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install Pillow imageio imageio-ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        return False

def upload_to_tiktok_browser(video_path, description):
    """Upload video to TikTok using browser automation"""
    
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return False
    
    driver = setup_chrome_driver(headless=False)
    if not driver:
        return False
    
    try:
        print("🌐 Opening TikTok...")
        driver.get("https://www.tiktok.com/upload")
        
        # Wait for page to load
        time.sleep(5)
        
        # Check if login required
        if "login" in driver.current_url.lower():
            print("🔐 Login required!")
            print("💡 Manual steps needed:")
            print("1. Login to TikTok in the browser that just opened")
            print("2. Navigate back to https://www.tiktok.com/upload")
            print("3. Press Enter here to continue...")
            input("Press Enter after logging in...")
        
        # Find file upload input
        try:
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload video
            print(f"📤 Uploading video: {video_path}")
            file_input.send_keys(str(Path(video_path).absolute()))
            
            # Wait for upload to process
            time.sleep(10)
            
            # Add description
            try:
                description_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='editor-text-input'], .public-DraftEditor-content, [contenteditable='true']"))
                )
                description_box.click()
                description_box.clear()
                description_box.send_keys(description)
                print("✅ Description added")
            except:
                print("⚠️ Could not add description automatically")
            
            # Try to find and click music/sound button
            try:
                music_buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid='sound-selector'], .sound-selector, [aria-label*='Sound'], button[aria-label*='music']")
                if music_buttons:
                    music_buttons[0].click()
                    time.sleep(3)
                    print("🎵 Music selector opened")
                    
                    # Try to select trending music
                    trending = driver.find_elements(By.CSS_SELECTOR, ".trending-music, [data-testid='trending-sound'], .recommended-sound")
                    if trending:
                        trending[0].click()
                        time.sleep(2)
                        print("✅ Trending music selected")
                else:
                    print("⚠️ Could not find music selector")
            except:
                print("⚠️ Could not add music automatically")
            
            print("\\n📱 Video ready for manual publishing!")
            print("💡 Complete these steps manually:")
            print("1. Select trending music (if not done)")
            print("2. Adjust privacy settings")
            print("3. Click 'Post' button")
            print("\\n🔗 Account: @dvorapa8")
            
            # Keep browser open for manual completion
            print("\\nBrowser will stay open for manual completion...")
            print("Close browser when done.")
            
            # Wait for user to complete
            input("Press Enter when you've published the video...")
            
            return True
            
        except Exception as e:
            print(f"❌ Upload process error: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Browser automation error: {e}")
        return False
    finally:
        # Don't close browser automatically
        print("🌐 Browser session active...")

def main():
    print("🎬 Villa Lithos TikTok Browser Uploader\\n")
    
    slides_dir = "villa_slides_test"
    video_path = "villa_slides_test/villa_tiktok_video.mp4"
    
    # Check if slides exist
    slides = list(Path(slides_dir).glob("final-*.png"))
    if len(slides) < 5:
        print("❌ Need slides first. Run:")
        print("cd villa_slides_test && node add_overlay.js")
        return
    
    print(f"📸 Found {len(slides)} slides")
    
    # Step 1: Create video
    if not Path(video_path).exists():
        if not create_simple_video_from_slides(slides_dir, video_path):
            print("❌ Failed to create video")
            return
    
    # Step 2: Upload via browser
    description = """Villa that costs LESS per person than a hotel room! 🏖️

22 friends split Villa Lithos in Porto Rafti:
✨ Private sea views & infinity pool  
✨ 15 min from Athens airport
✨ Luxury for LESS than a hotel!

Book your Greek paradise! 🇬🇷

#VillaLithos #PortoRafti #Greece #GroupTravel #LuxuryVilla #Travel2026"""

    success = upload_to_tiktok_browser(video_path, description)
    
    if success:
        print("\\n🎉 Upload process initiated!")
        print("📱 Check TikTok: @dvorapa8")
    else:
        print("\\n❌ Upload failed")

if __name__ == "__main__":
    main()