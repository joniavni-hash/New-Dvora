#!/usr/bin/env node

/**
 * Larry's Marketing Experiments - Onboarding Script
 * Validates TikTok marketing config is complete before first post
 */

const fs = require('fs');
const path = require('path');

function loadConfig(configPath) {
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    console.error(`❌ Config file not found: ${configPath}`);
    process.exit(1);
  }
}

function validateConfig(config) {
  const errors = [];
  const warnings = [];

  // App profile validation
  if (!config.app?.name) errors.push('app.name is required');
  if (!config.app?.description) errors.push('app.description is required');
  if (!config.app?.audience) errors.push('app.audience is required');
  if (!config.app?.category) warnings.push('app.category not set (home/beauty/fitness/productivity/food/other)');

  // Image generation validation  
  if (!config.imageGen?.provider) errors.push('imageGen.provider is required');
  if (!config.imageGen?.apiKey) errors.push('imageGen.apiKey is required');
  if (config.imageGen?.provider === 'openai' && config.imageGen?.model !== 'gpt-image-1.5') {
    warnings.push('⚠️ Use gpt-image-1.5 for OpenAI (NOT gpt-image-1)');
  }

  // Postiz validation
  if (!config.postiz?.apiKey) errors.push('postiz.apiKey is required');
  if (!config.postiz?.integrationIds?.tiktok) errors.push('postiz.integrationIds.tiktok is required');

  // RevenueCat (optional but recommended)
  if (!config.revenuecat?.enabled) {
    warnings.push('RevenueCat not connected - can only optimize for views, not revenue');
  }

  return { errors, warnings };
}

function main() {
  const args = process.argv.slice(2);
  const configPath = args.find(arg => arg.startsWith('--config='))?.split('=')[1] || 'tiktok-marketing/config.json';
  const validate = args.includes('--validate');

  if (!validate) {
    console.log('Larry\'s Marketing Experiments - Onboarding');
    console.log('Use --validate to check config completeness');
    return;
  }

  console.log('🎯 Validating TikTok marketing configuration...\n');

  const config = loadConfig(configPath);
  const { errors, warnings } = validateConfig(config);

  if (errors.length > 0) {
    console.error('❌ Configuration errors:');
    errors.forEach(error => console.error(`   - ${error}`));
    console.error('\nFix these before posting.\n');
    process.exit(1);
  }

  if (warnings.length > 0) {
    console.warn('⚠️  Configuration warnings:');
    warnings.forEach(warning => console.warn(`   - ${warning}`));
    console.warn('');
  }

  console.log('✅ Configuration valid! Ready to start posting.\n');
  
  console.log('Next steps:');
  console.log('1. Generate test slideshow: node scripts/generate-slides.js');
  console.log('2. Add text overlays: node scripts/add-overlays.js'); 
  console.log('3. Post to TikTok: node scripts/post-to-tiktok.js');
  console.log('4. Set up daily analytics cron');
}

if (require.main === module) {
  main();
}