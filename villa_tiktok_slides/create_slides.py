#!/usr/bin/env python3
"""Create TikTok-ready slideshow images for Villa Lithos"""

from PIL import Image, ImageDraw, ImageFont
import os

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'photos')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'final')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# TikTok dimensions (9:16)
WIDTH = 1080
HEIGHT = 1920

# Slide definitions: (photo_file, text_lines, text_position)
SLIDES = [
    {
        'photo': 'exterior.jpg',
        'lines': [
            'My friends think',
            "I'm rich...",
            '',
            'But this luxury villa',
            'costs LESS per person',
            'than most hotels 🏛️'
        ],
        'position': 'top'
    },
    {
        'photo': 'pool.jpg',
        'lines': [
            '22 guests',
            '9 bedrooms',
            'Private infinity pool',
            '15 min from Athens airport ✈️'
        ],
        'position': 'top'
    },
    {
        'photo': 'aerial.jpg',
        'lines': [
            'Private padel court 🎾',
            'Finnish barrel sauna 🧖',
            'Heated infinity pool 🏊',
            'Jacuzzi • Gym • Spa',
            '5,000m² private estate'
        ],
        'position': 'top'
    },
    {
        'photo': 'bathtub.jpg',
        'lines': [
            '€8,000 per week',
            '÷ 22 people',
            '= €52 per person/night',
            '',
            'That\'s LESS than a hostel 🤯'
        ],
        'position': 'center'
    },
    {
        'photo': 'fireplace.jpg',
        'lines': [
            'Hotels in Mykonos:',
            '€300+ per night per room',
            '',
            'Villa Lithos:',
            '€52/night with YOUR',
            'own infinity pool 💎'
        ],
        'position': 'top'
    },
    {
        'photo': 'hero.webp',
        'lines': [
            'Villa Lithos',
            'Porto Rafti, Greece',
            '',
            '🔗 Link in bio',
            '📩 DM for availability'
        ],
        'position': 'center'
    }
]


def load_font(size):
    """Try to load a bold font, fall back to default"""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def create_slide(slide_def, index):
    """Create a single TikTok slide"""
    photo_path = os.path.join(PHOTOS_DIR, slide_def['photo'])
    
    if not os.path.exists(photo_path):
        print(f"  ⚠️  Photo not found: {photo_path}")
        return None
    
    # Open and resize photo to fill 9:16
    img = Image.open(photo_path)
    
    # Calculate crop to fill 9:16
    target_ratio = WIDTH / HEIGHT  # 0.5625
    img_ratio = img.width / img.height
    
    if img_ratio > target_ratio:
        # Image is wider, crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller, crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))
    
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    
    # Add dark overlay for text readability
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    if slide_def['position'] == 'top':
        # Gradient from top
        for y in range(0, HEIGHT // 2):
            alpha = int(180 * (1 - y / (HEIGHT // 2)))
            draw.rectangle([(0, y), (WIDTH, y + 1)], fill=(0, 0, 0, alpha))
    elif slide_def['position'] == 'center':
        # Full semi-transparent overlay
        draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(0, 0, 0, 100))
    
    # Composite overlay
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    
    # Add text
    draw = ImageDraw.Draw(img)
    font_large = load_font(56)
    font_small = load_font(44)
    
    lines = slide_def['lines']
    line_height = 72
    total_height = len(lines) * line_height
    
    if slide_def['position'] == 'top':
        y_start = 200
    elif slide_def['position'] == 'center':
        y_start = (HEIGHT - total_height) // 2
    else:
        y_start = HEIGHT - total_height - 200
    
    for i, line in enumerate(lines):
        if not line:
            continue
        
        font = font_large if i == 0 or (index == 0 and i < 2) else font_small
        
        # Get text size
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        y = y_start + i * line_height
        
        # Draw text shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0, 200), font=font)
        # Draw main text
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
    
    # Convert back to RGB for saving
    img = img.convert('RGB')
    
    output_path = os.path.join(OUTPUT_DIR, f'slide-{index + 1}.jpg')
    img.save(output_path, 'JPEG', quality=95)
    print(f"  ✅ Slide {index + 1}: {output_path}")
    return output_path


def main():
    print("🎬 Creating Villa Lithos TikTok Slides\n")
    
    slides = []
    for i, slide_def in enumerate(SLIDES):
        result = create_slide(slide_def, i)
        if result:
            slides.append(result)
    
    print(f"\n📱 Created {len(slides)}/{len(SLIDES)} slides")
    print(f"📁 Output: {OUTPUT_DIR}/")
    
    if slides:
        print("\n📋 Caption for TikTok:")
        caption = """My friends think I'm rich but this luxury villa in Greece costs less per person than most hotels 🏛️✨

22 guests • 9 bedrooms • infinity pool • padel court • sauna
Only €52/person per night!

📍 Villa Lithos, Porto Rafti - 15 min from Athens Airport

#luxuryvilla #greecevilla #travelgreece #villagoals #airbnbfinds #grouptravel #europetravel #luxurytravel #splitcost #budgetluxury #travelhack #smarttravel #squadgoals #friendtrip #portorafti #athensgreece #greeksummer #visitgreece"""
        print(caption)
        
        # Save caption
        with open(os.path.join(OUTPUT_DIR, 'caption.txt'), 'w') as f:
            f.write(caption)


if __name__ == '__main__':
    main()
