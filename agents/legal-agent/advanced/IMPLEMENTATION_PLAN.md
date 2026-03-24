# מאשה Advanced — Implementation Plan

## Phase 1: Foundation (Done ✅)
**Status: Complete — 2026-03-23**

### Delivered:
1. ✅ `ARCHITECTURE.md` — Full system design with cost projections
2. ✅ `model_router.py` — Smart 3-tier routing engine
3. ✅ `legal_checklists.py` — 49 checklist items across 2 master checklists
4. ✅ `legal_cache.py` — Caching + retrieval-first system
5. ✅ `cost_tracker.py` — Token estimation + cost tracking + reporting
6. ✅ `tier_prompts.py` — 12 tier-specific prompt templates
7. ✅ `pipeline_engine.py` — Multi-stage pipeline with 7 workflow designs
8. ✅ `masha_advanced.py` — Main entry point (backward-compatible with masha_mvp.py)

---

## Phase 2: Live API Integration (Done ✅)
**Status: Complete — 2026-03-23**

### Delivered:
1. ✅ `model_client.py` — Direct Anthropic API client
   - Reads auth from OpenClaw `auth-profiles.json` (no env vars needed)
   - Tier 1/2 (Sonnet) and Tier 3 (Opus) model calls
   - Retry with exponential backoff (429 rate limit, 5xx server errors)
   - `ModelResponse` with real token counts from API
   - JSON extraction helper for structured responses
   - Cost calculation from actual usage

2. ✅ Pipeline wired to real model calls
   - All stages (`extract`, `analyze`, `format`, `qa`) make real API calls
   - Tier escalation works (Tier 1→2 on risk, Tier 2→3 on complexity)
   - Graceful degradation: if a stage fails, pipeline continues with available data
   - Opus refinement stage fires only when lower tiers flag escalation

3. ✅ Cache integration verified
   - First call: real model execution, results cached
   - Second call: $0 cost from cache hit
   - Cache stats tracking estimated savings

4. ✅ Cost tracking with real data
   - Actual token counts from Anthropic API responses
   - Real cost calculation per-call
   - Daily JSONL logs in `cost_logs/`
   - Session + daily reports working

5. ✅ Orchestrator integration
   - `orchestrator.py` routes legal→MashaAdvanced
   - `masha_mvp.py` wrapper delegates to MashaAdvanced
   - Backward compatibility maintained

### Test Results (Phase 2):
| Test | Tiers Used | Cost | Savings vs Opus | Duration |
|------|-----------|------|-----------------|----------|
| Clause extraction | T1+T2 | $0.10 | 80% | ~96s |
| Legal summary | T1+T2 | $0.08 | 80% | ~92s |
| Cache hit (repeat) | cache | $0.00 | 100% | 0ms |

### Cost Distribution:
- Tier 1: 88% of calls
- Tier 2: 12% of calls
- Tier 3: 0% (correctly reserved for complex/critical only)

---

## Phase 3: Optimization & Polish (Next)

### 3.1 Prompt Optimization
- Fine-tune tier prompts based on real output quality
- Reduce token waste in extraction prompts (currently some checklist items redundant for simple tasks)
- Improve JSON parsing reliability (some responses need fallback extraction)

### 3.2 Parallel Stage Execution
- Stages that don't depend on each other could run in parallel
- E.g., formatting + QA could overlap

### 3.3 Template Library
- Build up `templates/` and `precedents/` with real legal patterns
- Better retrieval-first results = fewer model calls

### 3.4 Monitoring Dashboard
- Real-time cost tracking visualization
- Tier distribution trends
- Cache hit rate over time
- Alert when approaching budget limits

### 3.5 Edge Cases
- Very long documents (>50K words) — chunking strategy
- Hebrew-only contracts — prompt optimization
- Multi-document workflows (compare versions with real files)
