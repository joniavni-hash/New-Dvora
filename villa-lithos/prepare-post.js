#!/usr/bin/env node

/**
 * Villa Lithos - Post Preparer
 * Generates post content and sends preview to Jonathan via Telegram for approval.
 * Run by LaunchAgent daily at 10:00.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CONFIG_PATH = path.join(__dirname, 'config.json');
const PENDING_PATH = path.join(__dirname, 'pending-post.json');

const TELEGRAM_BOT_TOKEN = '8704690302:AAEDZWvJJYBxHdXevaVtDGs_iJWTqrEI72k';
const TELEGRAM_CHAT_ID = '539224224';

// Each photo has its own dedicated caption — tight 1:1 match
const PHOTO_POSTS = [
  {
    photoName: 'Infinity Pool',
    caption: "Where the water meets the horizon. 🌊\n\nVilla Lithos' private infinity pool — overlooking the crystal-clear waters of Porto Rafti Bay. Wake up, take a dip, feel the Aegean breeze.\n\nThis is what mornings are made for. 🇬🇷\n\n#VillaLithos #InfinityPool #PortoRafti #LuxuryVilla #GreeceHoliday #PrivatePool"
  },
  {
    photoName: 'Bath with view to the beach',
    caption: "A bath with a view. 🛁🌊\n\nAt Villa Lithos, even the bathroom has a story to tell. Soak in the tub while watching the waves roll in over Porto Rafti Bay — because luxury really is in the details.\n\n#VillaLithos #BathroomGoals #LuxuryDetails #GreeceLuxury #VillaHoliday #PortoRafti"
  },
  {
    photoName: 'Sauna',
    caption: "Sauna session with an Aegean backdrop. 🧖‍♀️\n\nAt Villa Lithos, the sauna isn't tucked away in a corner — it's part of the experience. Steam, relax, and step out into the warm Greek air.\n\nThis is what a proper holiday feels like.\n\n#VillaLithos #PrivateSauna #LuxuryVilla #GreekRelaxation #VillaHoliday #PortoRafti"
  },
  {
    photoName: 'Outdoor Kitchen',
    caption: "Dinner al fresco, the Greek way. 🍽️🌿\n\nVilla Lithos' outdoor kitchen was built for long, lazy evenings — fresh fish from the local market, cold Assyrtiko in hand, the sound of the Aegean in the background.\n\nThis is the Greek holiday you deserve.\n\n#VillaLithos #OutdoorKitchen #AlFresco #GreekFood #LuxuryVilla #PortoRafti"
  },
  {
    photoName: 'Paddle Court',
    caption: "We thought of everything. Including a padel court. 🎾\n\nSome of the best holiday memories are made in unexpected moments — a spontaneous game under the Greek sun, sea breeze, good company.\n\nVilla Lithos. Where every day surprises you.\n\n#VillaLithos #PadelCourt #LuxuryVilla #VillaActivities #GreeceHoliday #PortoRafti"
  },
  {
    photoName: 'Path to the Sauna',
    caption: "Every step is part of the experience. 🌿\n\nThe path to the sauna at Villa Lithos winds through stone and greenery — a little moment of transition between the pool and the heat, the outside and the inside.\n\nThe details make the difference.\n\n#VillaLithos #LuxuryDetails #GreekVilla #PortoRafti #VillaHoliday"
  },
  {
    photoName: 'Villa Lithos exterior',
    caption: "Meet Villa Lithos. 🏛️\n\nBuilt from local stone, perched above Porto Rafti Bay — this is where Greece reveals its quieter, more intimate side.\n\nNot a resort. Not a hotel. A home — with an infinity pool, sauna, padel court, and one of the most beautiful views on the Attica coast.\n\n45 minutes from Athens Airport. A world away from everything else. 🇬🇷\n\n#VillaLithos #PortoRafti #LuxuryVilla #GreeceVilla #HiddenGreece #AtticaCoast"
  },
  {
    photoName: 'Living Room',
    caption: "This is what switching off actually looks like. 🌿\n\nOpen spaces, natural stone, soft light — the living room at Villa Lithos was designed to make you slow down. No agenda. No rush. Just your people and the Greek sun outside.\n\n#VillaLithos #InteriorDesign #LuxuryInteriors #GreeceHoliday #PrivateVilla #PortoRafti"
  },
  {
    photoName: 'View from above',
    caption: "Porto Rafti from above. 🗺️✨\n\nOne of Attica's most beautiful bays — and one of Greece's best-kept secrets. While the world queues for Santorini sunsets, guests at Villa Lithos enjoy this.\n\nDiscover the Greece that Greeks love.\n\n#PortoRafti #HiddenGreece #VillaLithos #AerialView #GreeceTravel #AtticaCoast"
  },
  {
    photoName: 'Paradise view',
    caption: "Paradise isn't a destination. It's a feeling. 🌊☀️\n\nAt Villa Lithos, it starts the moment you step outside — turquoise water, open sky, and the kind of quiet that actually lets you breathe.\n\nPorto Rafti, Greece. Come find it. 🇬🇷\n\n#VillaLithos #PortoRafti #GreeceParadise #LuxuryTravel #VillaHoliday #MediterraneanLife"
  },
  {
    photoName: 'Paradise view 2',
    caption: "No filter needed. No caption required. 🌊\n\nJust the view from Villa Lithos on a Greek morning — and the quiet knowledge that today has absolutely nowhere to be.\n\n#VillaLithos #PortoRafti #GreeceVibes #LuxuryVilla #MorningViews #VillaHoliday"
  }
];

async function prepare() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));

  // Check if enough time has passed
  if (config.last_post_date) {
    const hoursSince = (Date.now() - new Date(config.last_post_date).getTime()) / (1000 * 60 * 60);
    if (hoursSince < 40) {
      console.log(`⏭️ Skipping — last post was ${Math.round(hoursSince)}h ago`);
      process.exit(0);
    }
  }

  // Check if there's already a pending post waiting for approval
  if (fs.existsSync(PENDING_PATH)) {
    console.log('⏳ Already a pending post waiting for approval');
    process.exit(0);
  }

  // Pick a random photo-post pair (avoid repeating last used)
  const lastUsed = config.last_photo_index || 0;
  let index;
  do { index = Math.floor(Math.random() * PHOTO_POSTS.length); } while (index === lastUsed && PHOTO_POSTS.length > 1);
  
  const post = PHOTO_POSTS[index];
  const photo = config.photos.find(p => p.name.toLowerCase().includes(post.photoName.toLowerCase())) || config.photos[index % config.photos.length];
  const caption = post.caption;

  // Get fresh photo URL
  const photoData = JSON.parse(execSync(
    `curl -s "https://graph.facebook.com/v19.0/${photo.id}?fields=images&access_token=${config.page_access_token}"`
  ).toString());
  const freshUrl = photoData.images.sort((a, b) => b.width - a.width)[0].source;

  // Save pending post
  const pending = { photoIndex: index, photoId: photo.id, photoName: photo.name, freshUrl, caption, createdAt: new Date().toISOString() };
  fs.writeFileSync(PENDING_PATH, JSON.stringify(pending, null, 2));

  // Send Telegram preview
  const previewMsg = `🏛️ *Villa Lithos — פוסט ממתין לאישור*\n\n*תמונה:* ${photo.name}\n\n*טקסט:*\n${caption}\n\n---\nשלח *פרסם* לאישור, או *דלג* לדלג על הפוסט הזה`;

  execSync(
    `curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendPhoto" ` +
    `-F "chat_id=${TELEGRAM_CHAT_ID}" ` +
    `-F "photo=${freshUrl}" ` +
    `-F "caption=${previewMsg.replace(/"/g, '\\"')}" ` +
    `-F "parse_mode=Markdown"`
  );

  console.log(`✅ Preview sent to Jonathan for approval. Photo: ${photo.name}`);
}

prepare().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
