#!/usr/bin/env node

/**
 * Villa Lithos — Slide Generator (Larry's System)
 * Unlike app marketing (AI-generated images), Villa Lithos uses REAL photos.
 * This script downloads villa photos from the photo bank and applies text overlays.
 * 
 * Usage:
 *   node generate-villa-slides.js --hook-id=hook-002 --output=../posts/2026-03-24/
 *   node generate-villa-slides.js --hook-id=hook-003 --photos=custom-order.json --output=../posts/test/
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '../config/villa-lithos.json');
const HOOKS_PATH = path.join(__dirname, '../hooks/hook-performance.json');
const VARIATIONS_PATH = path.join(__dirname, '../../../workspace/villa-lithos/hook-variations-slides.json');

function loadJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { return null; }
}

// Photo selection per hook category - which villa photos best match each slide
const PHOTO_MAPS = {
  'cost-split': ['exterior', 'infinity-pool', 'paddle-court', 'living-room', 'sauna', 'paradise-view'],
  'math-challenge': ['exterior', 'paradise-view', 'living-room', 'outdoor-kitchen', 'sauna', 'aerial'],
  'pov': ['exterior', 'infinity-pool', 'paddle-court', 'bath-view', 'sauna-path', 'paradise-view-2'],
  'conspiracy': ['infinity-pool', 'paradise-view', 'paddle-court', 'outdoor-kitchen', 'sauna', 'exterior'],
  'airport-proximity': ['aerial', 'infinity-pool', 'living-room', 'paddle-court', 'paradise-view', 'exterior'],
  'amenity-tour': ['infinity-pool', 'paddle-court', 'sauna', 'outdoor-kitchen', 'bath-view', 'exterior'],
  'vs-hotel': ['infinity-pool', 'living-room', 'paddle-court', 'bath-view', 'sauna', 'exterior'],
  'corporate': ['living-room', 'outdoor-kitchen', 'infinity-pool', 'paddle-court', 'aerial', 'exterior'],
  'fomo-urgency': ['paradise-view', 'infinity-pool', 'paddle-court', 'sauna', 'outdoor-kitchen', 'exterior'],
  'bachelorette': ['infinity-pool', 'paradise-view', 'bath-view', 'outdoor-kitchen', 'sauna-path', 'exterior'],
  'default': ['exterior', 'infinity-pool', 'paddle-court', 'living-room', 'sauna', 'paradise-view']
};

function getSlideTexts(hookId, hooks) {
  // Check if hook has full slide set in variations file
  const variations = loadJSON(VARIATIONS_PATH);
  
  // Check the hook queue for slide text
  const hook = hooks.hooks.find(h => h.id === hookId) || hooks.hookQueue.find(h => h.id === hookId);
  if (!hook) return null;

  // Map variation IDs to their slide sets
  if (variations) {
    const variationMap = {
      'hook-002': 'variation_a_math_challenge',
      'hook-003': 'variation_b_pov',
      'hook-004': 'variation_c_conspiracy'
    };
    const varKey = variationMap[hookId];
    if (varKey && variations[varKey]) {
      return variations[varKey].slides.map(s => s.text.replace(/[🤔✓🇬🇷📌🤫🔥]/g, '').trim());
    }
  }

  // Fallback: return hook text as slide 1, rest need manual creation
  return null;
}

async function downloadPhoto(url, outputPath) {
  return new Promise((resolve, reject) => {
    const get = (u) => {
      https.get(u, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          get(res.headers.location);
          return;
        }
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode} downloading ${u}`));
          return;
        }
        const file = fs.createWriteStream(outputPath);
        res.pipe(file);
        file.on('finish', () => { file.close(); resolve(outputPath); });
        file.on('error', (e) => { fs.unlink(outputPath, () => {}); reject(e); });
      }).on('error', reject);
    };
    get(url);
  });
}

async function main() {
  const args = process.argv.slice(2);
  const hookId = args.find(a => a.startsWith('--hook-id='))?.split('=')[1];
  const outputDir = args.find(a => a.startsWith('--output='))?.split('=')[1];
  const listHooks = args.includes('--list');

  const config = loadJSON(CONFIG_PATH);
  const hooks = loadJSON(HOOKS_PATH);

  if (listHooks || !hookId) {
    console.log('🏛️  Villa Lithos — Available Hooks for Slide Generation\n');
    console.log('Ready hooks with slide texts:');
    for (const h of [...(hooks?.hooks || []), ...(hooks?.hookQueue || [])]) {
      const hasSlides = getSlideTexts(h.id, hooks) ? '✅' : '📝 needs slides';
      console.log(`  ${h.id} [${h.category}] ${hasSlides} — "${(h.text || '').slice(0, 60)}"`);
    }
    console.log('\nUsage: node generate-villa-slides.js --hook-id=hook-002 --output=../posts/2026-03-24/');
    return;
  }

  if (!outputDir) {
    console.error('❌ --output required');
    process.exit(1);
  }

  const hook = hooks.hooks.find(h => h.id === hookId) || hooks.hookQueue.find(h => h.id === hookId);
  if (!hook) {
    console.error(`❌ Hook ${hookId} not found`);
    process.exit(1);
  }

  const slideTexts = getSlideTexts(hookId, hooks);
  if (!slideTexts) {
    console.error(`❌ No slide texts defined for ${hookId}. Create them first.`);
    process.exit(1);
  }

  const photoMap = PHOTO_MAPS[hook.category] || PHOTO_MAPS['default'];
  
  console.log(`🏛️  Villa Lithos — Generating slides for ${hookId} (${hook.category})\n`);
  console.log(`📸 Photos: ${photoMap.join(', ')}`);
  console.log(`📝 Slides: ${slideTexts.length}`);
  console.log(`📁 Output: ${outputDir}\n`);

  // Create output dir
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  // Save texts for overlay script
  const textsPath = path.join(outputDir, 'texts.json');
  fs.writeFileSync(textsPath, JSON.stringify(slideTexts, null, 2));
  console.log(`📝 Saved slide texts to ${textsPath}`);

  // Map photo IDs to URLs from config
  const villaConfig = loadJSON(path.join(__dirname, '../../../workspace/villa-lithos/config.json'));
  if (villaConfig?.photos) {
    console.log('\n📸 Villa photos available from Facebook album.');
    console.log('Use existing slides from villa-lithos-tiktok/slides/ or download fresh.');
  }

  console.log('\n📋 Next steps:');
  console.log(`   1. Place/download 6 slide background images in ${outputDir} as slide-1.png through slide-6.png`);
  console.log(`   2. Run overlay: node ../../skills/larry-marketing/scripts/add-overlays.js --dir=${outputDir} --texts=${textsPath}`);
  console.log(`   3. Post: node post-villa.js --slides=${outputDir} --hook-id=${hookId} --caption="..."`);
}

if (require.main === module) { main(); }
