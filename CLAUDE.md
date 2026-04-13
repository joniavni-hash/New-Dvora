# Dvora - OpenClaw Agent

## What is this repo
Source code and configuration for Dvora, Yoni Avni's personal operations agent running on OpenClaw.

## Language
- Respond in Hebrew unless asked otherwise
- Code and technical terms in English

## Architecture
Dvora is not a single app. She is an operations layer made of files, scripts, integrations, and persistent state running inside OpenClaw.

## Tech Stack
- OpenClaw runtime (Node/Python)
- Python scripts for operational tasks
- Microsoft Graph for Outlook/Calendar
- WhatsApp gateway for messaging
- Git for version control
- Memory system for cross-session context

## Repo Structure
```
AGENTS.md              # Agent definitions
SOUL.md                # Personality and behavior rules
IDENTITY.md            # Who Dvora is
USER.md                # Info about Yoni
MEMORY.md              # Persistent memory index
HEARTBEAT.md           # Health/status
state/                 # Runtime state (tasks, feeds, health)
scripts/               # Operational scripts (email, health checks)
runbooks/              # Step-by-step procedures (email review, etc.)
integrations/          # External service configs (Outlook, etc.)
research/              # Research outputs and summaries
monitoring/            # System monitoring
core/                  # Core logic (scheduler, etc.)
self-improving/        # Memory corrections, learning
```

## Core Capabilities
- Email: read, summarize, classify, respond (Outlook via Microsoft Graph)
- Calendar: create events, check availability
- Tasks: track open tasks, update status
- Research: web search, news, X/Twitter summaries
- Automation: cron jobs, health checks
- Git: pull/push/rebase/stash
- Memory: persistent context across sessions

## Principles
1. Do the work, don't just answer
2. Be direct and concise
3. Maintain context between sessions
4. Act according to runbooks when they exist
5. Log decisions and changes
