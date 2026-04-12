# Gett Business API Reference

## Base URL
`https://business-api.gett.com`

## Auth
- Token URL: `https://business-api.gett.com/oauth/token`
- Grant Type: client_credentials
- Scopes: order, finance, employee
- Token TTL: ~15 דקות (899 שניות)
- Docs: https://developer.gett.com/docs/introduction

## API Flow להזמנת נסיעה
1. **Get Products** — `POST /v1/products?businessId={UUID}` (body: origin, destination, scheduled_at)
2. **Price Estimate** — `POST /v1/price-estimate?businessId={UUID}` (body: origin, destination, stops, product_id, scheduled_at) → returns quote_id (valid 2 min)
3. **Create Order** — `POST /v1/orders?businessId={UUID}` (body: category, product_id, scheduled_at, quote_id, stops[], note_to_driver, references[])
4. **Company Settings** — `GET /v1/companies/settings?businessId={UUID}` (check mandatory fields)
5. **Order Details** — `GET /v1/orders/{orderId}?businessId={UUID}`
6. **Cancel Order** — per docs at /docs/cancel-order

## Order Body Structure (Single Passenger)
- category: "transportation" | "delivery"
- product_id: from Products response
- scheduled_at: ISO8601 (omit for on-demand)
- quote_id: from Price Estimate (required, valid 2 min)
- stops[]: [{type: "origin", actions: [{type: "pick_up", user: {name, phone}}], location: {lat, lng}}, {type: "destination", actions: [{type: "drop_off", user: {name, phone}}], location: {lat, lng}}]
- note_to_driver: string (optional, max 100 chars)
- Phone format: international without "+" (e.g. 972543333556)
- Header: X-Request-ID to prevent duplicates
- Address: lat/lng required. full_address optional but recommended
