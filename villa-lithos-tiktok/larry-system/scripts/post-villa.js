#!/usr/bin/env node

/**
 * Villa Lithos — Integrated Poster (Larry's System)
 * Posts carousel slides via Postiz API, tracks hook performance, 
 * and updates the learning loop.
 * 
 * Usage:
 *   node post-villa.js --slides=../slides/ --hook-id=hook-001 --caption="..." --platform=tiktok
 *   node post-villa.js --slides=../slides/ --hook-id=hook-001 --dry-run
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '../config/villa-lithos.json');
const HOOKS_PATH = path.join(__dirname, '../hooks/hook-performance.json');

function loadJSON(filePath) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf8')); }
  catch (e) { console.error(`❌ Cannot load ${filePath}: ${e.message}`); process.exit(1); }
}

function saveJSON(filePath, data) {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

async function postToPostiz(config, slideImages, caption, platforms) {
  const integrationIds = [];
  for (const platform of platforms) {
    const id = config.postiz.integrationIds[platform];
    if (id && id !== `${platform.toUpperCase()}_INTEGRATION_ID`) {
      integrationIds.push(id);
    }
  }

  if (integrationIds.length === 0) {
    console.log('⚠️  No valid Postiz integration IDs configured.');
    console.log('📋 To configure, update config/villa-lithos.json → postiz.integrationIds');
    return { id: `dry-run-${Date.now()}`, status: 'dry-run' };
  }

  const postData = JSON.stringify({
    caption,
    integrations: integrationIds,
    media: slideImages.map(img => ({
      path: img,
      type: 'image/png'
    }))
  });

  return new Promise((resolve, reject) => {
    const options = {
      hostname: new URL(config.postiz.baseUrl).hostname,
      port: 443,
      path: '/public/v1/posts',
      method: 'POST',
      headers: {
        'Authorization': config.postiz.apiKey,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(response);
          } else {
            reject(new Error(`Postiz API error (${res.statusCode}): ${data}`));
          }
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function main() {
  const args = process.argv.slice(2);
  const slidesDir = args.find(a => a.startsWith('--slides='))?.split('=')[1];
  const hookId = args.find(a => a.startsWith('--hook-id='))?.split('=')[1];
  const caption = args.find(a => a.startsWith('--caption='))?.split('=')[1];
  const platform = args.find(a => a.startsWith('--platform='))?.split('=')[1] || 'tiktok';
  const dryRun = args.includes('--dry-run');

  if (!slidesDir) {
    console.error('Usage: node post-villa.js --slides=<dir> --hook-id=<id> --caption="..." [--platform=tiktok] [--dry-run]');
    process.exit(1);
  }

  console.log('🏛️  Villa Lithos — Larry\'s Integrated Poster\n');

  const config = loadJSON(CONFIG_PATH);
  const hooks = loadJSON(HOOKS_PATH);

  // Find final slides
  const finalSlides = fs.readdirSync(slidesDir)
    .filter(f => f.startsWith('final-') && f.endsWith('.png'))
    .sort((a, b) => parseInt(a.match(/final-(\d+)/)[1]) - parseInt(b.match(/final-(\d+)/)[1]))
    .map(f => path.join(slidesDir, f));

  if (finalSlides.length === 0) {
    console.error(`❌ No final-*.png slides in ${slidesDir}`);
    process.exit(1);
  }

  console.log(`📸 Found ${finalSlides.length} slides`);
  console.log(`🎣 Hook ID: ${hookId || 'none'}`);
  console.log(`📱 Platform: ${platform}`);
  console.log(`${dryRun ? '🧪 DRY RUN MODE\n' : ''}`);

  const platforms = platform === 'all' ? ['tiktok', 'instagram', 'youtube'] : [platform];

  if (dryRun) {
    console.log('✅ Dry run complete. Would post:');
    console.log(`   Slides: ${finalSlides.map(f => path.basename(f)).join(', ')}`);
    console.log(`   Platforms: ${platforms.join(', ')}`);
    console.log(`   Caption: ${(caption || '').slice(0, 100)}...`);
  } else {
    try {
      const response = await postToPostiz(config, finalSlides, caption || '', platforms);
      console.log(`✅ Posted! ID: ${response.id || 'N/A'}`);
      console.log('⚠️  Posts upload as DRAFTS — add trending audio before publishing!');

      // Update hook tracking
      if (hookId) {
        const hook = hooks.hooks.find(h => h.id === hookId) || 
                     hooks.hookQueue.find(h => h.id === hookId);
        if (hook) {
          hook.postId = response.id;
          hook.status = 'posted';
          hook.date = new Date().toISOString().slice(0, 10);
          hook.platform = platform;
          hook.postingTime = new Date().toISOString();
          
          // Move from queue to active if needed
          const queueIdx = hooks.hookQueue.findIndex(h => h.id === hookId);
          if (queueIdx !== -1) {
            const moved = hooks.hookQueue.splice(queueIdx, 1)[0];
            hooks.hooks.push({ ...moved, postId: response.id, status: 'posted', 
              date: new Date().toISOString().slice(0,10), views: null, likes: null,
              comments: null, shares: null, engagementRate: null });
          }
          
          hooks.lastUpdated = new Date().toISOString().slice(0, 10);
          saveJSON(HOOKS_PATH, hooks);
          console.log(`📊 Hook ${hookId} tracking updated`);
        }
      }
    } catch (e) {
      console.error(`❌ Error: ${e.message}`);
      process.exit(1);
    }
  }

  console.log('\n📋 Next steps:');
  console.log('   1. Add trending audio in TikTok drafts');
  console.log('   2. Publish manually');
  console.log('   3. Wait 2+ hours, then: node check-villa-analytics.js --connect');
  console.log('   4. Tomorrow morning: node villa-daily-report.js');
}

if (require.main === module) { main(); }
