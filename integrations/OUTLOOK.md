# OUTLOOK.md
Integration: Microsoft 365 Outlook
Owner: Yoni@grit-mind.com
Status: connected
Last verified: 2026-03-17
## Capabilities
- Read emails
- Send emails
- Read calendar
- Write calendar
## Default behavior
When Yoni says "emails" or "mailbox", default to Outlook unless he explicitly says Gmail.
## Auth
Auth method: client_credentials flow via Microsoft Graph API.
Secret: `MS_GRAPH_CLIENT_SECRET` — stored in `secrets/.env` or as environment variable.

### Azure client secret expiry
Azure AD client secrets expire. Default expiry is 6–24 months from creation.
**If auth fails — check the Azure Portal for secret expiry before assuming anything else is broken.**
When an expired secret is the cause, the Azure token endpoint returns `invalid_client` in the error response.

### Secret sources (checked in order)
1. Environment variable `MS_GRAPH_CLIENT_SECRET`
2. `/home/ubuntu/.openclaw/.env` (OpenClaw root env file)
3. `secrets/.env` file (key=value format, relative to workspace root)

### When auth fails
1. **Always try the API live** — don't rely on cached `state/health_check.json`
2. Check the error: is it `invalid_client` (expired secret) or network/timeout?
3. Report the specific error to Yoni — not just "can't authenticate"
4. If expired: "ה-secret של Outlook פג תוקף. צריך ליצור חדש ב-Azure Portal ולעדכן ב-secrets/.env"

## Operational notes
Use configured Microsoft Graph access.
Execution details belong in runbooks, not here.
