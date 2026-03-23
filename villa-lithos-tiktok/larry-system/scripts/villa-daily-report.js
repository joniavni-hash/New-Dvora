#!/usr/bin/env node

/**
 * Villa Lithos — Daily Intelligence Report (Larry's System)
 * Analyzes hook performance, generates recommendations, 
 * and outputs next-action decisions based on Larry's methodology.
 * 
 * Usage:
 *   node villa-daily-report.js                    # Full report
 *   node villa-daily-report.js --quick             # One-line summary
 *   node villa-daily-report.js --next-hook         # What to post next
 */

const fs = require('fs');
const path = require('path');

const CONFIG_PATH = path.join(__dirname, '../config/villa-lithos.json');
const HOOKS_PATH = path.join(__dirname, '../hooks/hook-performance.json');
const REPORTS_DIR = path.join(__dirname, '../reports');

function loadJSON(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { console.error(`❌ ${p}: ${e.message}`); process.exit(1); }
}

function analyzeHooks(hooks, thresholds) {
  const posted = hooks.hooks.filter(h => h.status !== 'pending-post');
  const withData = posted.filter(h => h.views !== null);
  
  const totalViews = withData.reduce((s, h) => s + (h.views || 0), 0);
  const avgViews = withData.length > 0 ? Math.round(totalViews / withData.length) : 0;
  const avgER = withData.length > 0 
    ? parseFloat((withData.reduce((s, h) => s + (h.engagementRate || 0), 0) / withData.length).toFixed(2))
    : 0;

  const bestHook = withData.sort((a, b) => (b.views || 0) - (a.views || 0))[0];
  const worstHook = withData.sort((a, b) => (a.views || 0) - (b.views || 0))[0];

  // Category analysis
  const byCategory = {};
  for (const h of withData) {
    if (!byCategory[h.category]) byCategory[h.category] = { views: 0, count: 0, hooks: [] };
    byCategory[h.category].views += h.views || 0;
    byCategory[h.category].count++;
    byCategory[h.category].hooks.push(h);
  }
  for (const cat in byCategory) {
    byCategory[cat].avgViews = Math.round(byCategory[cat].views / byCategory[cat].count);
  }

  return {
    totalPosts: posted.length,
    postsWithData: withData.length,
    totalViews,
    avgViews,
    avgER,
    bestHook,
    worstHook,
    byCategory,
    pending: hooks.hooks.filter(h => h.status === 'pending-post').length,
    queued: hooks.hookQueue.length
  };
}

function generateDecisions(analysis, hooks, thresholds) {
  const decisions = [];

  // What's working?
  if (analysis.bestHook && analysis.bestHook.views >= thresholds.strong) {
    decisions.push({
      type: 'SCALE',
      priority: 'HIGH',
      action: `Hook "${analysis.bestHook.text?.slice(0, 50)}..." got ${analysis.bestHook.views} views. Create 3 variations of the "${analysis.bestHook.category}" category NOW.`,
      category: analysis.bestHook.category
    });
  }

  // What's failing?
  const failedCategories = Object.entries(analysis.byCategory)
    .filter(([_, data]) => data.avgViews < thresholds.decent && data.count >= 2)
    .map(([cat]) => cat);
  
  for (const cat of failedCategories) {
    decisions.push({
      type: 'DROP',
      priority: 'MEDIUM',
      action: `Category "${cat}" averaging <${thresholds.decent} views after ${analysis.byCategory[cat].count} attempts. DROP IT.`,
      category: cat
    });
  }

  // What to test next?
  const untested = hooks.hookQueue.filter(h => h.status === 'ready' || h.status === 'concept');
  if (untested.length > 0) {
    const next = untested.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return (priorityOrder[a.priority] || 1) - (priorityOrder[b.priority] || 1);
    })[0];
    decisions.push({
      type: 'TEST',
      priority: 'MEDIUM',
      action: `Next test: "${next.text}" (${next.category}). Create slides and post at best-performing time.`,
      hookId: next.id
    });
  }

  // Engagement vs Views mismatch
  if (analysis.avgViews > thresholds.good && analysis.avgER < 3) {
    decisions.push({
      type: 'OPTIMIZE',
      priority: 'MEDIUM',
      action: 'Views are decent but engagement low. Test stronger CTAs on slide 6 and more provocative hooks.'
    });
  }

  if (analysis.avgViews < thresholds.decent && analysis.postsWithData >= 3) {
    decisions.push({
      type: 'PIVOT',
      priority: 'HIGH',
      action: 'Average views consistently low. Research trending travel content on TikTok RIGHT NOW. Check competitor villas posting in last 48h.'
    });
  }

  return decisions;
}

function selectNextHook(hooks, analysis) {
  // Priority: high-priority ready hooks from winning categories, then untested categories
  const winningCategories = Object.entries(analysis.byCategory)
    .filter(([_, d]) => d.avgViews >= 5000)
    .map(([cat]) => cat);

  // 1. Variations of winners
  const winnerVariations = hooks.hookQueue.filter(h => 
    winningCategories.includes(h.category) && (h.status === 'ready' || h.status === 'concept')
  );
  if (winnerVariations.length > 0) return winnerVariations[0];

  // 2. High priority untested
  const highPri = hooks.hookQueue.filter(h => h.priority === 'high' && h.status !== 'dropped');
  if (highPri.length > 0) return highPri[0];

  // 3. Any ready hook
  const ready = hooks.hookQueue.filter(h => h.status === 'ready' || h.status === 'concept');
  return ready[0] || null;
}

function main() {
  const args = process.argv.slice(2);
  const quick = args.includes('--quick');
  const nextHook = args.includes('--next-hook');

  const config = loadJSON(CONFIG_PATH);
  const hooks = loadJSON(HOOKS_PATH);
  const analysis = analyzeHooks(hooks, config.analytics.viewThresholds);
  const decisions = generateDecisions(analysis, hooks, config.analytics.viewThresholds);

  if (quick) {
    console.log(`📊 Villa Lithos | ${analysis.postsWithData} posts tracked | ${analysis.avgViews} avg views | ${analysis.avgER}% ER | ${decisions[0]?.action || 'No actions'}`);
    return;
  }

  if (nextHook) {
    const next = selectNextHook(hooks, analysis);
    if (next) {
      console.log(`🎣 Next hook to test:\n`);
      console.log(`   ID: ${next.id}`);
      console.log(`   Category: ${next.category}`);
      console.log(`   Text: "${next.text}"`);
      console.log(`   Priority: ${next.priority}`);
      console.log(`\n📋 Create slides for this hook, then:`);
      console.log(`   node post-villa.js --slides=<dir> --hook-id=${next.id} --caption="..."`);
    } else {
      console.log('📝 No hooks in queue. Time to brainstorm new angles!');
    }
    return;
  }

  // Full report
  const date = new Date().toISOString().slice(0, 10);
  
  const report = `# 🏛️ Villa Lithos — Daily Intelligence Report
## ${date}

### 📊 Performance Summary
| Metric | Value |
|--------|-------|
| Posts tracked | ${analysis.postsWithData} |
| Total views | ${analysis.totalViews.toLocaleString()} |
| Average views | ${analysis.avgViews.toLocaleString()} |
| Average ER | ${analysis.avgER}% |
| Hooks in queue | ${analysis.queued} |
| Pending posts | ${analysis.pending} |

### 🏆 Best Performer
${analysis.bestHook ? `**${analysis.bestHook.views?.toLocaleString()} views** — "${analysis.bestHook.text?.slice(0, 60)}..." (${analysis.bestHook.category})` : 'No data yet'}

### 📉 Worst Performer
${analysis.worstHook ? `**${analysis.worstHook.views?.toLocaleString()} views** — "${analysis.worstHook.text?.slice(0, 60)}..." (${analysis.worstHook.category})` : 'No data yet'}

### 📊 Category Breakdown
| Category | Posts | Avg Views | Status |
|----------|-------|-----------|--------|
${Object.entries(analysis.byCategory).map(([cat, d]) => 
  `| ${cat} | ${d.count} | ${d.avgViews.toLocaleString()} | ${d.avgViews >= 10000 ? '🟢 Scale' : d.avgViews >= 1000 ? '🟡 Test more' : '🔴 Consider dropping'} |`
).join('\n') || '| — | — | — | No data yet |'}

### 🎯 Decisions & Actions
${decisions.map((d, i) => `${i+1}. **[${d.type}]** ${d.priority} priority — ${d.action}`).join('\n') || 'No decisions yet — need more data.'}

### 🔄 Learning Rules
- **Double down**: ${hooks.rules.doubleDown.length > 0 ? hooks.rules.doubleDown.join(', ') : 'None yet'}
- **Currently testing**: ${hooks.rules.testing.join(', ')}
- **Dropped**: ${hooks.rules.dropped.length > 0 ? hooks.rules.dropped.join(', ') : 'None yet'}

### 📋 Next Hook to Test
${(() => {
  const next = selectNextHook(hooks, analysis);
  return next ? `**${next.id}** — "${next.text}" (${next.category}, ${next.priority} priority)` : 'Queue empty — brainstorm new hooks';
})()}

---
*Generated by Larry's Marketing System for Villa Lithos*
`;

  // Save report
  if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });
  const reportPath = path.join(REPORTS_DIR, `${date}.md`);
  fs.writeFileSync(reportPath, report);

  // Print to console
  console.log(report);
  console.log(`\n📄 Report saved: ${reportPath}`);
}

if (require.main === module) { main(); }
