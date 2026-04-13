# Google Ads

## Status
Connected (campaign paused)

## Purpose
Google Ads campaign management — reporting, pausing/enabling campaigns, keyword management.

## Account
- Customer ID: 5627405650
- MCC (Login Customer ID): 7395869307
- Campaign: Villa Lithos - Europe USA - Summer 2026 (ID: 23619869176)
- Ad Group: Large villas (ID: 194291769837)
- Current Status: PAUSED (paused 20.3.2026 — מצב ביטחוני)

## Credentials
All credentials in `/home/ubuntu/.openclaw/.env` (prefixed `GOOGLE_ADS_*`):
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- `GOOGLE_ADS_CUSTOMER_ID`
- `GOOGLE_ADS_MCC_ID`

## Script
`scripts/google_ads_report.py` — loads credentials from `/home/ubuntu/.openclaw/.env`, generates report and sends via WhatsApp.
- Fixed 22.3.2026: migrated from hardcoded REDACTED values to /home/ubuntu/.openclaw/.env
- ⚠️ Running `python3 scripts/google_ads_report.py` sends the report to WhatsApp automatically (no dry-run mode)

## Allowed Actions
- View campaign performance
- Pause/enable campaigns (with explicit approval)
- Modify keywords and bids (with explicit approval)
- Generate reports

## Campaign History
- 16.3.2026: Baseline — 13 impressions, 2 clicks, $0.93. Added 48 keywords.
- 16-20.3.2026: Performance surged — 2,332 impressions/week, 157 clicks, CTR 6.7%, $107/week
- 20.3.2026: Campaign paused per Yoni's request (security situation)
- MTD at pause: 12,005 impressions, 810 clicks, 65 conversions, ₪1,028

## Strategy
- Maximize Clicks, max CPC $2
- Daily budget cap: $50

## Monitoring
HEARTBEAT.md weekly check — currently suspended while campaign is paused.
