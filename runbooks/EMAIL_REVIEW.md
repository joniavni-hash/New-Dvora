# Email Review Runbook

## Trigger
Daily or on-demand

## Steps
1. Fetch unread emails from Outlook via Microsoft Graph
2. Classify by urgency: urgent / needs response / FYI / ignore
3. Summarize urgent items
4. Draft responses where possible
5. Update state/OPEN_TASKS.md with action items
6. Report summary to Yoni
