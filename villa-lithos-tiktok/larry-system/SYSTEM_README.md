# 🏛️ Villa Lithos — Larry's Integrated Marketing System

## Overview
Complete social media automation for Villa Lithos using Larry's proven methodology.
No external tools needed — everything runs from this directory.

## Architecture

```
larry-system/
├── config/
│   └── villa-lithos.json      ← Master config (Postiz, platforms, thresholds)
├── hooks/
│   └── hook-performance.json   ← Hook tracker + learning rules + decision log
├── scripts/
│   ├── post-villa.js           ← Post slides via Postiz API
│   ├── check-villa-analytics.js← Fetch analytics, update hook data
│   ├── villa-daily-report.js   ← Intelligence report + next-action decisions
│   └── generate-villa-slides.js← Prepare slides for a hook from photo bank
├── reports/                    ← Daily reports (auto-generated)
├── posts/                      ← Post assets per date
└── SYSTEM_README.md            ← This file
```

## Larry's Methodology (adapted for Villa Lithos)

### The Loop
```
Create Hook → Generate Slides → Post via Postiz → Track Analytics → 
Analyze Performance → Make Decision → Next Hook
```

### Decision Framework
| Views | Action |
|-------|--------|
| 50K+ | 🚀 VIRAL — make 3 variations immediately |
| 10K-50K | 🟢 STRONG — scale, increase frequency |
| 5K-10K | 🟡 GOOD — keep in rotation, test variations |
| 1K-5K | 🟠 DECENT — test 1 more variation |
| <1K (twice) | 🔴 DROP — try different category |

### Villa Lithos Adaptations
- **Real photos** instead of AI-generated images (villa photo bank)
- **Booking conversions** instead of app installs (profile visits → Airbnb clicks)
- **UK/EU audience** targeting (posting times optimized for GMT/BST)
- **Group travel** messaging (cost-per-person hook, squad/hen party/corporate angles)

## Quick Commands

### Check current status
```bash
cd villa-lithos-tiktok/larry-system/scripts
node check-villa-analytics.js --status
```

### Get next hook recommendation
```bash
node villa-daily-report.js --next-hook
```

### Generate full daily report
```bash
node villa-daily-report.js
```

### Post content (after slides are ready)
```bash
node post-villa.js --slides=../posts/2026-03-23/ --hook-id=hook-001 --caption="..." --platform=tiktok
```

### Dry run (test without posting)
```bash
node post-villa.js --slides=../posts/2026-03-23/ --hook-id=hook-001 --dry-run
```

## Setup Checklist

### ✅ Done
- [x] Villa Lithos config with property details
- [x] 10 hooks ready (1 with slides, 9 in queue)  
- [x] 3 hook variations with full 6-slide text sets
- [x] Hook performance tracking system
- [x] Decision framework (Larry's methodology)
- [x] Analytics integration scripts (Postiz API)
- [x] Daily intelligence reporting
- [x] Content pipeline with photo bank mapping
- [x] 48-hour pilot plan with timeline
- [x] Autonomous operation protocol
- [x] First carousel slides ready (final-1..6.png)

### 🔧 Needs Configuration (Yoni's action)
- [ ] **Postiz API key** → config/villa-lithos.json → `postiz.apiKey`
- [ ] **TikTok integration ID** → connect TikTok account in Postiz dashboard
- [ ] **Instagram integration ID** → connect @villa.lithos in Postiz
- [ ] **YouTube integration ID** (optional) → connect YouTube in Postiz

### 📋 To Get Postiz API Key
1. Sign up at https://postiz.pro
2. Connect TikTok, Instagram, YouTube accounts
3. Go to Settings → API Keys → Create
4. Note integration IDs from the integrations page
5. Paste into `config/villa-lithos.json`

## Hook Pipeline (10 ready)

| ID | Category | Text | Status |
|----|----------|------|--------|
| hook-001 | cost-split | "My friends think I'm rich..." | ✅ Slides ready |
| hook-002 | math-challenge | "I rented a 9-bedroom villa... guess how much?" | ✅ Slide texts ready |
| hook-003 | pov | "POV: luxury villa that sleeps 22, less than hotel" | ✅ Slide texts ready |
| hook-004 | conspiracy | "Hotels in Greece don't want you to see this" | ✅ Slide texts ready |
| hook-005 | airport-proximity | "15 min from landing to THIS pool" | 📝 Concept |
| hook-006 | amenity-tour | "Padel court, sauna, infinity pool AND fits 22" | 📝 Concept |
| hook-007 | vs-hotel | "I cancelled my Mykonos hotel for this" | 📝 Concept |
| hook-008 | corporate | "Instead of a boring conference room..." | 📝 Concept |
| hook-009 | fomo-urgency | "Only 12 weeks left for summer 2026" | 📝 Concept |
| hook-010 | bachelorette | "Forget Benidorm. Do your hen do HERE" | 📝 Concept |

## Integration with Existing Assets

This system uses:
- `villa-lithos-tiktok/slides/` — existing final slides (carousel #1)
- `workspace/villa-lithos/config.json` — Facebook page + photo URLs
- `workspace/villa-lithos/hook-variations-slides.json` — pre-written variations
- `state/VILLA_LITHOS_PROFILE.md` — property details
- `skills/larry-marketing/scripts/` — core Larry scripts (overlay, analytics API)

## Autonomous Operation (Phase 2+)

After pilot data (3+ posts with analytics):
1. Tali analyzes daily report automatically
2. Recommends next hook based on performance data
3. Generates slides + captions
4. Posts via Postiz as drafts
5. Yoni adds audio + publishes
6. Loop repeats with learning

---
*Built on Larry's Marketing Experiments v1.0.1*
*Configured for Villa Lithos by Tali, March 2026*
