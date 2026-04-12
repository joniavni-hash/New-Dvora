# Switchover Record
<!-- Date: 2026-03-23T20:10 -->
<!-- Status: ACTIVE -->

## What Changed
1. **AGENTS.md** — Simplified from 7-file boot chain → 3 files (IDENTITY, SOUL, AGENTS w/ orchestrator pointer)
2. **Orchestrator pipeline** — Now primary decision path (was shadow-only)
3. **Context loading** — Automated by ContextService (was manual per MEMORY_INDEX.md)
4. **Policy enforcement** — Automated by PolicyService (was manual per policy files)
5. **QA checks** — Automated by QAService before external actions
6. **Tracing** — All decisions logged to JSONL automatically

## Backups
- `AGENTS.md.old` — Previous full boot chain
- `core/orchestrator_flow.md.old` — Previous 11-step manual flow

## Rollback Instructions
If issues detected:
1. `cp AGENTS.md.old AGENTS.md`
2. `cp core/orchestrator_flow.md.old core/orchestrator_flow.md`
3. Revert `core/orchestrator.md` shadow mode section

## Validation Results (pre-switchover)
- 37/37 tests passed (100%)
- p95 latency: 0.8ms
- 144 shadow traces validated
- Zero QA failures

## Post-Switchover Tests
- DM question (general) → direct/auto ✅
- Email send action → direct/dvorah_approve ✅
- Group message → WhatsAppGroupAgent/auto ✅
- Legal contract → LegalAgent/dvorah_approve ✅
- Fitness tracking → direct/auto ✅
- Memory command → direct/dvorah_only (MUTATE) ✅

## Monitoring Plan
- Watch first 50 real messages for anomalies
- Check traces daily: `python3 scripts/trace_service.py --stats`
- Compare response quality vs pre-switchover
- Rollback if: >5% routing errors, QA failures on real messages, or user complaints
