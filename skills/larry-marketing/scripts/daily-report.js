#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - Daily Analytics Report
 * The intelligence loop that makes data-driven decisions
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

function loadConfig(configPath) {
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    console.error(`❌ Config file not found: ${configPath}`);
    process.exit(1);
  }
}

async function fetchPostizAnalytics(config, days = 3) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.postiz.com',
      port: 443,
      path: `/public/v1/posts?days=${days}`,
      method: 'GET',
      headers: {
        'Authorization': config.postiz.apiKey
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode === 200) {
            resolve(response.posts || []);
          } else {
            reject(new Error(`Postiz API error: ${data}`));
          }
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function fetchRevenueCatData(config) {
  if (!config.revenuecat?.enabled || !process.env.RC_API_KEY) {
    return null;
  }

  // Simplified RevenueCat integration
  // In practice, you'd fetch transactions and metrics here
  return {
    conversions: [],
    mrr: 0,
    trials: 0
  };
}

function analyzePerformance(posts, conversions = null) {
  const analysis = {
    totalPosts: posts.length,
    totalViews: 0,
    totalLikes: 0,
    totalComments: 0,
    totalShares: 0,
    avgViews: 0,
    topPosts: [],
    lowPosts: [],
    recommendations: []
  };

  if (posts.length === 0) {
    analysis.recommendations.push('No posts in the last 3 days. Resume posting schedule.');
    return analysis;
  }

  // Calculate totals
  posts.forEach(post => {
    const views = post.analytics?.views || 0;
    const likes = post.analytics?.likes || 0;
    const comments = post.analytics?.comments || 0;
    const shares = post.analytics?.shares || 0;

    analysis.totalViews += views;
    analysis.totalLikes += likes;
    analysis.totalComments += comments;
    analysis.totalShares += shares;

    // Categorize posts
    if (views >= 50000) {
      analysis.topPosts.push({ ...post, views, category: 'viral' });
    } else if (views >= 10000) {
      analysis.topPosts.push({ ...post, views, category: 'good' });
    } else if (views < 1000) {
      analysis.lowPosts.push({ ...post, views, category: 'poor' });
    }
  });

  analysis.avgViews = Math.round(analysis.totalViews / posts.length);

  // Generate recommendations based on Larry's framework
  if (analysis.topPosts.length > 0) {
    const topPost = analysis.topPosts.sort((a, b) => b.views - a.views)[0];
    analysis.recommendations.push(`🟢 SCALE IT: "${topPost.caption?.slice(0, 50)}..." got ${topPost.views} views. Make 3 variations of this hook immediately.`);
  }

  if (analysis.lowPosts.length >= 2) {
    analysis.recommendations.push(`🔴 Hook problem detected: ${analysis.lowPosts.length} posts under 1K views. Test radically different hooks - person+conflict, POV, or listicle formats.`);
  }

  if (analysis.avgViews < 5000) {
    analysis.recommendations.push(`🟡 Average views low (${analysis.avgViews}). Research what's trending in your niche RIGHT NOW. Check competitor posts from last 24h.`);
  }

  if (!conversions && analysis.avgViews > 10000) {
    analysis.recommendations.push(`⚠️ High views but no conversion tracking. Connect RevenueCat to optimize for revenue, not just vanity metrics.`);
  }

  return analysis;
}

function generateReport(analysis, config) {
  const date = new Date().toISOString().slice(0, 10);
  const reportPath = `tiktok-marketing/reports/${date}.md`;

  // Create reports directory if it doesn't exist
  const reportsDir = path.dirname(reportPath);
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }

  const report = `# TikTok Performance Report - ${date}

## 📊 3-Day Summary

- **Posts:** ${analysis.totalPosts}
- **Total Views:** ${analysis.totalViews.toLocaleString()}
- **Average Views:** ${analysis.avgViews.toLocaleString()}
- **Total Likes:** ${analysis.totalLikes.toLocaleString()}
- **Total Comments:** ${analysis.totalComments}
- **Total Shares:** ${analysis.totalShares}

## 🏆 Top Performers (${analysis.topPosts.length})

${analysis.topPosts.map(post => 
  `- **${post.views.toLocaleString()} views** - "${post.caption?.slice(0, 60)}..."`
).join('\\n') || 'None'}

## 📉 Underperformers (${analysis.lowPosts.length})

${analysis.lowPosts.map(post => 
  `- **${post.views.toLocaleString()} views** - "${post.caption?.slice(0, 60)}..."`
).join('\\n') || 'None'}

## 🎯 Recommendations

${analysis.recommendations.map(rec => `- ${rec}`).join('\\n')}

## 📈 Next Actions

1. **Immediate:** ${analysis.recommendations[0] || 'Continue current strategy'}
2. **Today:** Test ${analysis.topPosts.length > 0 ? 'variations of winning hook' : 'new hook categories'}
3. **This week:** ${analysis.avgViews > 10000 ? 'Scale successful content' : 'Research competitor trends'}

---
*Generated by Larry's Marketing Experiments v1.0.1*
`;

  fs.writeFileSync(reportPath, report);
  return reportPath;
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = args.find(arg => arg.startsWith('--config='))?.split('=')[1] || 'tiktok-marketing/config.json';
  const days = parseInt(args.find(arg => arg.startsWith('--days='))?.split('=')[1] || '3');

  console.log('📊 Larry\\'s Marketing Experiments - Daily Report\\n');

  const config = loadConfig(configPath);

  try {
    console.log(`📈 Fetching last ${days} days of post analytics...`);
    const posts = await fetchPostizAnalytics(config, days);
    
    console.log('💰 Checking conversion data...');
    const conversions = await fetchRevenueCatData(config);
    
    console.log('🧠 Analyzing performance patterns...');
    const analysis = analyzePerformance(posts, conversions);
    
    console.log('📝 Generating report...');
    const reportPath = generateReport(analysis, config);
    
    console.log(`✅ Report generated: ${reportPath}\\n`);
    
    // Print summary to console
    console.log('📊 QUICK SUMMARY:');
    console.log(`   ${analysis.totalPosts} posts, ${analysis.avgViews.toLocaleString()} avg views`);
    console.log(`   🏆 ${analysis.topPosts.length} top performers`);
    console.log(`   📉 ${analysis.lowPosts.length} underperformers`);
    
    if (analysis.recommendations.length > 0) {
      console.log('\\n🎯 TOP RECOMMENDATION:');
      console.log(`   ${analysis.recommendations[0]}`);
    }
    
    console.log(`\\n📋 Full report: ${reportPath}`);
    
  } catch (error) {
    console.error(`❌ Error generating report: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}