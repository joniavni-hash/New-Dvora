#!/usr/bin/env node

/**
 * Villa Lithos TikTok Slide Creator v2
 * Improved: stronger gradients, better contrast, refined text positioning
 */

const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

const SLIDES_DIR = path.join(__dirname, 'slides');

const slideData = [
  {
    bg: 'slide-1-bg.jpg',
    lines: [
      { text: "My friends think", highlight: false },
      { text: "I'm rich", highlight: false },
      { text: "", highlight: false },
      { text: "but this luxury villa", highlight: false },
      { text: "in Greece costs less", highlight: true },
      { text: "per person than", highlight: false },
      { text: "most hotels", highlight: true },
    ]
  },
  {
    bg: 'slide-2-bg.jpg',
    lines: [
      { text: "22 people", highlight: false },
      { text: "9 bedrooms", highlight: false },
      { text: "Private infinity pool", highlight: true },
      { text: "", highlight: false },
      { text: "15 min from", highlight: false },
      { text: "Athens airport", highlight: true },
    ]
  },
  {
    bg: 'slide-3-bg.jpg',
    lines: [
      { text: "Private paddle court", highlight: false },
      { text: "Sauna", highlight: false },
      { text: "", highlight: false },
      { text: "5000m² of", highlight: false },
      { text: "pure luxury", highlight: true },
    ]
  },
  {
    bg: 'slide-4-bg.jpg',
    lines: [
      { text: "€8000 per week", highlight: false },
      { text: "÷ 22 people", highlight: false },
      { text: "", highlight: false },
      { text: "= €360 per person", highlight: true },
      { text: "for THE WHOLE WEEK", highlight: true },
    ]
  },
  {
    bg: 'slide-5-bg.jpg',
    lines: [
      { text: "Meanwhile hotels", highlight: false },
      { text: "in Mykonos charge", highlight: false },
      { text: "", highlight: false },
      { text: "€300+ per NIGHT", highlight: true },
      { text: "per room", highlight: true },
    ]
  },
  {
    bg: 'slide-6-bg.jpg',
    lines: [
      { text: "Villa Lithos", highlight: true, size: 'xl' },
      { text: "Porto Rafti, Greece", highlight: false },
      { text: "", highlight: false },
      { text: "LINK IN BIO", highlight: true },
      { text: "↓", highlight: true, size: 'xl' },
    ]
  }
];

async function createSlide(slideInfo, index) {
  const img = await loadImage(path.join(SLIDES_DIR, slideInfo.bg));
  const W = img.width;  // 1080
  const H = img.height; // 1920
  
  const canvas = createCanvas(W, H);
  const ctx = canvas.getContext('2d');
  
  // Draw background image
  ctx.drawImage(img, 0, 0);
  
  // === STRONG GRADIENT OVERLAY ===
  // Full-height dark overlay, strongest at top where text lives
  const fullGrad = ctx.createLinearGradient(0, 0, 0, H);
  fullGrad.addColorStop(0, 'rgba(0,0,0,0.72)');    // Very dark at top
  fullGrad.addColorStop(0.15, 'rgba(0,0,0,0.60)');  // Still dark
  fullGrad.addColorStop(0.40, 'rgba(0,0,0,0.30)');  // Easing off
  fullGrad.addColorStop(0.60, 'rgba(0,0,0,0.10)');  // Mostly clear - show the image
  fullGrad.addColorStop(0.80, 'rgba(0,0,0,0.15)');  // Slight darkening at bottom
  fullGrad.addColorStop(1.0, 'rgba(0,0,0,0.50)');   // Dark at bottom for dots
  ctx.fillStyle = fullGrad;
  ctx.fillRect(0, 0, W, H);
  
  // === TEXT RENDERING ===
  const baseFontSize = 72;
  const lineHeight = baseFontSize * 1.4;
  const centerX = W / 2;
  const startY = H * 0.10; // Higher positioning
  
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  
  for (let i = 0; i < slideInfo.lines.length; i++) {
    const line = slideInfo.lines[i];
    if (!line.text) continue; // Empty line = spacer
    
    const y = startY + (i * lineHeight);
    
    // Font size
    let fontSize = baseFontSize;
    if (line.size === 'xl') fontSize = Math.round(baseFontSize * 1.3);
    if (line.size === 'sm') fontSize = Math.round(baseFontSize * 0.75);
    if (line.highlight && !line.size) fontSize = Math.round(baseFontSize * 1.1);
    
    ctx.font = `900 ${fontSize}px Arial`;
    
    // === Multi-layer text rendering for maximum readability ===
    
    // Layer 1: Dark shadow (depth effect)
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillText(line.text, centerX + 4, y + 4);
    
    // Layer 2: Thick black outline
    const outlineWidth = Math.round(fontSize * 0.10);
    ctx.strokeStyle = 'rgba(0,0,0,0.95)';
    ctx.lineWidth = outlineWidth * 2.5;
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.strokeText(line.text, centerX, y);
    
    // Layer 3: Text fill
    if (line.highlight) {
      // Bright yellow-gold for highlights with extra glow
      ctx.shadowColor = 'rgba(255,200,0,0.3)';
      ctx.shadowBlur = 15;
      ctx.fillStyle = '#FFD700';
      ctx.fillText(line.text, centerX, y);
      ctx.shadowBlur = 0;
    } else {
      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(line.text, centerX, y);
    }
  }
  
  // === SLIDE DOTS ===
  const dotY = H - 70;
  const dotSpacing = 22;
  const totalDotsWidth = 5 * dotSpacing;
  const dotsStartX = centerX - totalDotsWidth / 2;
  
  for (let d = 0; d < 6; d++) {
    const dotX = dotsStartX + d * dotSpacing;
    ctx.beginPath();
    ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
    if (d === index) {
      ctx.fillStyle = '#FFFFFF';
    } else {
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
    }
    ctx.fill();
  }
  
  // === SMALL BRANDING BAR ===
  if (index < 5) { // Not on last slide
    ctx.font = '600 28px Arial';
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.textAlign = 'center';
    ctx.fillText('Villa Lithos | Porto Rafti, Greece', centerX, H - 120);
  }
  
  // Save as PNG
  const outputPath = path.join(SLIDES_DIR, `final-${index + 1}.png`);
  fs.writeFileSync(outputPath, canvas.toBuffer('image/png'));
  console.log(`✅ Slide ${index + 1} saved (${(fs.statSync(outputPath).size / 1024 / 1024).toFixed(1)}MB)`);
  return outputPath;
}

async function main() {
  console.log('🏛️  Villa Lithos TikTok Slides v2\n');
  
  for (let i = 0; i < slideData.length; i++) {
    await createSlide(slideData[i], i);
  }
  
  console.log(`\n🎉 All 6 slides ready!`);
  console.log(`📁 ${SLIDES_DIR}/final-1.png through final-6.png`);
  console.log(`📐 1080x1920 vertical (TikTok native)`);
}

main().catch(console.error);
