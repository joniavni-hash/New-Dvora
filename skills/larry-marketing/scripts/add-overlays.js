#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - Text Overlay Generator
 * Adds text overlays to slideshow images using node-canvas
 * This is the exact code that Larry uses for viral TikTok slides
 */

const fs = require('fs');
const path = require('path');

// Check if canvas is installed
let Canvas;
try {
  Canvas = require('canvas');
} catch (error) {
  console.error('❌ node-canvas not installed!');
  console.error('Install it with: npm install canvas');
  console.error('You may need system dependencies first:');
  console.error('  macOS: brew install pkg-config cairo pango libpng jpeg giflib librsvg');
  console.error('  Ubuntu: sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev');
  process.exit(1);
}

const { createCanvas, loadImage } = Canvas;

async function addOverlay(imagePath, text, outputPath) {
  const img = await loadImage(imagePath);
  const canvas = createCanvas(img.width, img.height);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);

  // ─── Adjust font size based on text length ───
  const wordCount = text.split(/\s+/).length;
  let fontSizePercent;
  if (wordCount <= 5)       fontSizePercent = 0.075;  // Short: 75px on 1024w
  else if (wordCount <= 12) fontSizePercent = 0.065;  // Medium: 66px
  else                      fontSizePercent = 0.050;  // Long: 51px

  const fontSize = Math.round(img.width * fontSizePercent);
  const outlineWidth = Math.round(fontSize * 0.15);
  const maxWidth = img.width * 0.75;
  const lineHeight = fontSize * 1.3;

  ctx.font = `bold ${fontSize}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // ─── Word wrap ───
  const lines = [];
  const manualLines = text.split('\\n');
  for (const ml of manualLines) {
    const words = ml.trim().split(/\s+/);
    let current = '';
    for (const word of words) {
      const test = current ? `${current} ${word}` : word;
      if (ctx.measureText(test).width <= maxWidth) {
        current = test;
      } else {
        if (current) lines.push(current);
        current = word;
      }
    }
    if (current) lines.push(current);
  }

  // ─── Position: centered at ~28% from top ───
  const totalHeight = lines.length * lineHeight;
  const startY = (img.height * 0.28) - (totalHeight / 2);
  const x = img.width / 2;

  // ─── Draw each line ───
  for (let i = 0; i < lines.length; i++) {
    const y = startY + (i * lineHeight);

    // Black outline
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = outlineWidth;
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.strokeText(lines[i], x, y);

    // White fill
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(lines[i], x, y);
  }

  fs.writeFileSync(outputPath, canvas.toBuffer('image/png'));
}

async function main() {
  const args = process.argv.slice(2);
  const dir = args.find(arg => arg.startsWith('--dir='))?.split('=')[1];
  const textsPath = args.find(arg => arg.startsWith('--texts='))?.split('=')[1] || 'texts.json';

  if (!dir) {
    console.error('❌ --dir parameter required');
    console.error('Usage: node scripts/add-overlays.js --dir=tiktok-marketing/posts/YYYY-MM-DD-HHmm/');
    process.exit(1);
  }

  console.log('📝 Larry\'s Marketing Experiments - Text Overlay Generator\n');

  // Load text overlays
  let texts;
  try {
    texts = JSON.parse(fs.readFileSync(textsPath, 'utf8'));
  } catch (error) {
    console.error(`❌ Texts file not found: ${textsPath}`);
    console.error('Create texts.json with an array of overlay texts for each slide');
    process.exit(1);
  }

  if (!Array.isArray(texts)) {
    console.error('❌ texts.json must be an array of strings');
    process.exit(1);
  }

  // Find slide images
  const slideFiles = fs.readdirSync(dir)
    .filter(file => file.startsWith('slide-') && file.endsWith('.png'))
    .sort((a, b) => {
      const numA = parseInt(a.match(/slide-(\d+)/)[1]);
      const numB = parseInt(b.match(/slide-(\d+)/)[1]);
      return numA - numB;
    });

  if (slideFiles.length === 0) {
    console.error(`❌ No slide images found in ${dir}`);
    console.error('Generate slides first with: node scripts/generate-slides.js');
    process.exit(1);
  }

  if (texts.length !== slideFiles.length) {
    console.error(`❌ Mismatch: ${texts.length} texts vs ${slideFiles.length} slides`);
    console.error('Each slide needs corresponding text in texts.json');
    process.exit(1);
  }

  console.log(`📝 Adding text overlays to ${slideFiles.length} slides...\n`);

  for (let i = 0; i < slideFiles.length; i++) {
    const inputPath = path.join(dir, slideFiles[i]);
    const outputPath = path.join(dir, `final-${i + 1}.png`);
    
    // Skip if already exists
    if (fs.existsSync(outputPath)) {
      console.log(`⏩ Slide ${i + 1} overlay already exists, skipping...`);
      continue;
    }

    console.log(`📝 Adding text to slide ${i + 1}/${slideFiles.length}:`);
    console.log(`   Text: "${texts[i]}"`);
    console.log(`   Input: ${inputPath}`);
    console.log(`   Output: ${outputPath}`);

    try {
      await addOverlay(inputPath, texts[i], outputPath);
      console.log(`✅ Slide ${i + 1} overlay complete\n`);
    } catch (error) {
      console.error(`❌ Error processing slide ${i + 1}: ${error.message}`);
      process.exit(1);
    }
  }

  console.log(`🎉 All text overlays added successfully!`);
  console.log(`📁 Final slides in: ${dir}`);
  console.log(`\n📋 Next step:`);
  console.log(`Post to TikTok: node scripts/post-to-tiktok.js --dir ${dir}`);
}

if (require.main === module) {
  main();
}