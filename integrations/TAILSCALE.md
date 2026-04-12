# Tailscale

## Status
Connected

## Purpose
VPN mesh network, Funnel for exposing local services.

## Node
- Hostname: desktop-19fiehm
- Tailscale IP: 100.68.24.112
- DNS: desktop-19fiehm.tail2cefa5.ts.net
- User: joni.avni@

## Active Funnels
- Port 443 → localhost:8899 (dashboard, currently also via Vercel)
- Port 8899 → localhost:8899

## Allowed Actions
- Serve/funnel local services
- Access Tailscale network

## Notes
- Useful for exposing services when Vercel/Cloudflare not suitable
- WSL runs Tailscale, Windows Chrome not directly accessible via Tailscale
