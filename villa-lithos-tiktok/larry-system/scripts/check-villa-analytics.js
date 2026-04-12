#!/usr/bin/env node

/**
 * Villa Lithos — Analytics Checker (Larry's System)
 * Fetches Postiz analytics, connects posts to TikTok video IDs,
 * and updates hook-performance.json with real data.
 * 
 * Usage:
 *   node check-villa-analytics.js --connect          # Connect & fetch analytics
 *   node check-villa-analytics.js --status            # Quick status of all tracked hooks
 *   node check-villa-analytics.js --hook-id=hook-001  # Check specific hook
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG_PATH = path.join(__dirname, '../config/villa-lithos.json');
const HOOKS_PATH = path.join(__dirname, '../hooks/hook-performance.json');

function loadJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { console.error(`❌ ${p}: ${e.message}`); process.exit(1); }
}
function saveJSON(p, d) { fs.writeFileSync(p, JSON.stringify(d, null, 2)); }

function apiRequest(config, method, apiPath) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: new URL(config.postiz.baseUrl).hostname,
      port: 443,
      path: apiPath,
      method,
      headers: { 'Authorization': config.postiz.apiKey }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const r = JSON.parse(data);
          res.statusCode === 200 ? resolve(r) : reject(new Error(`API ${res.statusCode}: ${data}`));
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

function classifyPerformance(views, thresholds) {
  if (views >= thresholds.viral) return { tier: 'VIRAL', emoji: '🚀', action: 'DOUBLE DOWN — make 3 variations NOW' };
  if (views >= thresholds.strong) return { tier: 'STRONG', emoji: '🟢', action: 'Scale — increase posting frequency with this hook' };
  if (views >= thresholds.good) return { tier: 'GOOD', emoji: '🟡', action: 'Keep in rotation, test 1-2 variations' };
  if (views >= thresholds.decent) return { tier: 'DECENT', emoji: '🟠', action: 'Test 1 more variation, then decide' };
  return { tier: 'POOR', emoji: '🔴', action: 'Drop this hook category after 2 failures' };
}

async function main() {
  const args = process.argv.slice(2);
  const connect = args.includes('--connect');
  const status = args.includes('--status');
  const hookId = args.find(a => a.startsWith('--hook-id='))?.split('=')[1];
  const days = parseInt(args.find(a => a.startsWith('--days='))?.split('=')[1] || '3');

  console.log('📊 Villa Lithos — Analytics Checker (Larry\'s System)\n');

  const config = loadJSON(CONFIG_PATH);
  const hooks = loadJSON(HOOKS_PATH);

  if (status || (!connect && !hookId)) {
    // Show status of all tracked hooks
    console.log('📋 Hook Performance Status:\n');
    console.log('ID          | Category        | Views    | ER%    | Status    | Action');
    console.log('------------|-----------------|----------|--------|-----------|-------');
    
    for (const hook of hooks.hooks) {
      const views = hook.views ?? '—';
      const er = hook.engagementRate ? `${hook.engagementRate}%` : '—';
      const perf = hook.views ? classifyPerformance(hook.views, config.analytics.viewThresholds) : { emoji: '⏳' };
      console.log(`${hook.id.padEnd(12)}| ${(hook.category||'').padEnd(16)}| ${String(views).padEnd(9)}| ${er.padEnd(7)}| ${(hook.status||'').padEnd(10)}| ${perf.emoji} ${perf.action || 'Waiting for data'}`);
    }

    console.log(`\n🎯 Rules: Double down: [${hooks.rules.doubleDown.join(', ')||'none yet'}] | Testing: [${hooks.rules.testing.join(', ')}] | Dropped: [${hooks.rules.dropped.join(', ')||'none yet'}]`);
    return;
  }

  if (connect) {
    const apiKey = config.postiz.apiKey;
    if (!apiKey || apiKey === 'POSTIZ_API_KEY_HERE') {
      console.log('⚠️  Postiz API key not configured yet.');
      console.log('📋 Set it in config/villa-lithos.json → postiz.apiKey');
      console.log('\n🔧 To get your key:');
      console.log('   1. Sign up at https://postiz.pro');
      console.log('   2. Go to Settings → API Keys');
      console.log('   3. Create a new key');
      console.log('   4. Paste it in the config file');
      console.log('\n📊 Meanwhile, tracking hook performance manually via pilot tracker.');
      return;
    }

    try {
      console.log(`📡 Fetching posts from last ${days} days...`);
      const posts = await apiRequest(config, 'GET', `/public/v1/posts?days=${days}`);
      
      const postList = posts.posts || [];
      console.log(`📬 Found ${postList.length} posts\n`);

      for (const post of postList) {
        const hookMatch = hooks.hooks.find(h => h.postId === post.id);
        if (!hookMatch) continue;

        // Fetch per-post analytics
        try {
          const analytics = await apiRequest(config, 'GET', `/public/v1/analytics/post/${post.id}`);
          
          hookMatch.views = analytics.views || 0;
          hookMatch.likes = analytics.likes || 0;
          hookMatch.comments = analytics.comments || 0;
          hookMatch.shares = analytics.shares || 0;
          
          const totalEngagement = hookMatch.likes + hookMatch.comments + hookMatch.shares;
          hookMatch.engagementRate = hookMatch.views > 0 
            ? parseFloat(((totalEngagement / hookMatch.views) * 100).toFixed(2))
            : 0;

          const perf = classifyPerformance(hookMatch.views, config.analytics.viewThresholds);
          hookMatch.status = perf.tier.toLowerCase();

          console.log(`${perf.emoji} ${hookMatch.id} (${hookMatch.category}): ${hookMatch.views} views, ${hookMatch.engagementRate}% ER → ${perf.action}`);

          // Update rules
          if (hookMatch.views >= config.analytics.viewThresholds.strong) {
            if (!hooks.rules.doubleDown.includes(hookMatch.category)) {
              hooks.rules.doubleDown.push(hookMatch.category);
              hooks.rules.testing = hooks.rules.testing.filter(c => c !== hookMatch.category);
            }
          }

        } catch (e) {
          console.log(`⚠️  ${hookMatch.id}: ${e.message}`);
        }
      }

      hooks.lastUpdated = new Date().toISOString().slice(0, 10);
      saveJSON(HOOKS_PATH, hooks);
      console.log('\n✅ Hook performance data updated.');
      console.log('📋 Run: node villa-daily-report.js for full analysis');

    } catch (e) {
      console.error(`❌ ${e.message}`);
      process.exit(1);
    }
  }
}

if (require.main === module) { main(); }
