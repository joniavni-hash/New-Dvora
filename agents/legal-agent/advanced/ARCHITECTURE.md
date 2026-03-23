# מאשה Advanced — Multi-Model Legal Architecture
<!-- Status: Active -->
<!-- Purpose: Cost-efficient multi-model legal agent design -->
<!-- Version: 2.0 -->

## Overview

מאשה Advanced replaces the single-model (Opus) approach with a **3-tier multi-model pipeline** that routes 70-85% of work to cheap models while maintaining or improving quality.

### Design Principles
1. **Cheap first** — Start every task with the cheapest capable model
2. **Escalate on evidence** — Only use expensive models when cheap models detect complexity
3. **Retrieve before generate** — Search cache/templates before invoking any model
4. **Pipeline over monolith** — Split tasks into stages, each at the right tier
5. **Measure everything** — Track cost, latency, quality per operation

## Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    REQUEST INTAKE                        │
│  (Intent Classification + Complexity Scoring)            │
│  Model: Tier 1 (Sonnet) — always                        │
└──────────────┬──────────────────────────────────────────┘
               │
     ┌─────────▼─────────┐
     │  RETRIEVAL LAYER   │
     │  Cache + Templates  │
     │  + Precedents       │
     └─────────┬──────────┘
               │
     ┌─────────▼──────────────────────────────────────────┐
     │              MODEL ROUTER                           │
     │  complexity_score + risk_level + doc_type            │
     │  → Tier 1 / Tier 2 / Tier 3                        │
     └──┬──────────┬──────────────┬───────────────────────┘
        │          │              │
   ┌────▼────┐ ┌──▼─────┐  ┌────▼─────┐
   │ TIER 1  │ │ TIER 2 │  │ TIER 3   │
   │ Sonnet  │ │ Sonnet │  │ Opus     │
   │ 3.5     │ │ 4      │  │ 4        │
   │         │ │(or eq.)│  │          │
   │ 70-85%  │ │ 10-25% │  │ 5-10%   │
   └────┬────┘ └──┬─────┘  └────┬─────┘
        │          │              │
     ┌──▼──────────▼──────────────▼───┐
     │        OUTPUT ASSEMBLY          │
     │  QA Gate + Format + Cache Store │
     └────────────────────────────────┘
```

## Model Tiers

### Tier 1 — Cheap (claude-sonnet-4-20250514)
**Cost:** ~$3/$15 per 1M tokens (input/output)
**Use for:**
- Intent classification
- Document structure extraction (parties, dates, amounts)
- Clause identification and tagging
- Checklist-based analysis (obligations, payments, termination)
- Formatting and template filling
- Simple Q&A about already-analyzed documents
- Cache lookup decisions

**Expected workload:** 70-85% of all tasks

### Tier 2 — Mid (claude-sonnet-4-20250514 with enhanced prompting)
**Cost:** Same base cost, but larger context + chain-of-thought
**Use for:**
- Risk analysis (standard contracts)
- Simple contract drafting (using templates)
- Contract comparison (structural changes)
- Negotiation prep (standard scenarios)
- Ambiguity detection and flagging

**Expected workload:** 10-25% of all tasks

### Tier 3 — Premium (claude-opus-4-20250514)
**Cost:** ~$15/$75 per 1M tokens (input/output)
**Use for:**
- Complex multi-party contracts
- High-risk analysis (>₪100K exposure)
- Sensitive drafting (litigation, regulatory)
- Advanced reasoning (contradictions, novel structures)
- Final refinement when Tier 2 flags issues
- Explicit user request ("use Opus")

**Expected workload:** 5-10% of all tasks

## Pipeline Stages

Every legal task follows this pipeline:

### Stage 0: Intake (always Tier 1)
- Classify intent
- Score complexity (0-100)
- Check cache for similar prior work
- Estimate tokens needed

### Stage 1: Extract & Structure (Tier 1)
- Parse document structure
- Extract key entities (parties, dates, amounts, obligations)
- Run checklist evaluation
- Tag clauses by category

### Stage 2: Analyze (Tier 1 or Tier 2)
- Risk assessment against rubric
- Gap analysis (missing clauses)
- Balance analysis (one-sided terms)
- If complexity_score > 60 → Tier 2

### Stage 3: Synthesize (Tier 2 or Tier 3)
- Generate recommendations
- Draft responses (if needed)
- Compile final output
- If high_risk OR ambiguity_flagged → Tier 3

### Stage 4: QA & Output (Tier 1)
- Format check against LEGAL_OUTPUT_FORMATS.md
- QA validation
- Cache results
- Return to Dvorah

## Cost Projection

### Current State (All-Opus)
| Workflow | Avg Tokens | Cost/Task | Monthly (est. 50 tasks) |
|----------|-----------|-----------|-------------------------|
| Contract Review | 15K in + 5K out | $0.60 | $30.00 |
| Risk Analysis | 12K in + 4K out | $0.48 | $24.00 |
| Clause Extraction | 10K in + 3K out | $0.37 | $18.50 |
| Draft Response | 8K in + 6K out | $0.57 | $28.50 |
| Compare Versions | 20K in + 5K out | $0.68 | $34.00 |
| Legal Summary | 12K in + 3K out | $0.40 | $20.00 |
| Negotiation Prep | 15K in + 8K out | $0.83 | $41.50 |
| **Total** | | | **$196.50/mo** |

### After Multi-Model (Projected)
| Workflow | Tier Split | Cost/Task | Monthly (est. 50 tasks) |
|----------|-----------|-----------|-------------------------|
| Contract Review | 60% T1, 30% T2, 10% T3 | $0.15 | $7.50 |
| Risk Analysis | 50% T1, 35% T2, 15% T3 | $0.18 | $9.00 |
| Clause Extraction | 90% T1, 10% T2 | $0.04 | $2.00 |
| Draft Response | 40% T1, 40% T2, 20% T3 | $0.22 | $11.00 |
| Compare Versions | 70% T1, 25% T2, 5% T3 | $0.12 | $6.00 |
| Legal Summary | 85% T1, 15% T2 | $0.05 | $2.50 |
| Negotiation Prep | 30% T1, 40% T2, 30% T3 | $0.30 | $15.00 |
| **Total** | | | **$53.00/mo** |

### Savings: ~73% cost reduction ($196.50 → $53.00)

## Integration Points

### With Existing System
- `legal_intent_classifier.py` → Enhanced with complexity scoring
- `masha_mvp.py` → Replaced by `masha_advanced.py` (multi-model pipeline)
- `LEGAL_AGENT.md` → Updated to reference multi-model routing
- `legal_agent_prompt.md` → Split into per-tier prompts

### With Dvorah Pipeline
- `orchestrator.py` → Calls Masha Advanced instead of spawning single Opus agent
- `qa_service.py` → Validates output regardless of which tier produced it
- `trace_service.py` → Logs model tier + cost per operation

## Files in This Directory
- `ARCHITECTURE.md` — This file
- `model_router.py` — Smart model selection engine
- `pipeline_engine.py` — Multi-stage pipeline executor
- `cost_tracker.py` — Token estimation and cost tracking
- `legal_cache.py` — Caching and retrieval system
- `legal_checklists.py` — Structured checklist system
- `tier_prompts.py` — Per-tier prompt templates
- `masha_advanced.py` — Main entry point (replaces masha_mvp.py)
