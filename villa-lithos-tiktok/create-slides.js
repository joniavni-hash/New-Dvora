#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

const SLIDE_W = 1080;
const SLIDE_H = 1920;

const slides = [
  {
    img: 'slides/slide-1.png', // hero - villa exterior
    text: "My friends think I'm rich,\nbut this luxury villa in Greece\ncosts less per person\nthan most hotels"
  },
  {
    img: 'slides/slide-2.png', // pool
    text: "22 people, 9 bedrooms,\nprivate infinity pool,\n15 min from Athens airport"
  },
  {
    img: 'slides/slide-3.png', // wellness/spa
    text: "Private paddle court, sauna,\n5000m² of pure luxury"
  },
  {
    img: 'slides/slide-4.png', // exterior
    text: "€8000 per week\n÷ 22 people\n= €360 per person\nfor THE WHOLE WEEK"
  },
  {
    img: 'slides/slide-5.png', // living/dining
    text: "Meanwhile hotels in Mykonos\ncharge €300+ per NIGHT\nper room"
  },
  {
    img: 'slides/slide-6.png', // exterior pool
    text: "Villa Lithos\nPorto Rafti, Greece\nlink in bio"
  }
];

async function createSlide(slideInfo, index) {
  const canvas = createCanvas(SLIDE_W, SLIDE_H);
  const ctx = canvas.getContext('2d');

  // Load and crop-to-fill the image
  const img = await loadImage(slideInfo.img);
  
  // Calculate crop to fill 1080x1920 (center crop)
  const targetRatio = SLIDE_W / SLIDE_H;
  const imgRatio = img.width / img.height;
  
  let sx, sy, sw, sh;
  if (imgRatio > targetRatio) {
    // Image is wider - crop sides
    sh = img.height;
    sw = img.height * targetRatio;
    sx = (img.width - sw) / 2;
    sy = 0;
  } else {
    // Image is taller - crop top/bottom
    sw = img.width;
    sh = img.width / targetRatio;
    sx = 0;
    sy = (img.height - sh) / 2;
  }
  
  // Draw image filling canvas
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, SLIDE_W, SLIDE_H);
  
  // Add dark gradient overlay - heavier at top where text goes, lighter below to show villa
  const gradient = ctx.createLinearGradient(0, 0, 0, SLIDE_H);
  gradient.addColorStop(0, 'rgba(0,0,0,0.65)');
  gradient.addColorStop(0.30, 'rgba(0,0,0,0.35)');
  gradient.addColorStop(0.45, 'rgba(0,0,0,0.05)');
  gradient.addColorStop(0.75, 'rgba(0,0,0,0.0)');
  gradient.addColorStop(1, 'rgba(0,0,0,0.3)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, SLIDE_W, SLIDE_H);

  // Text overlay
  const lines = slideInfo.text.split('\n');
  const wordCount = slideInfo.text.replace(/\n/g, ' ').split(/\s+/).length;
  
  let fontSize;
  if (wordCount <= 8)       fontSize = 72;
  else if (wordCount <= 15) fontSize = 62;
  else                      fontSize = 52;

  // Special: slide 6 (CTA) gets bigger text
  if (index === 5) fontSize = 78;
  // Slide 4 (math) gets medium
  if (index === 3) fontSize = 68;
  
  const lineHeight = fontSize * 1.35;
  const outlineWidth = Math.round(fontSize * 0.12);

  ctx.font = `bold ${fontSize}px "Arial"`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  const totalH = lines.length * lineHeight;
  // Position text in top third - keeps villa photos visible below
  const startY = (SLIDE_H * 0.18) - (totalH / 2) + (totalH / 2);
  const x = SLIDE_W / 2;

  for (let i = 0; i < lines.length; i++) {
    const y = startY + (i * lineHeight);
    const line = lines[i].trim();

    // Shadow for depth
    ctx.shadowColor = 'rgba(0,0,0,0.8)';
    ctx.shadowBlur = 15;
    ctx.shadowOffsetX = 3;
    ctx.shadowOffsetY = 3;
    
    // Black outline
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = outlineWidth;
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.strokeText(line, x, y);

    // White fill
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(line, x, y);
  }

  // Save
  const outPath = `slides/final-${index + 1}.png`;
  fs.writeFileSync(outPath, canvas.toBuffer('image/png'));
  console.log(`✅ Slide ${index + 1}: ${outPath} (${lines.length} lines, font ${fontSize}px)`);
}

async function main() {
  console.log('🎬 Creating Villa Lithos TikTok Slides...\n');
  
  for (let i = 0; i < slides.length; i++) {
    await createSlide(slides[i], i);
  }
  
  console.log('\n🎉 All 6 TikTok slides created!');
  console.log('📁 Output: slides/final-1.png through final-6.png');
  console.log('📐 Format: 1080x1920 (TikTok portrait)');
}

main().catch(err => { console.error(err); process.exit(1); });
