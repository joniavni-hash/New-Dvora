#!/usr/bin/env python3
"""
Pipeline Engine — Multi-stage pipeline executor for Masha Advanced.
Replaces single expensive model calls with staged processing.
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

from model_router import ModelRouter, ModelTier, RoutingDecision
from legal_checklists import (
    get_checklist_for_workflow, build_extraction_prompt, build_checklist_summary,
    ChecklistResult
)
from legal_cache import LegalCache
from cost_tracker import CostTracker
from tier_prompts import get_prompt


@dataclass
class PipelineStage:
    """Result of a single pipeline stage."""
    stage_name: str
    tier_used: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    result: Dict
    was_cached: bool = False
    escalated: bool = False


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    task_type: str
    stages: List[PipelineStage]
    final_output: Dict
    total_cost_usd: float
    total_duration_ms: int
    tiers_used: List[str]
    was_fully_cached: bool
    routing_decision: Dict
    cost_comparison: Dict  # vs all-Opus

    def to_dict(self) -> Dict:
        return {
            "task_type": self.task_type,
            "stages": [asdict(s) for s in self.stages],
            "final_output": self.final_output,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "total_duration_ms": self.total_duration_ms,
            "tiers_used": self.tiers_used,
            "was_fully_cached": self.was_fully_cached,
            "routing_decision": self.routing_decision,
            "cost_comparison": self.cost_comparison,
        }


class PipelineEngine:
    """
    Executes legal analysis through a multi-stage pipeline.
    
    Pipeline flow:
    1. INTAKE: Classify + route (always Tier 1)
    2. RETRIEVE: Check cache + search templates/precedents
    3. EXTRACT: Structured extraction via checklist (Tier 1)
    4. ANALYZE: Risk/comparison/analysis (Tier 1 or 2)
    5. SYNTHESIZE: Generate final output (Tier 2 or 3, if needed)
    6. QA: Quality check (Tier 1)
    7. CACHE: Store results
    """

    def __init__(self):
        self.router = ModelRouter()
        self.cache = LegalCache()
        self.cost_tracker = CostTracker()

    def execute(
        self,
        task_type: str,
        message: str,
        document_text: Optional[str] = None,
        context: Optional[Dict] = None,
        attachments: List[str] = None,
        force_tier: Optional[str] = None,
    ) -> PipelineResult:
        """
        Execute the full pipeline for a legal task.
        
        This is the main entry point — replaces the old single-model call.
        """
        context = context or {}
        attachments = attachments or []
        start_time = time.time()
        stages: List[PipelineStage] = []
        tiers_used = set()

        # ========================================
        # STAGE 0: Check full cache
        # ========================================
        cached = self.cache.get(task_type, message, document_text)
        if cached and not force_tier:
            return PipelineResult(
                task_type=task_type,
                stages=[PipelineStage(
                    stage_name="cache_hit",
                    tier_used="cache",
                    input_tokens=0, output_tokens=0, cost_usd=0.0,
                    duration_ms=0, result=cached.result, was_cached=True,
                )],
                final_output=cached.result,
                total_cost_usd=0.0,
                total_duration_ms=int((time.time() - start_time) * 1000),
                tiers_used=["cache"],
                was_fully_cached=True,
                routing_decision={"tier": "cache", "reason": "Full cache hit"},
                cost_comparison={"opus_cost": cached.cost_usd, "actual_cost": 0.0, "savings_pct": 100},
            )

        # ========================================
        # STAGE 1: ROUTE — Determine model tier
        # ========================================
        routing = self.router.route(
            task_type=task_type,
            message=message,
            document_text=document_text,
            context=context,
            force_tier=force_tier,
        )
        tiers_used.add(routing.tier.value)

        # ========================================
        # STAGE 2: RETRIEVE — Get relevant context
        # ========================================
        retrieval_context = self.cache.build_retrieval_context(task_type, message, document_text)

        # ========================================
        # STAGE 3: EXTRACT — Structured extraction (Tier 1)
        # ========================================
        extraction_stage = self._run_extraction(task_type, message, document_text, retrieval_context)
        stages.append(extraction_stage)
        tiers_used.add("tier1")

        extraction_data = extraction_stage.result

        # Check if Tier 1 extraction flagged escalation
        if extraction_data.get("risk_escalation") and routing.tier == ModelTier.TIER1_CHEAP:
            # Escalate to Tier 2
            routing = RoutingDecision(
                tier=ModelTier.TIER2_MID,
                model=routing.model,
                reason=f"Escalated from Tier 1: {extraction_data.get('escalation_reason', 'risk flagged')}",
                confidence=0.7,
                complexity_score=routing.complexity_score + 20,
                risk_level="medium",
                escalation_triggers=["tier1_flagged_risk"],
            )
            tiers_used.add("tier2")

        # ========================================
        # STAGE 4: ANALYZE — Risk/comparison/analysis
        # ========================================
        if routing.tier in (ModelTier.TIER2_MID, ModelTier.TIER3_OPUS) or task_type in ("risk_analysis", "compare_versions", "negotiation_prep"):
            analysis_stage = self._run_analysis(
                task_type, message, document_text, extraction_data, retrieval_context, routing
            )
            stages.append(analysis_stage)
            tiers_used.add(analysis_stage.tier_used)
            analysis_data = analysis_stage.result

            # Check if Tier 2 analysis needs Opus
            if analysis_data.get("needs_opus_review") and routing.tier != ModelTier.TIER3_OPUS:
                synthesis_stage = self._run_opus_refinement(
                    task_type, message, document_text, extraction_data,
                    analysis_data, retrieval_context, analysis_data.get("opus_reason", "Flagged by Tier 2")
                )
                stages.append(synthesis_stage)
                tiers_used.add("tier3")
        else:
            analysis_data = extraction_data

        # ========================================
        # STAGE 5: FORMAT — Build final output (Tier 1)
        # ========================================
        format_stage = self._run_formatting(task_type, message, extraction_data, analysis_data)
        stages.append(format_stage)

        # ========================================
        # STAGE 6: QA — Quality check (Tier 1)
        # ========================================
        qa_stage = self._run_qa(task_type, message, format_stage.result)
        stages.append(qa_stage)

        # ========================================
        # COMPILE RESULT
        # ========================================
        total_cost = sum(s.cost_usd for s in stages)
        total_duration = int((time.time() - start_time) * 1000)

        # Build final output in standard Masha format
        final_output = self._build_final_output(
            task_type=task_type,
            extraction_data=extraction_data,
            analysis_data=analysis_data,
            formatted_content=format_stage.result.get("content", ""),
            qa_result=qa_stage.result,
            routing=routing,
        )

        # Cost comparison
        opus_cost = self.cost_tracker.estimate_cost(
            sum(s.input_tokens for s in stages),
            sum(s.output_tokens for s in stages),
            "tier3"
        )
        savings_pct = round((1 - total_cost / max(opus_cost, 0.0001)) * 100, 1)

        result = PipelineResult(
            task_type=task_type,
            stages=stages,
            final_output=final_output,
            total_cost_usd=total_cost,
            total_duration_ms=total_duration,
            tiers_used=list(tiers_used),
            was_fully_cached=False,
            routing_decision=routing.to_dict(),
            cost_comparison={
                "opus_cost_usd": round(opus_cost, 4),
                "actual_cost_usd": round(total_cost, 4),
                "savings_pct": savings_pct,
            },
        )

        # ========================================
        # STAGE 7: CACHE — Store for future use
        # ========================================
        self.cache.put(
            task_type=task_type,
            message=message,
            document_text=document_text,
            result=final_output,
            model_tier=routing.tier.value,
            cost_usd=total_cost,
            tags=self._extract_tags(extraction_data),
        )

        return result

    # ============================================================
    # STAGE IMPLEMENTATIONS
    # ============================================================

    def _run_extraction(
        self, task_type: str, message: str, document_text: Optional[str],
        retrieval_context: Dict
    ) -> PipelineStage:
        """Stage 3: Structured extraction using checklists."""
        start = time.time()

        # Get appropriate checklist
        checklist = get_checklist_for_workflow(task_type)
        checklist_prompt = build_extraction_prompt(checklist)

        # Build prompt
        prompt = get_prompt(
            "tier1", "extraction",
            document_text=document_text or "(No document provided)",
            message=message,
            checklist_prompt=checklist_prompt,
        )

        # Estimate tokens
        input_tokens = self.cost_tracker.estimate_tokens(
            prompt["system"] + prompt["user"], "mixed"
        )
        output_tokens = len(checklist) * 100  # ~100 tokens per checklist item

        # NOTE: In production, this calls the actual model API.
        # For now, we return the prompt configuration.
        result = {
            "prompt_ready": True,
            "system_prompt": prompt["system"],
            "user_prompt": prompt["user"],
            "checklist_items": len(checklist),
            "model": "anthropic/claude-sonnet-4-20250514",
            # Placeholder — actual model output would go here
            "extraction_results": [],
            "flagged_issues": [],
            "ambiguity_detected": False,
            "risk_escalation": False,
            "confidence": 0.8,
        }

        cost = self.cost_tracker.estimate_cost(input_tokens, output_tokens, "tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="extract",
            model_tier="tier1",
            model_id="anthropic/claude-sonnet-4-20250514",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return PipelineStage(
            stage_name="extraction",
            tier_used="tier1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_analysis(
        self, task_type: str, message: str, document_text: Optional[str],
        extraction_data: Dict, retrieval_context: Dict, routing: RoutingDecision
    ) -> PipelineStage:
        """Stage 4: Analysis using Tier 2 (or routing decision)."""
        start = time.time()
        tier = routing.tier.value if routing.tier != ModelTier.TIER1_CHEAP else "tier2"

        # Select appropriate prompt
        stage_map = {
            "risk_analysis": "risk_analysis",
            "compare_versions": "comparison",
            "draft_response": "draft",
            "negotiation_prep": "negotiation",
        }
        prompt_stage = stage_map.get(task_type, "risk_analysis")

        prompt = get_prompt(
            tier, prompt_stage,
            extraction_data=json.dumps(extraction_data, ensure_ascii=False),
            document_summary=document_text[:1000] if document_text else "",
            message=message,
            retrieval_context=json.dumps(retrieval_context, ensure_ascii=False),
            risk_analysis="",
            tone="רשמי",
            red_lines="",
            version_a_data="",
            version_b_data="",
        )

        input_tokens = self.cost_tracker.estimate_tokens(
            prompt["system"] + prompt["user"], "mixed"
        )
        output_tokens = 3000  # Estimate for analysis output

        result = {
            "prompt_ready": True,
            "system_prompt": prompt["system"],
            "user_prompt": prompt["user"],
            "model": routing.model,
            "tier": tier,
            # Placeholder
            "analysis_result": {},
            "needs_opus_review": False,
            "tier2_confidence": 0.8,
        }

        cost = self.cost_tracker.estimate_cost(input_tokens, output_tokens, tier)
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="analyze",
            model_tier=tier,
            model_id=routing.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return PipelineStage(
            stage_name="analysis",
            tier_used=tier,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_opus_refinement(
        self, task_type: str, message: str, document_text: Optional[str],
        extraction_data: Dict, tier2_analysis: Dict, retrieval_context: Dict,
        escalation_reason: str
    ) -> PipelineStage:
        """Stage 5 (optional): Opus refinement when escalated."""
        start = time.time()

        prompt = get_prompt(
            "tier3", "refinement",
            extraction_data=json.dumps(extraction_data, ensure_ascii=False),
            tier2_analysis=json.dumps(tier2_analysis, ensure_ascii=False),
            escalation_reason=escalation_reason,
            document_sections=document_text[:3000] if document_text else "",
            message=message,
            retrieval_context=json.dumps(retrieval_context, ensure_ascii=False),
        )

        input_tokens = self.cost_tracker.estimate_tokens(
            prompt["system"] + prompt["user"], "mixed"
        )
        output_tokens = 5000

        result = {
            "prompt_ready": True,
            "system_prompt": prompt["system"],
            "user_prompt": prompt["user"],
            "model": "anthropic/claude-opus-4-20250514",
            "escalation_reason": escalation_reason,
        }

        cost = self.cost_tracker.estimate_cost(input_tokens, output_tokens, "tier3")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="synthesize",
            model_tier="tier3",
            model_id="anthropic/claude-opus-4-20250514",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            escalated_from="tier2",
        )

        return PipelineStage(
            stage_name="opus_refinement",
            tier_used="tier3",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
            escalated=True,
        )

    def _run_formatting(
        self, task_type: str, message: str, extraction_data: Dict, analysis_data: Dict
    ) -> PipelineStage:
        """Stage 6: Format output using Tier 1."""
        start = time.time()

        prompt = get_prompt(
            "tier1", "formatting",
            task_type=task_type,
            analysis_data=json.dumps({
                "extraction": extraction_data,
                "analysis": analysis_data,
            }, ensure_ascii=False),
            output_format=task_type,
        )

        input_tokens = self.cost_tracker.estimate_tokens(
            prompt["system"] + prompt["user"], "mixed"
        )
        output_tokens = 4000

        result = {
            "prompt_ready": True,
            "content": "",  # Will be filled by actual model call
            "model": "anthropic/claude-sonnet-4-20250514",
        }

        cost = self.cost_tracker.estimate_cost(input_tokens, output_tokens, "tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="format",
            model_tier="tier1",
            model_id="anthropic/claude-sonnet-4-20250514",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return PipelineStage(
            stage_name="formatting",
            tier_used="tier1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_qa(self, task_type: str, message: str, formatted_output: Dict) -> PipelineStage:
        """Stage 7: QA check using Tier 1."""
        start = time.time()

        prompt = get_prompt(
            "tier1", "qa",
            output=json.dumps(formatted_output, ensure_ascii=False),
            message=message,
            task_type=task_type,
        )

        input_tokens = self.cost_tracker.estimate_tokens(
            prompt["system"] + prompt["user"], "mixed"
        )
        output_tokens = 500

        result = {
            "qa_passed": True,  # Placeholder
            "issues_found": [],
            "model": "anthropic/claude-sonnet-4-20250514",
        }

        cost = self.cost_tracker.estimate_cost(input_tokens, output_tokens, "tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="qa",
            model_tier="tier1",
            model_id="anthropic/claude-sonnet-4-20250514",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return PipelineStage(
            stage_name="qa",
            tier_used="tier1",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    # ============================================================
    # OUTPUT BUILDING
    # ============================================================

    def _build_final_output(
        self, task_type: str, extraction_data: Dict, analysis_data: Dict,
        formatted_content: str, qa_result: Dict, routing: RoutingDecision
    ) -> Dict:
        """Build the standard Masha output format."""
        return {
            "decision": self._task_type_to_decision(task_type),
            "confidence": routing.confidence,
            "reasoning": routing.reason,
            "draft": {
                "type": task_type,
                "content": formatted_content,
            },
            "legalRisk": routing.risk_level,
            "riskFactors": extraction_data.get("flagged_issues", []),
            "memoryDelta": None,
            "stateDelta": None,
            "qaResult": "pass" if qa_result.get("qa_passed") else "needs_revision",
            "suggestedActions": [],
            "requiresApproval": True,
            "modelTier": routing.tier.value,
            "costUsd": routing.estimated_cost_usd,
        }

    @staticmethod
    def _task_type_to_decision(task_type: str) -> str:
        decision_map = {
            "contract_review": "analysis",
            "risk_analysis": "analysis",
            "clause_extraction": "analysis",
            "legal_summary": "summary",
            "draft_response": "draft",
            "compare_versions": "comparison",
            "negotiation_prep": "analysis",
        }
        return decision_map.get(task_type, "analysis")

    @staticmethod
    def _extract_tags(extraction_data: Dict) -> List[str]:
        """Extract tags from extraction data for caching."""
        tags = []
        for item in extraction_data.get("extraction_results", []):
            if isinstance(item, dict) and item.get("found"):
                tags.append(item.get("item_id", ""))
        return [t for t in tags if t][:10]

    # ============================================================
    # PIPELINE DESIGNS FOR ALL 7 WORKFLOWS
    # ============================================================

    def get_pipeline_design(self, task_type: str) -> Dict:
        """Return the pipeline design for a specific workflow."""
        designs = {
            "contract_review": {
                "name": "Contract Review Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Classify + complexity score"},
                    {"stage": "retrieve", "tier": "cache", "action": "Search prior contract analyses + templates"},
                    {"stage": "extract", "tier": "tier1", "action": "Full checklist extraction (33 items)"},
                    {"stage": "analyze", "tier": "tier1|tier2", "action": "Risk rubric evaluation + balance analysis"},
                    {"stage": "synthesize", "tier": "tier2|tier3", "action": "Recommendations + overall assessment (if needed)"},
                    {"stage": "format", "tier": "tier1", "action": "Build contract_review output format"},
                    {"stage": "qa", "tier": "tier1", "action": "Quality validation"},
                ],
                "typical_tier_split": "60% T1, 30% T2, 10% T3",
                "escalation_triggers": ["unlimited liability", "multi-party", "foreign jurisdiction", "complexity > 60"],
            },
            "risk_analysis": {
                "name": "Risk Analysis Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Classify + risk pre-scan"},
                    {"stage": "retrieve", "tier": "cache", "action": "Search prior risk assessments"},
                    {"stage": "extract", "tier": "tier1", "action": "Risk checklist extraction (16 items)"},
                    {"stage": "analyze", "tier": "tier2", "action": "Risk scoring + interaction analysis"},
                    {"stage": "synthesize", "tier": "tier3", "action": "Deep risk reasoning (if critical/high)"},
                    {"stage": "format", "tier": "tier1", "action": "Build risk_analysis output format"},
                    {"stage": "qa", "tier": "tier1", "action": "Risk classification validation"},
                ],
                "typical_tier_split": "50% T1, 35% T2, 15% T3",
                "escalation_triggers": ["critical risk items", "ambiguity in liability", "cross-clause interactions"],
            },
            "clause_extraction": {
                "name": "Clause Extraction Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Identify target clause category"},
                    {"stage": "retrieve", "tier": "cache", "action": "Search clause templates"},
                    {"stage": "extract", "tier": "tier1", "action": "Targeted clause search + extraction"},
                    {"stage": "analyze", "tier": "tier1", "action": "Contradiction check + completeness"},
                    {"stage": "format", "tier": "tier1", "action": "Build clause_extraction output"},
                    {"stage": "qa", "tier": "tier1", "action": "Validate extraction accuracy"},
                ],
                "typical_tier_split": "90% T1, 10% T2",
                "escalation_triggers": ["contradicting clauses", "ambiguous definitions"],
            },
            "legal_summary": {
                "name": "Legal Summary Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Classify document type"},
                    {"stage": "retrieve", "tier": "cache", "action": "Check for cached summaries"},
                    {"stage": "extract", "tier": "tier1", "action": "Key points extraction (basics checklist)"},
                    {"stage": "format", "tier": "tier1", "action": "Build legal_summary output"},
                    {"stage": "qa", "tier": "tier1", "action": "Completeness check"},
                ],
                "typical_tier_split": "85% T1, 15% T2",
                "escalation_triggers": ["regulatory document", "very long document"],
            },
            "draft_response": {
                "name": "Draft Response Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Understand context + tone + target"},
                    {"stage": "retrieve", "tier": "cache", "action": "Search response templates + Yoni's preferences"},
                    {"stage": "extract", "tier": "tier1", "action": "Extract key points from source document"},
                    {"stage": "analyze", "tier": "tier2", "action": "Strategy analysis + key arguments"},
                    {"stage": "synthesize", "tier": "tier2|tier3", "action": "Draft the response"},
                    {"stage": "format", "tier": "tier1", "action": "Polish formatting"},
                    {"stage": "qa", "tier": "tier1", "action": "Tone + accuracy check"},
                ],
                "typical_tier_split": "40% T1, 40% T2, 20% T3",
                "escalation_triggers": ["litigation context", "sensitive counterparty", "high-value dispute"],
            },
            "compare_versions": {
                "name": "Version Comparison Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Identify documents + comparison focus"},
                    {"stage": "retrieve", "tier": "cache", "action": "Check for prior comparisons"},
                    {"stage": "extract", "tier": "tier1", "action": "Extract from both versions (parallel)"},
                    {"stage": "analyze", "tier": "tier1|tier2", "action": "Diff analysis + impact classification"},
                    {"stage": "format", "tier": "tier1", "action": "Build compare_versions output"},
                    {"stage": "qa", "tier": "tier1", "action": "Validate change classifications"},
                ],
                "typical_tier_split": "70% T1, 25% T2, 5% T3",
                "escalation_triggers": ["many critical changes", "liability clause changes", ">50 changes"],
            },
            "negotiation_prep": {
                "name": "Negotiation Prep Pipeline",
                "stages": [
                    {"stage": "intake", "tier": "tier1", "action": "Understand goals + red lines"},
                    {"stage": "retrieve", "tier": "cache", "action": "Search counterparty history + precedents"},
                    {"stage": "extract", "tier": "tier1", "action": "Full contract extraction + risk checklist"},
                    {"stage": "analyze", "tier": "tier2", "action": "Strategy analysis + alternative proposals"},
                    {"stage": "synthesize", "tier": "tier2|tier3", "action": "Build negotiation script + scenarios"},
                    {"stage": "format", "tier": "tier1", "action": "Build negotiation_prep output"},
                    {"stage": "qa", "tier": "tier1", "action": "Strategy coherence check"},
                ],
                "typical_tier_split": "30% T1, 40% T2, 30% T3",
                "escalation_triggers": ["high-value deal", "complex multi-issue negotiation", "adversarial counterparty"],
            },
        }
        return designs.get(task_type, designs["contract_review"])


def test_pipeline():
    """Test pipeline execution."""
    engine = PipelineEngine()

    # Test pipeline design retrieval
    for workflow in ["contract_review", "risk_analysis", "clause_extraction", "legal_summary",
                     "draft_response", "compare_versions", "negotiation_prep"]:
        design = engine.get_pipeline_design(workflow)
        print(f"\n{design['name']}: {len(design['stages'])} stages, typical split: {design['typical_tier_split']}")

    # Test full pipeline execution
    print("\n=== Full Pipeline Test ===")
    result = engine.execute(
        task_type="contract_review",
        message="תסכמי את החוזה",
        document_text="This is a sample contract between Party A and Party B. " * 100,
        context={"sender": "yoni"},
    )

    print(f"Task: {result.task_type}")
    print(f"Stages: {len(result.stages)}")
    print(f"Total cost: ${result.total_cost_usd:.4f}")
    print(f"Tiers used: {result.tiers_used}")
    print(f"Cost comparison: {json.dumps(result.cost_comparison, indent=2)}")

    # Session cost summary
    print(f"\nSession summary: {json.dumps(engine.cost_tracker.session_summary(), indent=2)}")


if __name__ == "__main__":
    test_pipeline()
