# מאשה Advanced — Implementation Plan

## Phase 1: Foundation (Done ✅)
**Status: Complete**

### Delivered:
1. ✅ `ARCHITECTURE.md` — Full system design with cost projections
2. ✅ `model_router.py` — Smart 3-tier routing engine
3. ✅ `legal_checklists.py` — 49 checklist items across 2 master checklists
4. ✅ `legal_cache.py` — Caching + retrieval-first system
5. ✅ `cost_tracker.py` — Token estimation + cost tracking + reporting
6. ✅ `tier_prompts.py` — 12 tier-specific prompt templates
7. ✅ `pipeline_engine.py` — Multi-stage pipeline with 7 workflow designs
8. ✅ `masha_advanced.py` — Main entry point (backward-compatible with masha_mvp.py)

### Test Results:
- Router correctly routes: simple→Tier1, medium→Tier2, critical→Tier3
- Cost estimation: 80% savings vs all-Opus for standard tasks
- Pipeline executes 5-7 stages per workflow
- Cache stores and retrieves results
- All 7 workflow pipelines designed

---

## Phase 2: Integration (Next)

### 2.1 Wire to Actual Model API
**Priority: High | Effort: Medium**

The pipeline currently builds prompts but returns placeholders. To go live:

1. Create `model_client.py` — wrapper around OpenClaw's model invocation
2. Replace placeholder returns in `pipeline_engine.py` stage methods with actual API calls
3. Parse JSON responses from models
4. Handle API errors, timeouts, retries

```python
# model_client.py sketch
class ModelClient:
    async def invoke(self, model: str, system: str, user: str) -> Dict:
        # Use sessions_spawn or direct API call
        pass
```

### 2.2 Update Orchestrator Integration
**Priority: High | Effort: Low**

Update `scripts/orchestrator.py` to use MashaAdvanced instead of spawning single-model agent:

```python
# In orchestrator.py, replace:
# agent = "legal_agent" → spawn with Opus prompt
# With:
from agents.legal_agent.advanced.masha_advanced import MashaAdvanced
masha = MashaAdvanced()
result = masha.analyze(task=message, document_text=doc_text, context=ctx)
```

### 2.3 Document Parsing
**Priority: Medium | Effort: Medium**

Add PDF/DOCX text extraction for attached documents:
- Use `pdftotext` or `pymupdf` for PDFs
- Use `python-docx` for DOCX
- Pass extracted text to `pipeline.execute(document_text=...)`

---

## Phase 3: Optimization

### 3.1 Template Library
**Priority: Medium | Effort: Low**

Populate `templates/` and `precedents/` directories with:
- Standard contract review templates (service, NDA, employment, lease)
- Common clause templates (liability caps, termination, IP)
- Negotiation playbooks for common scenarios

### 3.2 Memory Integration
**Priority: Medium | Effort: Low**

Connect cache system to `LEGAL_MEMORY_RULES.md`:
- Auto-store Yoni's preferences from corrections
- Store counterparty patterns from completed analyses
- Feed into retrieval context for future analyses

### 3.3 Embedding-Based Retrieval
**Priority: Low | Effort: High**

Replace keyword-based retrieval with vector embeddings:
- Embed all templates and precedents
- Use similarity search for retrieval
- Significantly improve retrieval quality

### 3.4 Parallel Stage Execution
**Priority: Low | Effort: Medium**

For workflows like `compare_versions`, run extraction on both documents in parallel:
- Use asyncio for parallel API calls
- Reduce total latency by ~40% for multi-document tasks

---

## Phase 4: Monitoring & Tuning

### 4.1 Quality Benchmarking
- Compare multi-model output quality against single-Opus baseline
- Track QA pass rates by tier
- Identify workflows where Tier 1 quality is insufficient

### 4.2 Routing Tuning
- Collect real routing decisions and outcomes
- Tune complexity thresholds based on actual escalation patterns
- Add A/B testing: run same task through Tier 1 and Tier 3, compare

### 4.3 Cost Dashboard
- Daily/weekly cost reports via `masha_advanced.py --cost-report`
- Track tier distribution over time
- Alert if Opus usage exceeds 10% threshold

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Tier 1 quality insufficient | Automatic escalation + QA stage catches issues |
| Over-reliance on cache | TTL-based expiration + invalidation on document change |
| Routing errors (wrong tier) | Conservative bias (escalate when uncertain) |
| Model API failures | Retry logic + fallback to next tier |
| Prompt injection in documents | Checklist-based extraction limits model freedom |

---

## Migration Path

### From masha_mvp.py to masha_advanced.py:

1. **Phase 1 (Current):** Both systems exist, advanced is tested standalone
2. **Phase 2:** Route 10% of requests through advanced, compare quality
3. **Phase 3:** Route 50% through advanced, monitor costs
4. **Phase 4:** Full cutover, deprecate masha_mvp.py

### Backward Compatibility:
- `MashaAdvanced.can_handle()` has same interface as `MashaMVP.can_handle()`
- `MashaAdvanced.analyze()` returns same JSON structure
- New fields (`modelTier`, `costUsd`) are additive — won't break existing consumers
