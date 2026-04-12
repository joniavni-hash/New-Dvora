# Vercel

## Status
Connected

## Purpose
Dashboard hosting and deployment.

## Account
- User: joniavni-7035 (Joni.avni@gmail.com)
- Project: vercel-dashboard (vercel-dashboard-two-ruby.vercel.app)

## Credentials Location
- CLI: ~/.local/share/com.vercel.cli/auth.json
- Push token: secrets/.env (DASHBOARD_PUSH_TOKEN)
- Blob store: dvorah-blob (store_HmpM1PBtwLfJhlCm)

## Cron
- dashboard_push.py runs every 2 minutes via crontab
- Pushes workspace data to Vercel Blob → dashboard fetches it

## Allowed Actions
- Deploy projects
- Manage environment variables
- Push dashboard data

## Notes
- BLOB_READ_WRITE_TOKEN set in Vercel project env vars
