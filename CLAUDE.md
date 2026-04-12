# New-Dvora

WhatsApp bot powered by Claude ACP agent in non-interactive background mode.

## Problem Solved

ACP `sessions_spawn` fails in background mode because:
1. **Thread/session mode** - can't bind to a WhatsApp conversation
2. **Run mode** - requires interactive approval prompts not available in background

## Solution Architecture

Instead of `sessions_spawn`, we use:
- **`--print` mode** (CLI) - single-shot request/response, no session binding needed
- **`--permission-mode accept-edits-and-execution`** - pre-approves all tool usage
- **SDK `permissionCallback`** - auto-approves tools programmatically when SDK is available
- **Environment vars `CI=true`** - forces non-interactive behavior at system level

## Files

- `.claude/settings.json` - Pre-approved permissions (no interactive prompts)
- `src/agent-runner.js` - Spawns agent in non-interactive background mode
- `src/whatsapp-handler.js` - Express server handling WhatsApp webhooks

## Running

```bash
npm install
npm start
```

## Environment Variables

Copy `.env.example` to `.env` and configure your WhatsApp API credentials.
