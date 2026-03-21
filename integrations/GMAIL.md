# Gmail

## Status
Connected (refreshed 20.3.2026)

## Purpose
Gmail access via GOG CLI — read, search, send, manage labels.

## Accounts
### Joni.avni@gmail.com
- Services: gmail, calendar, chat, classroom, drive, docs, slides, contacts, tasks, sheets, people, forms, appscript
- Auth: OAuth via GOG
- Status: Active

### dvora.officepa@gmail.com
- Services: gmail, calendar, drive, contacts, docs, sheets
- Auth: OAuth via GOG
- Status: Active

## Tool
GOG CLI: `GOG_KEYRING_PASSWORD=openclaw gog gmail ...`

## Allowed Actions
- Search and read emails
- Send emails (with explicit approval)
- Manage labels
- Access Calendar, Drive, Sheets, Docs, Contacts, Tasks

## Notes
- Gmail is NOT the default for email — Outlook is
- Use Gmail only when Yoni asks explicitly, or for specific flows (e.g. pending-tehila invoices)
- Tokens expire periodically — refresh with `gog auth add <email> --remote`
