# Google Analytics GA4

## Status
Connected

## Purpose
Website analytics and performance tracking — sessions, users, conversions, traffic sources.

## Account
- Property ID: 525610597 (Villa Lithos website)
- Connected: 16.3.2026 (baseline data captured)
- Scope: https://www.googleapis.com/auth/analytics.readonly

## Credentials
All credentials in `secrets/.env` (prefixed `GOOGLE_ANALYTICS_*`):
- `GOOGLE_ANALYTICS_PROPERTY_ID`
- `GOOGLE_ANALYTICS_CLIENT_ID`
- `GOOGLE_ANALYTICS_CLIENT_SECRET`
- `GOOGLE_ANALYTICS_REFRESH_TOKEN`

## Available Data
- Real-time active users
- Sessions and page views
- Traffic sources (organic, paid, direct, referral)
- Popular pages and content
- User demographics and behavior
- Goal completions and conversions
- Device and browser statistics
- Geographic data

## Common Queries
- Daily/weekly/monthly traffic trends
- Top traffic sources for booking conversions
- Popular villa content pages
- Mobile vs desktop usage
- Geographic distribution of visitors
- Seasonal traffic patterns

## Integration with Villa Marketing
- Cross-reference with Google Ads campaign performance
- Track booking funnel completion rates
- Monitor SEO performance for "villa Greece" keywords
- Analyze social media referral traffic
- Measure email campaign effectiveness

## Data Freshness
- Real-time data: immediate
- Standard reports: 24-48 hours delay
- Custom dimensions: up to 24 hours

## API Limitations
- 100,000 requests per day per project
- 10 queries per second per property
- Read-only access (no data modification)

## Security
- OAuth 2.0 with refresh token
- Scoped to analytics.readonly only
- No write permissions to GA4 property
- Credentials stored securely in secrets/.env