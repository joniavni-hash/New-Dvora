#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - Slideshow Image Generator
 * Generates 6 AI images for TikTok slideshows using OpenAI, Stability AI, or Replicate
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

function loadPrompts(promptsPath) {
  try {
    return JSON.parse(fs.readFileSync(promptsPath, 'utf8'));
  } catch (error) {
    console.error(`❌ Prompts file not found: ${promptsPath}`);
    process.exit(1);
  }
}

async function generateWithOpenAI(prompt, config) {
  const payload = {
    model: config.imageGen.model || 'gpt-image-1.5',
    prompt: prompt,
    n: 1,
    size: '1024x1536', // Portrait for TikTok
    quality: 'hd'
  };

  console.log(`🎨 Generating with OpenAI ${payload.model}...`);
  
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(payload);
    
    const options = {
      hostname: 'api.openai.com',
      port: 443,
      path: '/v1/images/generations',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.imageGen.apiKey}`,
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.data && response.data[0]?.url) {
            resolve(response.data[0].url);
          } else {
            reject(new Error(`OpenAI API error: ${data}`));
          }
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function downloadImage(url, outputPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(outputPath);
    
    https.get(url, (response) => {
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        resolve(outputPath);
      });
      
      file.on('error', (err) => {
        fs.unlink(outputPath, () => {}); // Delete partial file
        reject(err);
      });
    }).on('error', reject);
  });
}

function buildPrompts(basePrompt, slideStructure) {
  return slideStructure.map((slide, index) => {
    return `${basePrompt}, ${slide.description}. iPhone photo, realistic lighting, natural colors, taken on iPhone 15 Pro. Portrait orientation. No text, no watermarks, no logos.`;
  });
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = args.find(arg => arg.startsWith('--config='))?.split('=')[1] || 'tiktok-marketing/config.json';
  const outputDir = args.find(arg => arg.startsWith('--output='))?.split('=')[1] || `tiktok-marketing/posts/${new Date().toISOString().slice(0,16).replace(/[-:]/g, '').replace('T', '-')}`;
  const promptsPath = args.find(arg => arg.startsWith('--prompts='))?.split('=')[1] || 'prompts.json';

  console.log('🎯 Larry\'s Marketing Experiments - Image Generator\n');

  const config = loadConfig(configPath);
  const prompts = loadPrompts(promptsPath);

  // Create output directory
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Default 6-slide structure if not provided
  const defaultSlides = [
    { description: "modern living room, clean and inviting" },
    { description: "same living room, slightly different angle, cozy atmosphere" }, 
    { description: "same living room, showing transformation potential" },
    { description: "same living room, beautifully designed, aspirational" },
    { description: "same living room, perfect lighting, magazine quality" },
    { description: "same living room, final result, absolutely stunning" }
  ];

  const slides = prompts.slides || defaultSlides;
  const basePrompt = config.imageGen.basePrompt || "iPhone photo of a modern apartment living room";

  const fullPrompts = buildPrompts(basePrompt, slides);

  console.log(`📝 Generating ${fullPrompts.length} slides...`);
  console.log(`📁 Output directory: ${outputDir}\n`);

  for (let i = 0; i < fullPrompts.length; i++) {
    const outputPath = path.join(outputDir, `slide-${i + 1}.png`);
    
    // Skip if file already exists (resume functionality)
    if (fs.existsSync(outputPath)) {
      console.log(`⏩ Slide ${i + 1} already exists, skipping...`);
      continue;
    }

    try {
      console.log(`🎨 Generating slide ${i + 1}/${fullPrompts.length}...`);
      console.log(`   Prompt: ${fullPrompts[i].slice(0, 100)}...`);
      
      let imageUrl;
      
      if (config.imageGen.provider === 'openai') {
        imageUrl = await generateWithOpenAI(fullPrompts[i], config);
      } else {
        throw new Error(`Provider ${config.imageGen.provider} not implemented yet`);
      }
      
      console.log(`📥 Downloading slide ${i + 1}...`);
      await downloadImage(imageUrl, outputPath);
      console.log(`✅ Slide ${i + 1} saved: ${outputPath}\n`);
      
      // Delay to avoid rate limits
      if (i < fullPrompts.length - 1) {
        console.log('⏳ Waiting 2 seconds...\n');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
    } catch (error) {
      console.error(`❌ Error generating slide ${i + 1}: ${error.message}`);
      process.exit(1);
    }
  }

  console.log(`🎉 All slides generated successfully!`);
  console.log(`📁 Output: ${outputDir}`);
  console.log(`\n📋 Next steps:`);
  console.log(`1. Add text overlays: node scripts/add-overlays.js --dir ${outputDir}`);
  console.log(`2. Post to TikTok: node scripts/post-to-tiktok.js --dir ${outputDir}`);
}

if (require.main === module) {
  main();
}