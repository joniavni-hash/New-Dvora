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
Stored in secrets only (MS_GRAPH_CLIENT_SECRET).
Auth method: client_credentials flow via Microsoft Graph API.
**Azure client secrets expire periodically** — if auth fails, it may just need renewal.

## Fallback for reading emails
If Graph API auth fails (secret expired / missing / 401):
1. **Try Gmail MCP tools** (`gmail_search_messages` / `gmail_read_message`) as degraded fallback
2. Gmail covers Joni.avni@gmail.com — not the same mailbox, but better than nothing
3. Report the Outlook failure as a side note, not a blocker
4. See `runbooks/EMAIL_REVIEW.md` for full fallback chain

## Operational notes
Use configured Microsoft Graph access.
Always try auth live — don't rely on cached `state/health_check.json` status.
Execution details belong in runbooks, not here.
