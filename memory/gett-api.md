# Gett Business API

## חשבון עסקי — א. דניא אחזקות בע"מ
- **חברה:** א. דניא אחזקות בע"מ — החברה המשפחתית של יוני
- **Business ID:** `4896c7bf-d0f6-431f-a816-54697cc24a53`
- **Resource UUID:** `82e1b95a-8690-4c26-b45b-5465af3a1bd7`

### OAuth Credentials (חשבון דניא)
- **Token URL:** `https://business-api.gett.com/oauth/token`
- **Client ID:** `82e1b95a-8690-4c26-b45b-5465af3a1bd7.e9c0270e-2091-11f1-83e6-72f43255ea7d`
- **Client Secret:** `e9c01e21-2091-11f1-83e6-72f43255ea7d`
- **Scopes:** order, finance, employee
- **Grant Type:** client_credentials
- **Token TTL:** ~15 דקות (899 שניות)

### סטטוס API (18.3.2026)
- ✅ OAuth עובד
- ✅ API endpoints עובדים — Base URL: `https://business-api.gett.com`
- ✅ Docs: https://developer.gett.com/docs/introduction

### API Flow להזמנת נסיעה
1. **Get Products** — `POST /v1/products?businessId={UUID}` (body: origin, destination, scheduled_at)
2. **Price Estimate** — `POST /v1/price-estimate?businessId={UUID}` (body: origin, destination, stops, product_id, scheduled_at) → returns quote_id (valid 2 min)
3. **Create Order** — `POST /v1/orders?businessId={UUID}` (body: category, product_id, scheduled_at, quote_id, stops[], note_to_driver, references[])
4. **Company Settings** — `GET /v1/companies/settings?businessId={UUID}` (check mandatory fields)
5. **Order Details** — `GET /v1/orders/{orderId}?businessId={UUID}`
6. **Cancel Order** — per docs at /docs/cancel-order

### Order Body Structure (Single Passenger)
- category: "transportation" | "delivery"
- product_id: from Products response
- scheduled_at: ISO8601 (omit for on-demand)
- quote_id: from Price Estimate (required, valid 2 min)
- stops[]: [{type: "origin", actions: [{type: "pick_up", user: {name, phone}}], location: {lat, lng}}, {type: "destination", actions: [{type: "drop_off", user: {name, phone}}], location: {lat, lng}}]
- note_to_driver: string (optional, max 100 chars)
- Phone format: international without "+" (e.g. 972543333556)
- Header: X-Request-ID to prevent duplicates
- Address: lat/lng required. full_address optional but recommended

---

## חשבון עוסק מורשה — יוני אבני
- **Business ID:** `b7feb531-d9c2-4352-b0b9-aff646bb3213`
- **Resource UUID:** `82e1b95a-8690-4c26-b45b-5465af3a1bd7` (משותף עם דניא)

### OAuth Credentials (חשבון עוסק מורשה)
- **Token URL:** `https://business-api.gett.com/oauth/token`
- **Client ID:** `82e1b95a-8690-4c26-b45b-5465af3a1bd7.e242d763-2105-11f1-ad35-465d3cd79872`
- **Client Secret:** `e242d75b-2105-11f1-ad35-465d3cd79872`
- **Scopes:** order, employee, finance
- **Grant Type:** client_credentials

---

## מידע כללי
- **א. דניא אחזקות בע"מ** — חברה משפחתית של יוני אבני
- שני החשבונות חולקים את אותו Resource UUID
- שניהם עובדים ✅ (נבדק 18.3.2026)
