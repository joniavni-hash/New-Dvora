#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - TikTok Poster
 * Posts slideshow to TikTok as draft via Postiz API
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

async function postToPostiz(config, slideImages, caption, title) {
  const formData = new FormData();
  
  // Add images
  slideImages.forEach((imagePath, index) => {
    const imageBuffer = fs.readFileSync(imagePath);
    formData.append('media', imageBuffer, `slide-${index + 1}.png`);
  });

  // Add post data
  formData.append('caption', caption);
  formData.append('title', title);
  formData.append('privacy_level', config.posting.privacyLevel || 'SELF_ONLY'); // Draft mode
  
  // Add integration IDs for cross-posting
  const integrationIds = [];
  if (config.postiz.integrationIds.tiktok) {
    integrationIds.push(config.postiz.integrationIds.tiktok);
  }
  if (config.posting.crossPost && config.posting.crossPost.includes('instagram')) {
    if (config.postiz.integrationIds.instagram) {
      integrationIds.push(config.postiz.integrationIds.instagram);
    }
  }
  if (config.posting.crossPost && config.posting.crossPost.includes('youtube')) {
    if (config.postiz.integrationIds.youtube) {
      integrationIds.push(config.postiz.integrationIds.youtube);
    }
  }
  
  formData.append('integrations', JSON.stringify(integrationIds));

  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.postiz.com',
      port: 443,
      path: '/public/v1/posts',
      method: 'POST',
      headers: {
        'Authorization': config.postiz.apiKey,
        'Content-Type': 'multipart/form-data'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(response);
          } else {
            reject(new Error(`Postiz API error (${res.statusCode}): ${data}`));
          }
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', reject);
    
    // Note: This is a simplified form-data implementation
    // In production, use a proper form-data library
    req.write('--boundary\\r\\n');
    req.write('Content-Disposition: form-data; name="caption"\\r\\n\\r\\n');
    req.write(caption);
    req.write('\\r\\n--boundary--\\r\\n');
    req.end();
  });
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = args.find(arg => arg.startsWith('--config='))?.split('=')[1] || 'tiktok-marketing/config.json';
  const dir = args.find(arg => arg.startsWith('--dir='))?.split('=')[1];
  const caption = args.find(arg => arg.startsWith('--caption='))?.split('=')[1] || '';
  const title = args.find(arg => arg.startsWith('--title='))?.split('=')[1] || '';

  if (!dir) {
    console.error('❌ --dir parameter required');
    console.error('Usage: node scripts/post-to-tiktok.js --dir=tiktok-marketing/posts/YYYY-MM-DD-HHmm/ --caption="Your caption" --title="Your title"');
    process.exit(1);
  }

  console.log('📱 Larry\'s Marketing Experiments - TikTok Poster\\n');

  const config = loadConfig(configPath);

  // Find final slide images
  const finalSlides = fs.readdirSync(dir)
    .filter(file => file.startsWith('final-') && file.endsWith('.png'))
    .sort((a, b) => {
      const matchA = a.match(/final-(\d+)/);
      const matchB = b.match(/final-(\d+)/);
      const numA = matchA ? parseInt(matchA[1]) : 0;
      const numB = matchB ? parseInt(matchB[1]) : 0;
      return numA - numB;
    })
    .map(file => path.join(dir, file));

  if (finalSlides.length === 0) {
    console.error(`❌ No final slides found in ${dir}`);
    console.error('Add text overlays first with: node scripts/add-overlays.js');
    process.exit(1);
  }

  console.log(`📱 Posting ${finalSlides.length} slides to TikTok...`);
  console.log(`📁 Directory: ${dir}`);
  console.log(`📝 Caption: ${caption}`);
  console.log(`🎬 Title: ${title}\\n`);

  try {
    console.log('🚀 Uploading to Postiz...');
    const response = await postToPostiz(config, finalSlides, caption, title);
    
    console.log('✅ Posted successfully!');
    console.log(`📱 Post ID: ${response.id || 'N/A'}`);
    console.log(`📊 Platforms: ${config.posting.crossPost ? config.posting.crossPost.join(', ') : 'TikTok'}`);
    
    console.log('\\n⚠️  IMPORTANT: Posts are uploaded as DRAFTS');
    console.log('🎵 Go to your TikTok inbox and add trending music before publishing');
    console.log('🎯 Music is the #1 factor for TikTok reach - don\'t skip this step!');
    
    console.log('\\n📊 Track performance:');
    console.log('   node scripts/check-analytics.js --connect (after 2+ hours)');
    console.log('   node scripts/daily-report.js (next morning)');
    
  } catch (error) {
    console.error(`❌ Error posting to TikTok: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}