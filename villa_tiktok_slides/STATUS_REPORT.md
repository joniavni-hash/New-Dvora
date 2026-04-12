# Villa Lithos TikTok Posting — Status Report
**Date:** 2026-03-23 18:12

## Bottom Line
**Larry's system requires Postiz account setup — there's no bypass.** The entire pipeline (post → track → iterate) routes through Postiz API. Config has placeholder values (`POSTIZ_API_KEY_HERE`, `TIKTOK_INTEGRATION_ID`).

## What's Ready RIGHT NOW ✅
1. **6 TikTok slides created** — real villa photos, text overlays, 9:16 format
   - Location: `villa_tiktok_slides/final/slide-1.jpg` through `slide-6.jpg`
2. **Caption + hashtags written** — saved in `villa_tiktok_slides/final/caption.txt`
3. **Larry's full pipeline installed** — generate → overlay → post → analytics → iterate
4. **Villa config complete** — property profile, photo bank, hashtag strategy, posting schedule

## What's Blocking 🚫
**One thing: Postiz account not connected.**

Larry's `post-to-tiktok.js` posts exclusively via Postiz API. No fallback exists. The config has:
```
postiz.apiKey: "POSTIZ_API_KEY_HERE"
postiz.integrationIds.tiktok: "TIKTOK_INTEGRATION_ID"
```

### Why Can't We Bypass Postiz?
- TikTok has no public "upload video" API for personal accounts
- TikTok Content Posting API requires a registered app + OAuth approval (weeks)
- Browser automation on TikTok = instant ban (heavy bot detection)
- Postiz is the middleware that handles OAuth + posting + analytics

## Setup Needed (10-15 min, one time)
1. **Sign up at [postiz.pro](https://postiz.pro)** — get API key
2. **Connect TikTok account** in Postiz dashboard (OAuth flow, click-through)
3. **Update config:**
   ```
   villa-lithos-tiktok/larry-system/config/villa-lithos.json
   ```
   Fill in: `postiz.apiKey`, `postiz.integrationIds.tiktok`

After that — fully autonomous posting, analytics, and iteration.

## Alternative: Post Manually Right Now
The slides are ready. Yoni (or anyone) can:
1. Open TikTok app
2. Create slideshow post
3. Add the 6 images from `villa_tiktok_slides/final/`
4. Paste the caption from `caption.txt`
5. Add trending audio
6. Post

## Recommendation
Set up Postiz once → then Larry handles everything automatically going forward. The 15 minutes of setup unlocks fully autonomous daily posting with analytics-driven optimization.
