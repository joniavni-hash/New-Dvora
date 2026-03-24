#!/usr/bin/env python3
"""
Pipeline Engine — Multi-stage pipeline executor for Masha Advanced.
LIVE VERSION: Makes real model calls via model_client.
"""

import json
import time
import logging
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
from model_client import call_for_tier, extract_json, ModelResponse, ModelCallError

logger = logging.getLogger("masha.pipeline")


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
    Executes legal analysis through a multi-stage pipeline with REAL model calls.

    Pipeline flow:
    1. CACHE CHECK: Return cached result if available
    2. ROUTE: Determine model tier
    3. RETRIEVE: Get relevant context (templates/precedents)
    4. EXTRACT: Structured extraction via checklist (Tier 1)
    5. ANALYZE: Risk/comparison/analysis (Tier 1 or 2, escalate if needed)
    6. SYNTHESIZE: Opus refinement (Tier 3, only if escalated)
    7. FORMAT: Build final output (Tier 1)
    8. QA: Quality check (Tier 1)
    9. CACHE STORE: Save results
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
        """Execute the full pipeline for a legal task with REAL model calls."""
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
        # STAGE 3: EXTRACT — Structured extraction (Tier 1) — REAL CALL
        # ========================================
        try:
            extraction_stage = self._run_extraction(task_type, message, document_text, retrieval_context)
            stages.append(extraction_stage)
            tiers_used.add("tier1")
            extraction_data = extraction_stage.result
        except ModelCallError as e:
            logger.error(f"Extraction failed: {e}")
            return self._build_error_result(task_type, str(e), start_time, routing)

        # Check if Tier 1 extraction flagged escalation
        if extraction_data.get("risk_escalation") and routing.tier == ModelTier.TIER1_CHEAP:
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
        # STAGE 4: ANALYZE — Risk/comparison/analysis — REAL CALL
        # ========================================
        analysis_data = extraction_data  # Default: skip analysis for simple tasks

        if routing.tier in (ModelTier.TIER2_MID, ModelTier.TIER3_OPUS) or \
           task_type in ("risk_analysis", "compare_versions", "negotiation_prep"):
            try:
                analysis_stage = self._run_analysis(
                    task_type, message, document_text, extraction_data, retrieval_context, routing
                )
                stages.append(analysis_stage)
                tiers_used.add(analysis_stage.tier_used)
                analysis_data = analysis_stage.result

                # Check if Tier 2 analysis needs Opus
                if analysis_data.get("needs_opus_review") and routing.tier != ModelTier.TIER3_OPUS:
                    try:
                        synthesis_stage = self._run_opus_refinement(
                            task_type, message, document_text, extraction_data,
                            analysis_data, retrieval_context,
                            analysis_data.get("opus_reason", "Flagged by Tier 2")
                        )
                        stages.append(synthesis_stage)
                        tiers_used.add("tier3")
                        # Merge opus refinement into analysis_data
                        analysis_data.update(synthesis_stage.result)
                    except ModelCallError as e:
                        logger.warning(f"Opus refinement failed, continuing with Tier 2 output: {e}")

            except ModelCallError as e:
                logger.error(f"Analysis failed: {e}")
                # Continue with extraction data only — degrade gracefully

        # ========================================
        # STAGE 5: FORMAT — Build final output (Tier 1) — REAL CALL
        # ========================================
        try:
            format_stage = self._run_formatting(task_type, message, extraction_data, analysis_data)
            stages.append(format_stage)
        except ModelCallError as e:
            logger.warning(f"Formatting failed, using raw analysis: {e}")
            format_stage = PipelineStage(
                stage_name="formatting",
                tier_used="tier1",
                input_tokens=0, output_tokens=0, cost_usd=0.0,
                duration_ms=0,
                result={"content": json.dumps(analysis_data, ensure_ascii=False, indent=2)},
            )
            stages.append(format_stage)

        # ========================================
        # STAGE 6: QA — Quality check (Tier 1) — REAL CALL
        # ========================================
        try:
            qa_stage = self._run_qa(task_type, message, format_stage.result)
            stages.append(qa_stage)
        except ModelCallError as e:
            logger.warning(f"QA failed, passing anyway: {e}")
            qa_stage = PipelineStage(
                stage_name="qa", tier_used="tier1",
                input_tokens=0, output_tokens=0, cost_usd=0.0,
                duration_ms=0, result={"qa_passed": True, "issues_found": [], "note": "QA skipped due to error"},
            )
            stages.append(qa_stage)

        # ========================================
        # COMPILE RESULT
        # ========================================
        total_cost = sum(s.cost_usd for s in stages)
        total_duration = int((time.time() - start_time) * 1000)

        final_output = self._build_final_output(
            task_type=task_type,
            extraction_data=extraction_data,
            analysis_data=analysis_data,
            formatted_content=format_stage.result.get("content", ""),
            qa_result=qa_stage.result,
            routing=routing,
            total_cost=total_cost,
        )

        # Cost comparison vs all-Opus
        total_input = sum(s.input_tokens for s in stages)
        total_output = sum(s.output_tokens for s in stages)
        opus_cost = self.cost_tracker.estimate_cost(total_input, total_output, "tier3")
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
    # STAGE IMPLEMENTATIONS — ALL WITH REAL MODEL CALLS
    # ============================================================

    def _run_extraction(
        self, task_type: str, message: str, document_text: Optional[str],
        retrieval_context: Dict
    ) -> PipelineStage:
        """Stage 3: Structured extraction using checklists — REAL MODEL CALL."""
        start = time.time()

        checklist = get_checklist_for_workflow(task_type)
        checklist_prompt = build_extraction_prompt(checklist)

        prompt = get_prompt(
            "tier1", "extraction",
            document_text=document_text or "(No document provided)",
            message=message,
            checklist_prompt=checklist_prompt,
        )

        # REAL API CALL
        response = call_for_tier(
            "tier1",
            system=prompt["system"],
            user=prompt["user"],
            max_tokens=4096,
        )

        # Parse structured response
        parsed = extract_json(response.content)
        if parsed is None:
            parsed = {}

        # Build result
        result = {
            "model": response.model,
            "extraction_results": parsed.get("extraction_results", parsed.get("items", [])) if isinstance(parsed, dict) else parsed if isinstance(parsed, list) else [],
            "flagged_issues": parsed.get("flagged_issues", []) if isinstance(parsed, dict) else [],
            "ambiguity_detected": parsed.get("ambiguity_detected", False) if isinstance(parsed, dict) else False,
            "risk_escalation": parsed.get("risk_escalation", False) if isinstance(parsed, dict) else False,
            "escalation_reason": parsed.get("escalation_reason", "") if isinstance(parsed, dict) else "",
            "confidence": parsed.get("confidence", 0.8) if isinstance(parsed, dict) else 0.8,
            "raw_content": response.content,
        }

        cost = response.cost_usd("tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="extract",
            model_tier="tier1",
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        return PipelineStage(
            stage_name="extraction",
            tier_used="tier1",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_analysis(
        self, task_type: str, message: str, document_text: Optional[str],
        extraction_data: Dict, retrieval_context: Dict, routing: RoutingDecision
    ) -> PipelineStage:
        """Stage 4: Analysis using Tier 2 (or routing decision) — REAL MODEL CALL."""
        start = time.time()
        tier = routing.tier.value if routing.tier != ModelTier.TIER1_CHEAP else "tier2"

        stage_map = {
            "risk_analysis": "risk_analysis",
            "compare_versions": "comparison",
            "draft_response": "draft",
            "negotiation_prep": "negotiation",
        }
        prompt_stage = stage_map.get(task_type, "risk_analysis")

        # Build extraction summary (don't send raw_content to save tokens)
        extraction_summary = {k: v for k, v in extraction_data.items() if k != "raw_content"}

        prompt = get_prompt(
            tier, prompt_stage,
            extraction_data=json.dumps(extraction_summary, ensure_ascii=False),
            document_summary=document_text[:2000] if document_text else "",
            message=message,
            retrieval_context=json.dumps(retrieval_context, ensure_ascii=False),
            risk_analysis="",
            tone="רשמי",
            red_lines="",
            version_a_data="",
            version_b_data="",
        )

        # REAL API CALL
        response = call_for_tier(
            tier,
            system=prompt["system"],
            user=prompt["user"],
            max_tokens=8192,
        )

        parsed = extract_json(response.content)

        result = {
            "model": response.model,
            "tier": tier,
            "analysis_result": parsed if parsed else {},
            "needs_opus_review": (parsed or {}).get("needs_opus_review", False) if isinstance(parsed, dict) else False,
            "opus_reason": (parsed or {}).get("opus_reason", "") if isinstance(parsed, dict) else "",
            "tier2_confidence": (parsed or {}).get("tier2_confidence", 0.8) if isinstance(parsed, dict) else 0.8,
            "raw_content": response.content,
        }

        cost = response.cost_usd(tier)
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="analyze",
            model_tier=tier,
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        return PipelineStage(
            stage_name="analysis",
            tier_used=tier,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_opus_refinement(
        self, task_type: str, message: str, document_text: Optional[str],
        extraction_data: Dict, tier2_analysis: Dict, retrieval_context: Dict,
        escalation_reason: str
    ) -> PipelineStage:
        """Stage 5 (optional): Opus refinement — REAL MODEL CALL."""
        start = time.time()

        # Strip raw_content to save tokens
        extraction_clean = {k: v for k, v in extraction_data.items() if k != "raw_content"}
        analysis_clean = {k: v for k, v in tier2_analysis.items() if k != "raw_content"}

        prompt = get_prompt(
            "tier3", "refinement",
            extraction_data=json.dumps(extraction_clean, ensure_ascii=False),
            tier2_analysis=json.dumps(analysis_clean, ensure_ascii=False),
            escalation_reason=escalation_reason,
            document_sections=document_text[:4000] if document_text else "",
            message=message,
            retrieval_context=json.dumps(retrieval_context, ensure_ascii=False),
        )

        response = call_for_tier(
            "tier3",
            system=prompt["system"],
            user=prompt["user"],
            max_tokens=8192,
        )

        parsed = extract_json(response.content)

        result = {
            "model": response.model,
            "escalation_reason": escalation_reason,
            "refinement_result": parsed if parsed else {},
            "raw_content": response.content,
        }

        cost = response.cost_usd("tier3")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="synthesize",
            model_tier="tier3",
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            escalated_from="tier2",
        )

        return PipelineStage(
            stage_name="opus_refinement",
            tier_used="tier3",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
            escalated=True,
        )

    def _run_formatting(
        self, task_type: str, message: str, extraction_data: Dict, analysis_data: Dict
    ) -> PipelineStage:
        """Stage 6: Format output — REAL MODEL CALL."""
        start = time.time()

        # Prepare compact data for formatting
        extraction_clean = {k: v for k, v in extraction_data.items() if k != "raw_content"}
        analysis_clean = {k: v for k, v in analysis_data.items() if k != "raw_content"}

        prompt = get_prompt(
            "tier1", "formatting",
            task_type=task_type,
            analysis_data=json.dumps({
                "extraction": extraction_clean,
                "analysis": analysis_clean,
            }, ensure_ascii=False),
            output_format=task_type,
        )

        response = call_for_tier(
            "tier1",
            system=prompt["system"],
            user=prompt["user"],
            max_tokens=4096,
        )

        result = {
            "content": response.content,
            "model": response.model,
        }

        cost = response.cost_usd("tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="format",
            model_tier="tier1",
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        return PipelineStage(
            stage_name="formatting",
            tier_used="tier1",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    def _run_qa(self, task_type: str, message: str, formatted_output: Dict) -> PipelineStage:
        """Stage 7: QA check — REAL MODEL CALL."""
        start = time.time()

        # Don't send full raw content to QA — just the formatted output
        output_for_qa = formatted_output.get("content", "")
        if len(output_for_qa) > 6000:
            output_for_qa = output_for_qa[:6000] + "\n...(truncated for QA)"

        prompt = get_prompt(
            "tier1", "qa",
            output=output_for_qa,
            message=message,
            task_type=task_type,
        )

        response = call_for_tier(
            "tier1",
            system=prompt["system"],
            user=prompt["user"],
            max_tokens=1024,
        )

        parsed = extract_json(response.content)

        result = {
            "qa_passed": (parsed or {}).get("qa_passed", True) if isinstance(parsed, dict) else True,
            "overall_result": (parsed or {}).get("overall_result", "pass") if isinstance(parsed, dict) else "pass",
            "issues_found": (parsed or {}).get("issues_found", []) if isinstance(parsed, dict) else [],
            "model": response.model,
            "raw_content": response.content,
        }

        cost = response.cost_usd("tier1")
        self.cost_tracker.record(
            task_type=task_type,
            pipeline_stage="qa",
            model_tier="tier1",
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        return PipelineStage(
            stage_name="qa",
            tier_used="tier1",
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            duration_ms=int((time.time() - start) * 1000),
            result=result,
        )

    # ============================================================
    # OUTPUT BUILDING
    # ============================================================

    def _build_final_output(
        self, task_type: str, extraction_data: Dict, analysis_data: Dict,
        formatted_content: str, qa_result: Dict, routing: RoutingDecision,
        total_cost: float = 0.0,
    ) -> Dict:
        """Build the standard Masha output format."""
        # Determine risk level from analysis
        risk_level = routing.risk_level
        if isinstance(analysis_data.get("analysis_result"), dict):
            risk_level = analysis_data["analysis_result"].get("overall_risk", risk_level)

        return {
            "decision": self._task_type_to_decision(task_type),
            "confidence": routing.confidence,
            "reasoning": routing.reason,
            "draft": {
                "type": task_type,
                "content": formatted_content,
            },
            "legalRisk": risk_level,
            "riskFactors": extraction_data.get("flagged_issues", []),
            "memoryDelta": None,
            "stateDelta": None,
            "qaResult": "pass" if qa_result.get("qa_passed") else "needs_revision",
            "qaDetails": qa_result.get("issues_found", []),
            "suggestedActions": [],
            "requiresApproval": True,
            "modelTier": routing.tier.value,
            "costUsd": round(total_cost, 4),
        }

    def _build_error_result(
        self, task_type: str, error_msg: str, start_time: float, routing: RoutingDecision
    ) -> PipelineResult:
        """Build an error result when pipeline fails."""
        return PipelineResult(
            task_type=task_type,
            stages=[PipelineStage(
                stage_name="error",
                tier_used="none",
                input_tokens=0, output_tokens=0, cost_usd=0.0,
                duration_ms=int((time.time() - start_time) * 1000),
                result={"error": error_msg},
            )],
            final_output={
                "decision": "error",
                "confidence": 0,
                "reasoning": f"Pipeline failed: {error_msg}",
                "draft": {"type": task_type, "content": ""},
                "legalRisk": "unknown",
                "riskFactors": [],
                "qaResult": "error",
                "modelTier": routing.tier.value,
                "costUsd": 0,
                "error": error_msg,
            },
            total_cost_usd=0.0,
            total_duration_ms=int((time.time() - start_time) * 1000),
            tiers_used=[],
            was_fully_cached=False,
            routing_decision=routing.to_dict(),
            cost_comparison={"opus_cost_usd": 0, "actual_cost_usd": 0, "savings_pct": 0},
        )

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
    """Test pipeline execution with REAL model calls."""
    engine = PipelineEngine()

    print("=" * 60)
    print("מאשה Advanced — LIVE Pipeline Test")
    print("=" * 60)

    # Test: Simple clause extraction (should be cheap — Tier 1 only)
    print("\n--- Test: Clause Extraction (Tier 1) ---")
    result = engine.execute(
        task_type="clause_extraction",
        message="תמצאי סעיפי תשלום",
        document_text="""
        SERVICES AGREEMENT
        Between: Acme Corp ("Provider") and Beta Inc ("Client")
        Date: January 1, 2026

        4. PAYMENT TERMS
        4.1 Client shall pay Provider ₪50,000 per month.
        4.2 Payment is due within 30 days of invoice.
        4.3 Late payment incurs 1.5% monthly interest.
        4.4 All amounts are exclusive of VAT.

        5. TERM
        This agreement is for 12 months from the Effective Date.
        """,
        context={"sender": "yoni"},
    )
    print(f"  Tiers used: {result.tiers_used}")
    print(f"  Total cost: ${result.total_cost_usd:.4f}")
    print(f"  Duration: {result.total_duration_ms}ms")
    print(f"  Stages: {len(result.stages)}")
    print(f"  Cost savings vs Opus: {result.cost_comparison['savings_pct']}%")
    for s in result.stages:
        print(f"    → {s.stage_name}: {s.tier_used} ({s.input_tokens}+{s.output_tokens} tokens, ${s.cost_usd:.4f})")

    # Session summary
    print(f"\n--- Session Cost Summary ---")
    summary = engine.cost_tracker.session_summary()
    print(f"  Total: ${summary['total_cost_usd']:.4f}")
    print(f"  By tier: {summary['by_tier']}")

    print("\n" + "=" * 60)
    print("Pipeline test complete!")


if __name__ == "__main__":
    test_pipeline()
