# Gett Business API

## Status
Connected

## Purpose
שימוש ב-Gett Business להזמנת נסיעות, קבלת הצעות מחיר, ובדיקת סטטוס נסיעה.

## Account
- Label: Dania Holdings
- Business ID: from secrets/gett.json
- Credentials: secrets/gett.json

## Authentication
- OAuth2 client_credentials flow
- POST https://business-api.gett.com/oauth/token
- Content-Type: application/json
- Body: {"grant_type":"client_credentials","client_id":"...","client_secret":"...","scope":"employee finance order"}
- Token expires in ~900 seconds, refresh before each session

## API Base
https://business-api.gett.com/v1

## Endpoints

### Get Products (vehicle types)
POST /v1/products?businessId={businessId}
Body: {"origin":{"lat":...,"lng":...},"destination":{"lat":...,"lng":...}}
Returns available products with product_id, name, ETA

### Book a Ride
POST /v1/orders?businessId={businessId}
Body includes: category, product_id, scheduled_at (optional for on-demand), stops array with origin/destination, each with location (lat/lng/address) and user (name/phone)
Phone format: international without + sign (e.g. 972552755547)

### Get Order Details
GET /v1/orders/{orderId}?businessId={businessId}

### Cancel Order
PUT /v1/orders/{orderId}/cancel?businessId={businessId}

## Default Passenger
- Name: Yoni Avni
- Phone: 972552755547

## Approval Rules
- Estimates and product checks: allowed without approval
- Booking a ride: requires explicit approval from Yoni
- Cancelling a ride: requires explicit approval from Yoni

## Trigger Terms
gett, taxi, cab, ride, מונית, נסיעה, הזמיני מונית, תזמיני לי נסיעה

## Notes
- Always get products first to find valid product_id for the area
- Do not hardcode product_ids, they can change
- For on-demand rides, omit scheduled_at
- For pre-booked rides, use ISO8601 format with timezone
