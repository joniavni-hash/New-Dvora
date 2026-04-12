# Architecture Migration Blueprint
# Markdown Rules → Runtime Agent System
<!-- Status: Draft -->
<!-- Created: 2026-03-23 -->
<!-- Purpose: Complete migration plan from static rule files to runtime agent architecture -->

---

## Part 1: Current Architecture Mapping

### 1.1 System Overview — What We Have Now

```
┌─────────────────────────────────────────────────┐
│                   OpenClaw Runtime               │
│  ┌───────────────────────────────────────────┐   │
│  │            Dvorah (Main Agent)             │   │
│  │  - Reads markdown rules on every session   │   │
│  │  - Manually routes to sub-agents           │   │
│  │  - Interprets policies inline              │   │
│  │  - Makes all decisions via prompt logic    │   │
│  └──────────────┬────────────────────────────┘   │
│                 │                                 │
│    ┌────────────┼────────────────────┐            │
│    │            │                    │            │
│    ▼            ▼                    ▼            │
│  ┌──────┐  ┌────────┐  ┌────────────────┐        │
│  │אודיה │  │ צופית  │  │  מאשה (Legal)  │        │
│  │Group │  │Research│  │  + אתי (Auto)  │        │
│  └──────┘  └────────┘  └────────────────┘        │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │          Static File Layer                   │ │
│  │  AGENTS.md  SOUL.md  IDENTITY.md            │ │
│  │  PRINCIPLES.md  MEMORY_INDEX.md             │ │
│  │  core/*.md  policies/*.md  state/*.md       │ │
│  │  integrations/*.md  memory/*.md             │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 1.2 Current Components

| Component | Type | Location | Role |
|-----------|------|----------|------|
| **Dvorah** | Main agent | Boot chain + SOUL.md | Central brain — routes, decides, executes |
| **אודיה (Odya)** | Sub-agent prompt | `agents/group_agent_prompt.md` | WhatsApp group message analysis |
| **צופית (Tzofit)** | Sub-agent prompt | `agents/research_agent_prompt.md` | Deep research with tool use |
| **מאשה (Masha)** | Sub-agent prompt | `agents/legal-agent/` (6 files) | Legal analysis, contract review |
| **אתי (Eti)** | Sub-agent prompt | `agents/automation_agent_prompt.md` | Automation planning |
| **Orchestrator Flow** | Static markdown | `core/orchestrator_flow.md` | 11-step request processing |
| **Policy Engine** | Static markdown | `core/policy_engine.md` | Domain → policy mapping |
| **Approval Gate** | Static markdown | `core/approval_gate.md` | Action classification & approval |
| **Context Loader** | Static markdown | `core/context_loader.md` | Domain → context file mapping |
| **QA Layer** | Static markdown | `core/qa_layer.md` | 6-check quality gate |
| **Trace Logger** | Static markdown | `core/trace_logger.md` | Action audit trail |
| **Agent Contract** | Static markdown | `core/agent_contract.md` | Standard I/O interface |
| **Scripts** | Python | `scripts/*.py` | Runtime logic (metrics, health, group context, legal) |

### 1.3 Current Flow (Per Request)

```
Message In
    │
    ▼
AGENTS.md boot chain (load 5-7 files)
    │
    ▼
Dvorah reads orchestrator_flow.md mentally
    │
    ▼
1. INTAKE — identify source
2. CONTEXT — scan state/ + memory/ (manual)
3. CLASSIFY — intent + domain + action type
4. POLICY — load relevant policies (manual lookup)
5. ROUTE — decide which agent (if any)
6. INVOKE — sessions_spawn with assembled prompt
7. QA — check output (mental checklist)
8. APPROVE — approval gate logic (mental)
9. EXECUTE — send/act
10. WRITEBACK — memory/state updates
11. TRACE — log action
```

### 1.4 Current Weaknesses

| Issue | Impact | Severity |
|-------|--------|----------|
| **Every step is prompt-interpreted** | Inconsistency between sessions | High |
| **Boot chain loads 5-7 files minimum** | Token waste, slow startup | Medium |
| **Policy enforcement is honor-system** | No runtime enforcement | High |
| **No real service boundaries** | Dvorah is god-object | High |
| **Agents are just prompt templates** | No state, no persistence, no learning | Medium |
| **Orchestration is re-read every request** | Same rules re-parsed constantly | Medium |
| **No real approval queue** | `state/approvals/` is empty — unused | Medium |
| **Trace logging is sparse** | Only 1 trace file exists | Medium |
| **Scripts exist but aren't integrated** | `masha_mvp.py`, `legal_intent_classifier.py` partly wired | Low |
| **Context loading is manual** | Dvorah decides what to load — sometimes wrong | Medium |

---

## Part 2: Target Architecture Design

### 2.1 Architecture Vision

```
┌──────────────────────────────────────────────────────────────┐
│                        OpenClaw Runtime                       │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   ORCHESTRATOR SERVICE                    │ │
│  │  - Request routing (deterministic, not prompt-guessed)   │ │
│  │  - Agent lifecycle management                            │ │
│  │  - Policy enforcement (runtime, not honor-system)        │ │
│  │  - Context assembly (automated)                          │ │
│  │  - Approval workflow management                          │ │
│  └────────┬──────────┬──────────┬──────────┬───────────────┘ │
│           │          │          │          │                   │
│     ┌─────┘    ┌─────┘    ┌─────┘    ┌─────┘                 │
│     ▼          ▼          ▼          ▼                        │
│  ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐                   │
│  │אודיה │ │ צופית  │ │ מאשה   │ │ אתי    │  ← Agents        │
│  │Group │ │Research│ │ Legal  │ │ Auto   │                   │
│  │Agent │ │ Agent  │ │ Agent  │ │ Agent  │                   │
│  └──┬───┘ └───┬────┘ └───┬────┘ └───┬────┘                   │
│     │         │          │          │                         │
│  ┌──┴─────────┴──────────┴──────────┴──┐                     │
│  │         SHARED SERVICES LAYER        │                     │
│  │                                      │                     │
│  │  ┌──────────┐  ┌─────────┐          │                     │
│  │  │ Approval │  │   QA    │          │                     │
│  │  │ Service  │  │ Service │          │                     │
│  │  └──────────┘  └─────────┘          │                     │
│  │  ┌──────────┐  ┌─────────┐          │                     │
│  │  │ Memory   │  │  Trace  │          │                     │
│  │  │ Service  │  │ Service │          │                     │
│  │  └──────────┘  └─────────┘          │                     │
│  │  ┌──────────┐  ┌─────────┐          │                     │
│  │  │ Context  │  │ Policy  │          │                     │
│  │  │ Service  │  │ Service │          │                     │
│  │  └──────────┘  └─────────┘          │                     │
│  └──────────────────────────────────────┘                     │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    DVORAH (Main Agent)                    │ │
│  │  Now: personality + judgment + user interface             │ │
│  │  NOT: routing, policy lookup, context assembly            │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Key Architectural Shifts

| From (Current) | To (Target) | Why |
|-----------------|-------------|-----|
| Dvorah reads rules and routes | Orchestrator routes deterministically | Consistency, speed |
| Policies are "please follow" | Policy Service enforces at runtime | No drift |
| Context loading is manual | Context Service assembles automatically | No missed files |
| QA is a mental checklist | QA Service runs structured checks | No skips |
| Approval is prompt-interpreted | Approval Service tracks state | Real workflow |
| Trace logging is optional | Trace Service logs everything | Debugging, audit |
| Memory writes are ad-hoc | Memory Service with gates | Data integrity |
| Agents are prompt-only | Agents with persistent config | Reliability |

### 2.3 Dvorah's New Role

**Before:** God-object that reads rules, routes, loads context, checks QA, enforces policy, traces, decides, and responds.

**After:** Personality layer + judgment layer + user interface.

Dvorah focuses on:
- Being Dvorah (tone, style, personality from SOUL.md)
- Making judgment calls the Orchestrator can't (ambiguous requests)
- Communicating with Yoni
- Final approval on sensitive actions
- Overriding agent recommendations when judgment says so

Dvorah does NOT:
- Manually look up which policy to load
- Manually assemble context
- Manually run QA checklists
- Manually log traces
- Route requests by re-reading orchestrator_flow.md

---

## Part 3: Service Specifications

### 3.1 Orchestrator Service

**File:** `core/orchestrator.md` (replaces `orchestrator_flow.md`)

**Purpose:** Deterministic request routing and agent lifecycle.

**Input:** Raw message/request + source metadata

**Process:**
```
1. CLASSIFY — Deterministic intent + domain detection
   - Use keyword matching from CAPABILITY_INDEX.md
   - Use legal_intent_detection.md patterns
   - Use group detection from KNOWN_GROUPS.md
   - Output: { intent, domain, actionType, confidence }

2. ROUTE — Based on classification
   - domain=group → WhatsAppGroupAgent
   - domain=legal → LegalAgent
   - domain=research → ResearchAgent
   - domain=automation → AutomationAgent
   - domain=simple → Dvorah direct
   - confidence < 0.7 → Dvorah decides

3. ASSEMBLE — Invoke Context Service + Policy Service
   - Context Service returns relevant files
   - Policy Service returns constraints
   - Combine into agent task prompt

4. INVOKE — Spawn agent with assembled task
   - Use agent_contract.md format
   - Set model per MODEL_ROUTING_POLICY

5. RECEIVE — Get agent output
   - Invoke QA Service
   - Invoke Approval Service
   - Pass to Dvorah for final review if needed

6. EXECUTE — Based on approval
   - Invoke Memory Service for writes
   - Invoke Trace Service for logging
   - Return result to Dvorah for delivery
```

**Key Change:** Steps 1-3 are deterministic lookup, not LLM interpretation. The Orchestrator is a **decision tree with fallback to Dvorah**, not a prompt that hopes the LLM follows the rules.

### 3.2 WhatsApp Group Agent (אודיה)

**File:** `agents/group_agent_prompt.md` (enhanced)

**Current State:** Single prompt template. Dvorah manually assembles context and spawns.

**Target State:** Dedicated runtime agent with:

```yaml
agent: WhatsAppGroupAgent
name: אודיה (Odya)
trigger:
  - source: whatsapp_group
    condition: message.groupId in KNOWN_GROUPS
domain: group
model: sonnet (default), opus (complex/sensitive)
auto_invoke: true  # Orchestrator auto-routes group messages

context_requirements:
  always:
    - state/KNOWN_GROUPS.md (filtered to this group)
    - state/GROUP_MEMBERS.md (filtered)
  conditional:
    - state/GROUP_MEMORY.md (if group has memory)
    - state/OPEN_TASKS.md (if actionable intent)
  runtime:
    - last 10 messages (from channel)

policy_constraints:
  always:
    - GROUP_BEHAVIOR_POLICY (iron rules)
    - GROUP_INTELLIGENCE (scoring engine)
    - GROUP_QA (pre-send checks)
    - PRIVACY_POLICY
  conditional:
    - EXTERNAL_ACTIONS_POLICY (if actionable)

output_contract:
  format: agent_contract.md standard
  extra_fields:
    - shouldReply: boolean
    - replyMode: none|send|draft_to_yoni
    - score: 0-10
    - scoringBreakdown: string
    - intent: enum
    - suggestedReaction: string

approval_rules:
  role=observer: BLOCK (never send)
  role=responder+no_mention: BLOCK
  role=active+score<7: BLOCK
  role=active+score>=7: AUTO (Dvorah reviews)
  role=representative: AUTO (Dvorah reviews)
  draft_mode=true: REQUIRE_YONI

post_actions:
  - memory_update: if memoryDelta present, via Memory Service
  - task_tracking: if actionable, via state/OPEN_TASKS.md
  - trace: always, via Trace Service
```

**What Changes:**
- Context assembly is automatic (Context Service), not Dvorah guessing
- Policy enforcement is structural (approval rules table), not prompt hope
- Scoring thresholds are enforced, not suggested
- Post-actions happen automatically

### 3.3 Shared Services

#### 3.3.1 Approval Service

**File:** `core/approval_service.md`

**Replaces:** `core/approval_gate.md` (static rules) + empty `state/approvals/`

**How It Works:**

```
Classification (deterministic):
  READ  → auto-approve
  DRAFT → QA Service check → pass to Dvorah review
  SEND  → Dvorah approves (sensitive → Yoni approves)
  MUTATE → Dvorah only

State Management:
  Pending approvals stored in state/approvals/
  Format: YYYY-MM-DD_HH-MM_<type>_<target>.json
  Fields: { action, target, draft, status, requestedBy, requestedAt, decidedBy, decidedAt }

Escalation:
  - Unknown recipient → escalate to Yoni
  - External email → escalate to Yoni
  - Financial action → escalate to Yoni
  - Ambiguous classification → escalate to Dvorah
```

**Key Difference from Current:** Actually tracks approval state. Current system has the rules but doesn't use the state folder.

#### 3.3.2 QA Service

**File:** `core/qa_service.md`

**Replaces:** `core/qa_layer.md` (mental checklist)

**Structured Check Pipeline:**

```
Check 1: FACTUAL_FIT
  - Cross-reference claims against loaded context
  - Flag URLs not fetched by agent
  - Flag research answers without web_search usage
  → pass/fail + details

Check 2: STYLE_FIT
  - Match against group profile (formality, tone, emoji, length)
  - Match against Dvorah voice guidelines (IDENTITY.md)
  → pass/fail + details

Check 3: POLICY_FIT
  - Verify constraints from Policy Service were respected
  - Verify role allows action
  - Verify approval gate classification
  → pass/fail + details

Check 4: RISK_CHECK
  - Privacy scan: personal info leakage
  - Embarrassment scan: tone/content appropriateness
  - Conflict scan: intervention in disputes
  - Accuracy scan: confidence vs claims
  → pass/fail + risk_level

Check 5: MISSING_CONTEXT
  - Did agent guess where it should have known?
  - Is there context in memory/state that wasn't loaded?
  → pass/fail + what's missing

Check 6: WRONG_ACTION
  - Did agent use correct tools?
  - Does response match the question?
  - Did agent stay in scope?
  → pass/fail + details

Pipeline Logic:
  ALL pass → approve
  ANY fail → block + return failure details to Orchestrator
  Orchestrator decides: retry / edit / cancel
```

#### 3.3.3 Memory Service

**File:** `core/memory_service.md`

**Replaces:** Ad-hoc memory writes + `policies/MEMORY_POLICY.md` as guidance

**Responsibilities:**
- Gate all writes to `memory/` and `state/`
- Enforce MEMORY_POLICY rules (is this worth storing?)
- Prevent duplicate entries
- Maintain index consistency (MEMORY_INDEX.md)
- Handle corrections (CORRECTION_POLICY.md flow)

```
Write Request → Memory Service:
  1. Check: Does this match MEMORY_POLICY criteria?
     - Stable new fact? → allow
     - Repeated preference? → allow
     - New relationship? → allow
     - Active project change? → allow
     - Transient info? → reject
  
  2. Check: Duplicate?
     - Scan target file for similar content
     - If exists → update or skip
  
  3. Write with metadata:
     - timestamp
     - source (which agent/request)
     - category
  
  4. Update indexes if needed
```

#### 3.3.4 Context Service

**File:** `core/context_service.md`

**Replaces:** `core/context_loader.md` (static table) + manual loading

**How It Works:**

```
Input: { domain, intent, groupId?, keywords? }

Process:
  1. Load domain → files mapping from context_loader config
  2. Load always-required files (IDENTITY.md, current conversation)
  3. For group domain: filter KNOWN_GROUPS.md to specific group
  4. For legal domain: include attached documents
  5. Scan state/ filenames for relevance
  6. Trim large files to relevant sections
  
Output: { files: [...], totalTokens: N, warnings: [...] }

Budget: Target < 4K tokens of context per agent invocation
```

#### 3.3.5 Policy Service

**File:** `core/policy_service.md`

**Replaces:** `core/policy_engine.md` (lookup table)

**How It Works:**

```
Input: { domain, actionType, groupId? }

Process:
  1. Load domain → policies mapping
  2. Always include: ACTION_LEVELS, PRIVACY_POLICY
  3. Extract constraints as structured rules (not full file text)
  4. Return constraint set
  
Output: {
  constraints: [
    { rule: "no_observer_replies", applies: true, source: "GROUP_BEHAVIOR_POLICY" },
    { rule: "approval_required", level: "dvorah", source: "EXTERNAL_ACTIONS_POLICY" },
    ...
  ],
  policiesLoaded: ["GROUP_BEHAVIOR_POLICY", "PRIVACY_POLICY"]
}
```

**Key Difference:** Returns structured constraints, not raw markdown for the LLM to interpret.

#### 3.3.6 Trace Service

**File:** `core/trace_service.md`

**Replaces:** `core/trace_logger.md` (guidance only)

**Auto-logs:**
- Every agent invocation (model, tokens, duration)
- Every approval decision
- Every QA check result
- Every memory write
- Every external action (message sent, API call)

**Format:** `state/traces/YYYY-MM-DD.jsonl` (machine-readable, not markdown)

```json
{"ts":"2026-03-23T19:30:00Z","type":"agent_invoke","agent":"WhatsAppGroupAgent","model":"sonnet","domain":"group","trigger":"group_message","tokens":{"in":2400,"out":350},"duration_ms":3200}
{"ts":"2026-03-23T19:30:03Z","type":"qa_check","agent":"WhatsAppGroupAgent","results":{"factual":"pass","style":"pass","policy":"pass","risk":"pass","context":"pass","action":"pass"}}
{"ts":"2026-03-23T19:30:03Z","type":"approval","action":"send","level":"auto","target":"group:120363303184821917@g.us"}
{"ts":"2026-03-23T19:30:04Z","type":"action","kind":"message_sent","target":"group:פורטו על המפה","content_hash":"abc123"}
```

---

## Part 4: Migration Plan

### Phase 0: Foundation (No Breaking Changes)
**Duration:** 1-2 days
**Risk:** Zero — adds structure without changing behavior

| Step | Action | Impact |
|------|--------|--------|
| 0.1 | Create `architecture/` directory with this blueprint | Documentation |
| 0.2 | Create `core/services/` directory structure | Organization |
| 0.3 | Convert trace format: add JSONL alongside markdown | Better data |
| 0.4 | Activate `state/approvals/` — start actually tracking | Fill the gap |
| 0.5 | Add structured headers to all agent prompts (yaml config block) | Preparation |

### Phase 1: Service Extraction (Parallel to Current System)
**Duration:** 3-5 days
**Risk:** Low — new services run alongside, don't replace yet

| Step | Action | What Changes |
|------|--------|-------------|
| 1.1 | **Context Service** — implement as script (`scripts/context_service.py`) that returns context for a domain | Nothing yet — Dvorah can call it optionally |
| 1.2 | **Policy Service** — implement as structured constraint extractor | Nothing yet — produces constraints alongside current flow |
| 1.3 | **Trace Service** — implement JSONL logging alongside current markdown traces | Better logging immediately |
| 1.4 | **QA Service** — implement as structured checker that Dvorah invokes | Replaces mental checklist gradually |
| 1.5 | **Memory Service** — implement write gate as script | Dvorah calls before writes |

**Validation:** Run both old (manual) and new (service) paths. Compare results. Fix discrepancies.

### Phase 2: Orchestrator Bootstrap
**Duration:** 3-5 days
**Risk:** Medium — changes routing, but with fallback

| Step | Action | What Changes |
|------|--------|-------------|
| 2.1 | Create `core/orchestrator.md` v2 with deterministic routing rules | Dvorah uses new orchestrator |
| 2.2 | Implement classifier script (`scripts/request_classifier.py`) | Domain/intent detection before LLM |
| 2.3 | Wire Context Service + Policy Service into agent invocation | Automated context assembly |
| 2.4 | Wire QA Service into post-agent check | Structured QA replaces mental |
| 2.5 | Wire Trace Service into all actions | Full audit trail |

**Fallback:** If classifier confidence < 0.7, fall back to Dvorah's judgment (current behavior).

### Phase 3: Agent Hardening
**Duration:** 2-3 days
**Risk:** Low — agents already work, just adding structure

| Step | Action | What Changes |
|------|--------|-------------|
| 3.1 | Add yaml config blocks to all agent prompts | Machine-readable agent config |
| 3.2 | WhatsAppGroupAgent: integrate with Context Service (auto-load group profile) | No manual context assembly |
| 3.3 | LegalAgent: integrate legal_intent_classifier.py with Orchestrator | Auto-routing to Masha |
| 3.4 | ResearchAgent: add scope auto-detection | Better research quality |
| 3.5 | Standardize all agent output to strict agent_contract.md JSON | Consistent processing |

### Phase 4: Approval Workflow
**Duration:** 1-2 days
**Risk:** Low — formalizes what already exists informally

| Step | Action | What Changes |
|------|--------|-------------|
| 4.1 | Implement Approval Service with state tracking | Pending approvals are real |
| 4.2 | Wire SEND actions through Approval Service | All sends tracked |
| 4.3 | Implement escalation rules (→ Dvorah → Yoni) | Clear escalation path |
| 4.4 | Add approval state to trace logs | Full audit |

### Phase 5: Optimization & Polish
**Duration:** Ongoing
**Risk:** Low

| Step | Action | What Changes |
|------|--------|-------------|
| 5.1 | Reduce boot chain from 5-7 files to 2-3 (IDENTITY + SOUL + Orchestrator) | Faster startup |
| 5.2 | Move policy content from full-text to structured constraints | Less tokens |
| 5.3 | Add metrics dashboard for agent performance | Visibility |
| 5.4 | Add agent health monitoring | Reliability |
| 5.5 | Consider SchedulingAgent, TravelAgent, DocumentAgent | Expansion |

---

## Part 5: Implementation Strategy

### 5.1 Core Principle: Shadow Mode

Every new component runs in **shadow mode** first:
1. New service runs alongside current behavior
2. Compare outputs
3. Fix discrepancies
4. Only then switch over

This ensures **zero disruption** to current WhatsApp, email, and group functionality.

### 5.2 What NOT to Change

| Component | Status | Reason |
|-----------|--------|--------|
| SOUL.md | Keep as-is | Dvorah's identity — core, not infrastructure |
| IDENTITY.md | Keep as-is | External contract |
| PRINCIPLES.md | Keep as-is | Decision framework — still valid |
| Agent prompts (content) | Keep as-is | The prompts work — just add config headers |
| Memory/state data | Preserve all | No data migration needed |
| Scripts | Keep + extend | Already runtime — good foundation |
| Integrations | Keep as-is | External system configs don't change |

### 5.3 What Changes

| Component | From | To |
|-----------|------|-----|
| `core/orchestrator_flow.md` | 11-step mental checklist | Deterministic router + fallback |
| `core/policy_engine.md` | Lookup table in markdown | Structured constraint service |
| `core/context_loader.md` | Manual file list | Automated context assembly |
| `core/qa_layer.md` | Mental checklist | Structured check pipeline |
| `core/approval_gate.md` | Rules without state | Stateful approval workflow |
| `core/trace_logger.md` | Guidance + sparse logs | Auto-logging JSONL |
| `AGENTS.md` boot chain | Load 5-7 files every time | Load 2-3 + let Orchestrator handle rest |

### 5.4 File Structure After Migration

```
workspace/
├── IDENTITY.md              ← unchanged
├── SOUL.md                  ← unchanged
├── PRINCIPLES.md            ← unchanged
├── AGENTS.md                ← simplified: boot + Orchestrator pointer
├── MEMORY_INDEX.md          ← maintained by Memory Service
├── CAPABILITY_INDEX.md      ← unchanged (used by Orchestrator)
│
├── core/
│   ├── orchestrator.md      ← NEW: deterministic router spec
│   ├── agent_contract.md    ← unchanged
│   ├── legal_intent_detection.md ← unchanged
│   │
│   └── services/            ← NEW
│       ├── approval_service.md
│       ├── qa_service.md
│       ├── memory_service.md
│       ├── context_service.md
│       ├── policy_service.md
│       └── trace_service.md
│
├── agents/
│   ├── group_agent_prompt.md      ← add yaml config header
│   ├── research_agent_prompt.md   ← add yaml config header
│   ├── automation_agent_prompt.md ← add yaml config header
│   └── legal-agent/               ← unchanged internally
│
├── policies/                ← unchanged (Policy Service reads them)
├── state/                   ← unchanged (services write here)
├── memory/                  ← unchanged (Memory Service gates writes)
├── integrations/            ← unchanged
├── runbooks/                ← unchanged
├── templates/               ← unchanged
│
└── scripts/
    ├── context_service.py   ← NEW
    ├── policy_service.py    ← NEW
    ├── request_classifier.py ← NEW
    ├── (existing scripts)   ← unchanged
    └── ...
```

### 5.5 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| New routing breaks group messages | Shadow mode: run old + new, compare before switching |
| QA Service too strict | Start permissive, tighten gradually |
| Context Service misses files | Compare against Dvorah's manual loading for 1 week |
| Approval Service blocks legitimate actions | Default to current behavior, service logs only initially |
| Token costs increase | Context Service has budget cap (4K tokens target) |
| Agents produce inconsistent output | Agent contract is already defined — enforce strictly |

### 5.6 Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Boot chain files loaded | 5-7 | 2-3 |
| Context tokens per agent call | Unknown (no tracking) | < 4K measured |
| QA checks actually run | 0 (mental) | 6 structured checks |
| Trace coverage | ~10% of actions | 100% of external actions |
| Approval state tracked | 0% | 100% of SEND/MUTATE |
| Group message response accuracy | Good but inconsistent | Consistent + auditable |
| Time to first response | Variable | Measurable via traces |

---

## Part 6: Implementation Order (Recommended)

```
Week 1:
  Day 1-2: Phase 0 (foundation, no risk)
  Day 3-5: Phase 1.1-1.3 (Context, Policy, Trace services)

Week 2:
  Day 1-2: Phase 1.4-1.5 (QA, Memory services)
  Day 3-5: Phase 2.1-2.3 (Orchestrator bootstrap)

Week 3:
  Day 1-2: Phase 2.4-2.5 (wire services)
  Day 3-4: Phase 3 (agent hardening)
  Day 5: Phase 4 (approval workflow)

Week 4+:
  Phase 5 (optimization, expansion)
```

---

## Appendix A: Agent Config Block Format

To be added as yaml header to each agent prompt:

```yaml
# Agent Configuration
---
name: אודיה (Odya)
role: WhatsAppGroupAgent
domain: group
model_default: sonnet
model_complex: opus
auto_invoke: true
trigger:
  source: whatsapp_group
  condition: groupId in KNOWN_GROUPS

context:
  always: [state/KNOWN_GROUPS.md, state/GROUP_MEMBERS.md]
  conditional:
    actionable: [state/OPEN_TASKS.md]
    memory_needed: [state/GROUP_MEMORY.md]
  runtime: [last_10_messages]

policies:
  always: [GROUP_BEHAVIOR_POLICY, GROUP_INTELLIGENCE, GROUP_QA, PRIVACY_POLICY]
  conditional:
    external_action: [EXTERNAL_ACTIONS_POLICY]

approval:
  observer: BLOCK
  responder_no_mention: BLOCK
  active_low_score: BLOCK
  active_high_score: AUTO_DVORAH
  representative: AUTO_DVORAH
  draft_mode: REQUIRE_YONI

output_extras: [shouldReply, replyMode, score, scoringBreakdown, intent, suggestedReaction]
---
```

## Appendix B: Orchestrator Decision Tree

```
INPUT: message + source metadata

IF source = whatsapp_group:
  group = lookup(KNOWN_GROUPS, groupId)
  IF group not found → SILENCE
  IF group.role = observer → SILENCE
  → ROUTE to WhatsAppGroupAgent

IF source = whatsapp_dm OR source = direct:
  IF contains legal keywords (legal_intent_detection) → ROUTE to LegalAgent
  IF contains research request → ROUTE to ResearchAgent
  IF contains automation request → ROUTE to AutomationAgent
  IF simple (question, command, chat) → DVORAH DIRECT
  IF ambiguous → DVORAH DECIDES

IF source = heartbeat:
  → Execute heartbeat tasks per HEARTBEAT.md

IF source = subagent_return:
  → Process through QA → Approval → Execute
```

## Appendix C: Compatibility Matrix

| Existing Feature | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|-----------------|---------|---------|---------|---------|---------|
| WhatsApp groups | ✅ | ✅ | ✅ | ✅+ | ✅+ |
| DM conversations | ✅ | ✅ | ✅ | ✅ | ✅ |
| Legal analysis (Masha) | ✅ | ✅ | ✅ | ✅+ | ✅+ |
| Research (Tzofit) | ✅ | ✅ | ✅ | ✅+ | ✅+ |
| Memory writes | ✅ | ✅ | ✅ | ✅ | ✅+ |
| Email integration | ✅ | ✅ | ✅ | ✅ | ✅ |
| Home automation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fitness tracking | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ = works as today | ✅+ = works better with new architecture
