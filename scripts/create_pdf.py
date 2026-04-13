content = """Google Ads API Tool - Design Document

Overview
Villa Lithos is a vacation rental property in Porto Rafti, Greece.
This tool provides internal monitoring of Google Ads campaign performance.

Purpose
- Monitor campaign performance: impressions, clicks, cost, CTR
- Generate automated weekly performance reports
- Support data-driven budget decisions for the property owner

Users
Internal use only. Accessed by the property owner and their personal assistant.
No external or public access.

API Usage
- Read-only access to campaign metrics via Google Ads API
- Queries: campaigns, ad groups, keywords, performance metrics
- No automation of ad creation, bidding, or budget modifications
- Estimated API calls: fewer than 100 per day

Data Handling
- All data stored locally, never shared with third parties
- No user data collection
- Full compliance with Google Ads API Terms of Service

Villa Lithos | Porto Rafti, Greece | Internal Tool | March 2026
"""

with open('/home/ubuntu/.openclaw/workspace/google_ads_design_doc.txt', 'w') as f:
    f.write(content)
print('OK')
