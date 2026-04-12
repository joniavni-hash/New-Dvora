# Analytics & Feedback Loop

## Performance Tracking

### Postiz Analytics API

**Platform analytics** (followers, views, likes, comments, shares over time):
```
GET https://api.postiz.com/public/v1/analytics/{integrationId}
Authorization: {apiKey}
```

Response:
```json
[
  { "label": "Followers", "percentageChange": 2.4, "data": [{ "total": "1250", "date": "2025-01-01" }] },
  { "label": "Views", "percentageChange": 4, "data": [{ "total": "5000", "date": "2025-01-01" }] },
  { "label": "Total Likes", "data": [{ "total": "6709", "date": "2026-02-15" }] },
  { "label": "Recent Likes", "data": [{ "total": "6354", "date": "2026-02-15" }] },
  { "label": "Recent Comments", "data": [{ "total": "148", "date": "2026-02-15" }] },
  { "label": "Recent Shares", "data": [{ "total": "119", "date": "2026-02-15" }] }
]
```

### Per-Post Analytics

**Individual post performance**:
```
GET https://api.postiz.com/public/v1/analytics/post/{postId}
Authorization: {apiKey}
```

## Daily Feedback Loop

### Decision Framework

**High views + High conversions** → 🟢 SCALE IT
- Make 3 variations of winning hook
- Test different posting times  
- Cross-post to more platforms
- Don't change the CTA

**High views + Low conversions** → 🟡 FIX THE CTA
- Hook works, CTA is broken
- Test different CTAs on slide 6
- Check app landing page alignment
- The hook is gold — don't touch it

**Low views + High conversions** → 🟡 FIX THE HOOKS
- Content converts, not enough eyeballs
- Test radically different hooks
- Keep CTA and structure identical
- Focus on first slide/thumbnail

**Low views + Low conversions** → 🔴 FULL RESET
- Neither hook nor conversion working
- Try completely different format
- Research trending content NOW
- Test new hook categories

### Hook Performance Tracking

Track in `tiktok-marketing/hook-performance.json`:
```json
{
  "hooks": [
    {
      "postId": "postiz-id",
      "text": "My boyfriend said our flat looks like a catalogue",
      "date": "2026-02-15",
      "views": 45000,
      "likes": 1200,
      "comments": 45,
      "shares": 89,
      "conversions": 4,
      "cta": "Download App — link in bio"
    }
  ],
  "rules": {
    "doubleDown": ["person-conflict-ai"],
    "testing": ["listicle", "pov-format"], 
    "dropped": ["self-complaint", "price-comparison"]
  }
}
```

### Decision Rules
- 50K+ views → DOUBLE DOWN — make 3 variations
- 10K-50K → Good — keep in rotation
- 1K-10K → Try 1 more variation  
- <1K twice → DROP — try something different