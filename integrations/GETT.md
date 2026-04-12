# Gett

## Status
Connected

## Purpose
שימוש ב-Gett Business להזמנת נסיעות, קבלת הצעות מחיר, ובדיקת סטטוס נסיעה.

## Available Accounts
### Account A
- Label: Dania Holdings
- Use case: נסיעות עסקיות / משפחתיות לפי הצורך
- Business ID: (from secrets: GETT_DANIA_BUSINESS_ID)
- Resource UUID: (from secrets: GETT_DANIA_RESOURCE_UUID)

### Account B
- Label: Yoni Avni
- Use case: נסיעות עבור יוני כעוסק מורשה
- Business ID: (from secrets: GETT_YONI_BUSINESS_ID)
- Resource UUID: (from secrets: GETT_YONI_RESOURCE_UUID)

## Allowed Actions
- get products
- get price estimate
- create ride order, with explicit approval
- get order details
- cancel ride, with explicit approval

## Approval Rules
- Estimates and availability checks: allowed
- Booking a ride: requires explicit approval
- Cancelling a ride: requires explicit approval

## Secret Handling
Credentials are never stored in memory files or tracked documents.
Load secrets only from local secure storage.

Expected secret names:
- GETT_DANIA_CLIENT_ID
- GETT_DANIA_CLIENT_SECRET
- GETT_DANIA_BUSINESS_ID
- GETT_DANIA_RESOURCE_UUID
- GETT_YONI_CLIENT_ID
- GETT_YONI_CLIENT_SECRET
- GETT_YONI_BUSINESS_ID
- GETT_YONI_RESOURCE_UUID

## Trigger Terms
- gett
- taxi
- cab
- ride
- order me a ride
- airport ride
- נסיעה
- מונית

## Notes
- Use this integration before asking whether ride ordering is connected.
- If account choice is ambiguous, ask which account to use.
- Do not print or summarize secrets.
