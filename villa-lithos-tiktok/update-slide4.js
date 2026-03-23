#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

const SLIDES_DIR = path.join(__dirname, 'slides');

async function main() {
  const img = await loadImage(path.join(SLIDES_DIR, 'slide-4.png'));
  const W = img.width;
  const H = img.height;
  const canvas = createCanvas(W, H);
  const ctx = canvas.getContext('2d');

  // Draw background image
  ctx.drawImage(img, 0, 0, W, H);

  // Add subtle dark gradient overlay for text readability
  const grad = ctx.createLinearGradient(0, 0, 0, H * 0.6);
  grad.addColorStop(0, 'rgba(0,0,0,0.45)');
  grad.addColorStop(0.5, 'rgba(0,0,0,0.25)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Text config
  const text = "When 22 friends split this villa, the math will blow your mind";
  const maxWidth = W * 0.75;
  const yPos = H * 0.28;

  // Dynamic font sizing - start large and shrink to fit
  let fontSize = 72;
  const minFontSize = 36;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // Word-wrap function
  function wrapText(text, maxW, fSize) {
    ctx.font = `bold ${fSize}px "Arial", "Helvetica", sans-serif`;
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    for (const word of words) {
      const testLine = currentLine ? currentLine + ' ' + word : word;
      if (ctx.measureText(testLine).width > maxW && currentLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = testLine;
      }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
  }

  // Find best font size (max 4 lines)
  let lines;
  while (fontSize >= minFontSize) {
    lines = wrapText(text, maxWidth, fontSize);
    if (lines.length <= 4) break;
    fontSize -= 2;
  }

  const lineHeight = fontSize * 1.35;
  const totalTextHeight = lines.length * lineHeight;
  const startY = yPos - totalTextHeight / 2;

  // Draw text with black outline and white fill
  ctx.font = `bold ${fontSize}px "Arial", "Helvetica", sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  const outlineWidth = Math.max(3, fontSize / 12);

  for (let i = 0; i < lines.length; i++) {
    const x = W / 2;
    const y = startY + i * lineHeight;

    // Black outline
    ctx.strokeStyle = 'rgba(0,0,0,0.9)';
    ctx.lineWidth = outlineWidth;
    ctx.lineJoin = 'round';
    ctx.strokeText(lines[i], x, y);

    // White fill
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(lines[i], x, y);
  }

  // Save
  const outPath = path.join(SLIDES_DIR, 'final-4.png');
  const buf = canvas.toBuffer('image/png');
  fs.writeFileSync(outPath, buf);
  console.log(`Saved: ${outPath} (${W}x${H}, font=${fontSize}px, ${lines.length} lines)`);
}

main().catch(err => { console.error(err); process.exit(1); });
