# Agent Architecture — Dvorah v2
<!-- Status: Draft -->
<!-- Created: 22.3.2026 -->
<!-- Purpose: Lean sub-agent architecture plan -->

## Current State

### What exists
- **Orchestrator**: Dvorah (main agent) — handles all routing, decisions, tool use
- **Policies**: 14 files in policies/ — GROUP_BEHAVIOR, EXTERNAL_ACTIONS, MEMORY, PRIVACY, etc.
- **Memory**: MEMORY_INDEX.md → memory/, state/, corrections.md
- **Integrations**: 10 connected (Outlook, Google Ads, Gmail/GOG, WhatsApp, Vercel, GitHub, etc.)
- **Runbooks**: 7 operational playbooks
- **Monitoring**: metrics.py, health_check.py, heartbeat tracker

### What works well
- Single-agent model handles most tasks
- Policies are written and mostly followed
- Memory and state are organized
- External actions have approval awareness

### What doesn't work well
- Long tasks block the conversation (e.g., email review = 5+ tool calls while Yoni waits)
- No parallel execution — everything is sequential
- Group message handling is in-context (heavy, expensive)
- Research tasks consume many tokens in main context
- No background processing capability

## Target Architecture (Lean)

```
Yoni → Dvorah (orchestrator)
           ├── direct response (simple tasks)
           ├── spawn → GroupAgent (WhatsApp group handling)
           ├── spawn → ResearchAgent (deep research, web, docs)
           └── spawn → CodeAgent (scripts, fixes, builds)
           
         ApprovalGate: all SEND/MUTATE actions return to Dvorah for approval
```

### What Dvorah keeps doing
- All routing and intent classification
- All approval decisions
- All memory writes
- All direct Yoni communication
- Simple tasks (reminders, quick answers, calculations)

### What gets delegated
- Heavy research (legal analysis, market research, document review)
- Group message analysis and draft responses
- Code tasks (script writing, debugging, deployment)

## POC Results (22.3.2026)

| Finding | Detail |
|---------|--------|
| Workspace access | Full — reads all files including secrets |
| Tools | All except sessions_spawn, memory_search |
| Model | Can specify per-spawn (sonnet for routine, opus for complex) |
| Cost | ~760 tokens for simple task — negligible |
| Latency | 20 seconds for simple task |
| Context | Does NOT inherit conversation — must be passed explicitly |
| Memory | Cannot search — orchestrator must provide relevant context |

## Phase 1: WhatsApp Group Agent (Week 1)

### Goal
When a group message arrives, spawn a sub-agent to analyze it and return a decision. Dvorah reviews and acts.

### Flow
```
1. Group message arrives → Dvorah
2. Dvorah spawns GroupAgent with:
   - The message
   - Group profile (from state/KNOWN_GROUPS.md)
   - Group memory (from state/GROUP_MEMORY.md) 
   - Group policy (from policies/GROUP_BEHAVIOR_POLICY.md)
   - Member context (from state/GROUP_MEMBERS.md)
3. GroupAgent returns:
   - shouldReply: yes/no
   - confidence: 0-1
   - reasoning: why
   - draftReply: text (if yes)
   - memoryUpdate: what to remember (if anything)
4. Dvorah reviews:
   - If shouldReply=no → silent
   - If shouldReply=yes → review draft → send or edit
   - If memoryUpdate → write to state
```

### What to build
1. **Group agent task template** — structured prompt with all context slots
2. **Context assembler** — function that pulls relevant group files and formats them
3. **Response parser** — extract structured decision from agent output
4. **Integration into message flow** — detect group message → spawn instead of handling inline

### What NOT to build
- Separate PolicyEngine module (policies are files, agent reads them)
- Separate MemoryService (memory is files, orchestrator manages writes)
- Separate TraceLogger (use existing metrics + corrections)
- TriggerScorer with 12 features (start with simple rules, learn from corrections)

## Phase 2: Research Agent (Week 2)

### Goal
When Yoni asks something that requires deep research (web search, document analysis, cross-referencing), spawn a sub-agent.

### Flow
```
1. Yoni asks complex question → Dvorah recognizes research need
2. Dvorah spawns ResearchAgent with:
   - The question
   - Relevant context from memory
   - Specific instructions (what to search, what to analyze)
3. ResearchAgent returns:
   - Summary
   - Sources
   - Confidence level
   - Open questions
4. Dvorah reviews → delivers to Yoni
```

## Phase 3: Expand Based on Learnings (Week 3)

- Review what worked and what didn't
- Write contracts/interfaces based on actual experience
- Add CodeAgent if needed
- Formalize ApprovalGate rules

## ApprovalGate — Simple Version

Rules:
- Sub-agent returns DRAFT, never sends directly
- All external actions (email, WhatsApp, API calls) require Dvorah review
- Sub-agent can READ anything but cannot WRITE to state or memory
- Only Dvorah writes to memory/state after reviewing sub-agent output

Implementation: This is not code — it's enforced by the task prompt given to sub-agents:
"You are a research/analysis agent. Return your findings. Do NOT send messages, write files, or take external actions."

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Sub-agent sends message directly | Task prompt explicitly forbids it + limit tools via task instructions |
| Sub-agent reads secrets unnecessarily | Acceptable risk — same security boundary as main agent |
| Sub-agent gives wrong answer | Dvorah reviews all output before acting |
| Cost explosion | Use sonnet by default, opus only when specified |
| Latency too high | Sub-agent runs in parallel while Dvorah handles other messages |
| Context too large for sub-agent | Keep task prompts focused, include only relevant files |

## Files to Create/Modify

### Phase 1
- `agents/group_agent_prompt.md` — task template for group agent
- `policies/GROUP_BEHAVIOR_POLICY.md` — review and tighten for agent use
- `state/KNOWN_GROUPS.md` — ensure complete for context assembly

### No new code needed
The orchestration happens through sessions_spawn calls from Dvorah.
No separate modules, services, or engines required at this stage.

## Success Criteria

### Phase 1 done when:
- [ ] Group message → sub-agent → decision → Dvorah acts/silences
- [ ] At least 20 group messages handled by sub-agent
- [ ] No message sent without Dvorah approval
- [ ] Cost per group message < $0.01

### Phase 2 done when:
- [ ] Research question → sub-agent → summary → Dvorah delivers
- [ ] At least 5 research tasks completed
- [ ] Quality equal or better than Dvorah doing it inline
- [ ] Time-to-response faster (parallel execution)
