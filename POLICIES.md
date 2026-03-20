# Policies
<!-- Status: Overview -->
<!-- Purpose: Policy index and action level categories -->
<!-- Authority: Summary only. See policies/* for detailed rules -->

For detailed policies, see individual files in `policies/`.
This file defines action level categories only.

## Action Levels

### READ
Safe to execute without approval

### DRAFT
Create output but do not send

### SEND
Requires explicit approval

### MUTATE
Requires explicit approval and confirmation

## Rules

- Never send messages without approval
- Never modify external systems without approval
- Always log intended actions
