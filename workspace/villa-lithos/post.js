#!/usr/bin/env node

/**
 * Villa Lithos - Post Publisher
 * Reads the pending-post.json (approved by Jonathan) and publishes to FB + Instagram.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CONFIG_PATH = path.join(__dirname, 'config.json');
const PENDING_PATH = path.join(__dirname, 'pending-post.json');

async function publish() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));

  if (!fs.existsSync(PENDING_PATH)) {
    console.error('❌ No pending post found. Run prepare-post.js first.');
    process.exit(1);
  }

  const pending = JSON.parse(fs.readFileSync(PENDING_PATH, 'utf8'));
  const { photoId, photoName, caption, photoIndex } = pending;

  console.log(`Publishing: ${photoName}`);

  // Get fresh photo URL
  const photoData = JSON.parse(execSync(
    `curl -s "https://graph.facebook.com/v19.0/${photoId}?fields=images&access_token=${config.page_access_token}"`
  ).toString());

  if (photoData.error) {
    console.error('❌ Could not fetch photo:', photoData.error.message);
    process.exit(1);
  }

  const freshUrl = photoData.images.sort((a, b) => b.width - a.width)[0].source;

  // Download photo
  const tmpPath = `/tmp/villa_post_${Date.now()}.jpg`;
  execSync(`curl -s -L "${freshUrl}" -o "${tmpPath}"`);
  const size = fs.statSync(tmpPath).size;
  console.log(`Downloaded: ${size} bytes`);

  if (size < 1000) {
    console.error('❌ Photo download failed');
    process.exit(1);
  }

  // Post to Facebook
  const fbResult = JSON.parse(execSync(
    `curl -s -X POST "https://graph.facebook.com/v19.0/${config.page_id}/photos" ` +
    `-F "caption=${caption.replace(/"/g, '\\"').replace(/\n/g, '\\n')}" ` +
    `-F "source=@${tmpPath}" ` +
    `-F "access_token=${config.page_access_token}"`
  ).toString());

  if (fbResult.id) {
    console.log(`✅ Facebook posted! ID: ${fbResult.id}`);
  } else {
    console.error('❌ Facebook failed:', JSON.stringify(fbResult));
    fs.unlinkSync(tmpPath);
    process.exit(1);
  }

  // Post to Instagram
  if (config.instagram_id) {
    try {
      const containerResult = JSON.parse(execSync(
        `curl -s -X POST "https://graph.facebook.com/v19.0/${config.instagram_id}/media" ` +
        `-F "image_url=${freshUrl}" ` +
        `-F "caption=${caption.replace(/"/g, '\\"').replace(/\n/g, '\\n')}" ` +
        `-F "access_token=${config.page_access_token}"`
      ).toString());

      if (containerResult.id) {
        const publishResult = JSON.parse(execSync(
          `curl -s -X POST "https://graph.facebook.com/v19.0/${config.instagram_id}/media_publish" ` +
          `-F "creation_id=${containerResult.id}" ` +
          `-F "access_token=${config.page_access_token}"`
        ).toString());

        if (publishResult.id) {
          console.log(`✅ Instagram posted! ID: ${publishResult.id}`);
        } else {
          console.error('❌ Instagram publish failed:', JSON.stringify(publishResult));
        }
      }
    } catch (e) {
      console.error('❌ Instagram error:', e.message);
    }
  }

  fs.unlinkSync(tmpPath);

  // Update config & remove pending
  config.last_post_date = new Date().toISOString();
  if (photoIndex !== undefined) config.last_photo_index = photoIndex;
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
  fs.unlinkSync(PENDING_PATH);

  console.log('✅ Done. Pending post cleared.');
}

publish().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
