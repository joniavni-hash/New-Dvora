#!/usr/bin/env python3
"""
Villa Lithos TikTok Slideshow Creator
Using Larry's approach: Google Drive images → Text overlays → TikTok slideshow
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def download_villa_images(count=5):
    """Download Villa Lithos images from Google Drive"""
    
    # Villa Lithos image IDs (from our previous scan)
    villa_images = [
        "1V9EoVvcodmzTEGsgYgQ5tyeRRjfRAVl6",  # Copy of IMG_0160.jpg (exterior)
        "1E9JHXZ2fW4vs8OqDSoiNEo4O2AHrBOpO",  # Copy of IMG_0139.jpg (dining)
        "1XxTIM7oBxoNHyK5PTwiQ1yNXt-Rl7i0I",  # Copy of IMG_0151.jpg (living)
        "1Y7D9TgH0-OASgMPFGf5Bd43MtTNfZWOJ",  # Copy of IMG_0132-2.jpg (sunset)
        "1IR5m1Vky9j1TePIqaG3TGXEdnfVMJf-G"   # IMG_8363.jpeg (recent)
    ]
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    output_dir = f"villa_slides_{timestamp}"
    Path(output_dir).mkdir(exist_ok=True)
    
    downloaded_images = []
    
    for i, image_id in enumerate(villa_images[:count]):
        try:
            # Download image via gog
            result = subprocess.run([
                'bash', '-c', 
                f'export GOG_KEYRING_PASSWORD="" && gog drive download "{image_id}" --account joni.avni@gmail.com'
            ], capture_output=True, text=True, cwd=output_dir)
            
            if result.returncode == 0:
                # Find downloaded file
                for file in Path(output_dir).glob("*.jpg"):
                    new_name = f"slide-{i+1:02d}.jpg"
                    file.rename(Path(output_dir) / new_name)
                    downloaded_images.append(str(Path(output_dir) / new_name))
                    print(f"✅ Downloaded slide {i+1}: {new_name}")
                    break
            else:
                print(f"❌ Failed to download image {i+1}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error downloading image {i+1}: {e}")
    
    return output_dir, downloaded_images

def add_text_overlays(output_dir, images, hooks):
    """Add text overlays using Node.js canvas (Larry's method)"""
    
    overlay_script = f"""
const {{ createCanvas, loadImage }} = require('canvas');
const fs = require('fs');

async function addOverlay(imagePath, text, outputPath) {{
    try {{
        const image = await loadImage(imagePath);
        const canvas = createCanvas(image.width, image.height);
        const ctx = canvas.getContext('2d');
        
        // Draw original image
        ctx.drawImage(image, 0, 0);
        
        // Add text overlay
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 3;
        ctx.font = 'bold 48px Arial';
        ctx.textAlign = 'center';
        
        // Wrap text
        const lines = wrapText(ctx, text, canvas.width * 0.9);
        const lineHeight = 60;
        const startY = canvas.height * 0.15;
        
        lines.forEach((line, index) => {{
            const y = startY + (index * lineHeight);
            ctx.strokeText(line, canvas.width/2, y);
            ctx.fillText(line, canvas.width/2, y);
        }});
        
        // Save
        const buffer = canvas.toBuffer('image/png');
        fs.writeFileSync(outputPath, buffer);
        console.log(`✅ Added overlay: ${{outputPath}}`);
        
    }} catch (error) {{
        console.error(`❌ Error adding overlay: ${{error.message}}`);
    }}
}}

function wrapText(ctx, text, maxWidth) {{
    const words = text.split(' ');
    const lines = [];
    let currentLine = words[0];
    
    for (let i = 1; i < words.length; i++) {{
        const word = words[i];
        const width = ctx.measureText(currentLine + ' ' + word).width;
        if (width < maxWidth) {{
            currentLine += ' ' + word;
        }} else {{
            lines.push(currentLine);
            currentLine = word;
        }}
    }}
    lines.push(currentLine);
    return lines;
}}

// Process images
const images = {json.dumps(images)};
const hooks = {json.dumps(hooks)};

async function processAll() {{
    for (let i = 0; i < images.length; i++) {{
        const hook = hooks[i % hooks.length];
        const inputPath = images[i];
        const outputPath = inputPath.replace('.jpg', '-final.png');
        
        await addOverlay(inputPath, hook, outputPath);
    }}
}}

processAll().then(() => console.log('🎨 All overlays completed!'));
"""
    
    # Write and run overlay script
    script_path = Path(output_dir) / "add_overlays.js"
    with open(script_path, 'w') as f:
        f.write(overlay_script)
    
    # Install canvas if needed and run script
    try:
        subprocess.run(['npm', 'install', 'canvas'], cwd=output_dir, capture_output=True)
        result = subprocess.run(['node', 'add_overlays.js'], cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Text overlays added successfully!")
            return [str(Path(output_dir) / f) for f in os.listdir(output_dir) if f.endswith('-final.png')]
        else:
            print(f"❌ Overlay error: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"❌ Failed to add overlays: {e}")
        return []

def post_slideshow_to_tiktok(slides, caption, config_path):
    """Post slideshow to TikTok via Postiz (Larry's method)"""
    
    if not slides:
        print("❌ No slides to post")
        return False
    
    try:
        # Use our existing postiz_real.py but adapted for slideshows
        import postiz_real
        
        result = postiz_real.publish_villa_lithos_post(
            content=caption,
            platforms=['tiktok', 'instagram'],
            image_paths=slides
        )
        
        if result['success']:
            print(f"✅ Slideshow posted successfully!")
            print(f"📱 Platforms: {result['platforms']}")
            print(f"🎬 Post ID: {result['post_id']}")
            return True
        else:
            print(f"❌ Failed to post: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting slideshow: {e}")
        return False

def main():
    print("🏖️ Villa Lithos TikTok Slideshow Creator\\n")
    
    # Load config
    config_path = "villa_lithos_tiktok_config.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    hooks = config['app']['hooks']
    
    print("📥 Step 1: Downloading Villa Lithos images...")
    output_dir, images = download_villa_images(count=5)
    
    if not images:
        print("❌ No images downloaded. Check Google Drive connection.")
        return
    
    print(f"\\n🎨 Step 2: Adding text overlays...")
    final_slides = add_text_overlays(output_dir, images, hooks)
    
    if not final_slides:
        print("❌ Failed to create slides with overlays")
        return
    
    print(f"\\n📱 Step 3: Posting to TikTok...")
    caption = f"""Villa that costs LESS per person than a hotel room! 🏖️

When 22 friends split Villa Lithos in Porto Rafti, you get:
✨ Private sea views 
✨ Infinity pool
✨ 15 min from Athens airport
✨ Luxury for less than a hotel!

#VillaLithos #PortoRafti #Greece #GroupTravel #LuxuryVilla #Travel2026"""
    
    success = post_slideshow_to_tiktok(final_slides, caption, config_path)
    
    if success:
        print(f"\\n🎉 Villa Lithos slideshow created and posted!")
        print(f"📁 Files saved in: {output_dir}")
        print(f"🎬 Slides: {len(final_slides)}")
        print("\\n⚠️  Remember: Go to TikTok and add trending music before publishing!")
    else:
        print("\\n❌ Slideshow creation failed")

if __name__ == "__main__":
    main()