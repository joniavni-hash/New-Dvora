#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - Analytics Connector
 * Connects Postiz posts to TikTok video IDs for per-post analytics
 */

const fs = require('fs');
const https = require('https');

function loadConfig(configPath) {
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    console.error(`❌ Config file not found: ${configPath}`);
    process.exit(1);
  }
}

async function fetchPostizPosts(config, days = 3) {
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

async function fetchMissingVideos(config, postId) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.postiz.com',
      port: 443,
      path: `/public/v1/posts/${postId}/missing`,
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
            resolve(response.videos || []);
          } else {
            reject(new Error(`Missing videos API error: ${data}`));
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

async function connectReleaseId(config, postId, releaseId) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ releaseId });
    
    const options = {
      hostname: 'api.postiz.com',
      port: 443,
      path: `/public/v1/posts/${postId}/release-id`,
      method: 'PUT',
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
        if (res.statusCode === 200) {
          resolve();
        } else {
          reject(new Error(`Connect release ID error: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function getPostAnalytics(config, postId) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.postiz.com',
      port: 443,
      path: `/public/v1/analytics/post/${postId}`,
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
            resolve(response);
          } else {
            reject(new Error(`Analytics API error: ${data}`));
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

function isRecentEnough(publishDate) {
  const now = new Date();
  const published = new Date(publishDate);
  const hoursSince = (now - published) / (1000 * 60 * 60);
  
  // Wait at least 2 hours for TikTok API indexing
  return hoursSince >= 2;
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = args.find(arg => arg.startsWith('--config='))?.split('=')[1] || 'tiktok-marketing/config.json';
  const days = parseInt(args.find(arg => arg.startsWith('--days='))?.split('=')[1] || '3');
  const connect = args.includes('--connect');

  console.log('🔗 Larry\\'s Marketing Experiments - Analytics Connector\\n');

  if (!connect) {
    console.log('Add --connect flag to link posts to TikTok video IDs');
    console.log('Usage: node scripts/check-analytics.js --connect --days 3');
    return;
  }

  const config = loadConfig(configPath);

  try {
    console.log(`📊 Fetching posts from last ${days} days...`);
    const posts = await fetchPostizPosts(config, days);
    
    const unconnectedPosts = posts.filter(post => 
      !post.releaseId && 
      post.platform === 'tiktok' && 
      isRecentEnough(post.publishedAt)
    );

    if (unconnectedPosts.length === 0) {
      console.log('✅ All eligible posts already connected or too recent');
      console.log('⏳ Wait 2+ hours after publishing before connecting');
      return;
    }

    console.log(`🔗 Found ${unconnectedPosts.length} posts to connect...\\n`);

    for (const post of unconnectedPosts) {
      console.log(`📱 Processing post: "${post.caption?.slice(0, 50)}..."`);
      console.log(`   Published: ${new Date(post.publishedAt).toLocaleString()}`);
      
      try {
        const videos = await fetchMissingVideos(config, post.id);
        
        if (videos.length === 0) {
          console.log('   ⚠️  No unconnected TikTok videos found');
          continue;
        }

        // Sort videos by ID (higher = newer) and pick the newest unconnected one
        const sortedVideos = videos.sort((a, b) => parseInt(b.id) - parseInt(a.id));
        const newestVideo = sortedVideos[0];
        
        console.log(`   🎬 Connecting to TikTok video ID: ${newestVideo.id}`);
        await connectReleaseId(config, post.id, newestVideo.id);
        
        console.log('   ✅ Connected successfully');
        
        // Fetch analytics for connected post
        console.log('   📊 Fetching analytics...');
        const analytics = await getPostAnalytics(config, post.id);
        console.log(`   📈 Views: ${analytics.views || 0}, Likes: ${analytics.likes || 0}, Comments: ${analytics.comments || 0}`);
        
      } catch (error) {
        console.log(`   ❌ Error: ${error.message}`);
      }
      
      console.log('');
    }

    console.log('🎉 Analytics connection complete!');
    console.log('\\n📊 Run daily report to see performance:');
    console.log('   node scripts/daily-report.js --days 3');
    
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}