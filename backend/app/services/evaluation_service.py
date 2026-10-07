"""
AI Investigation Evaluation Service

Evaluates the diagnostic quality and operational rigor of an investigation session.
Computes deterministic heuristic engineering metrics across 5 core dimensions:
1. Evidence Support (25%)
2. Hypothesis Quality (20%)
3. Verification Rigor (25%)
4. RAG Knowledge Relevance (15%)
5. Diagnostic Tool Execution Efficiency (15%)

Note: These metrics are transparent heuristic engineering indicators for auditing and
continuous improvement, not statistically validated academic benchmarks.
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.investigation import Investigation
from app.models.investigation_evaluation import InvestigationEvaluation
from app.repositories.investigation_repo import InvestigationRepository
from app.repositories.investigation_evaluation_repo import InvestigationEvaluationRepository
from app.core.logging import logger


class EvaluationService:
    """
    Evaluates investigation sessions using explainable, deterministic heuristic algorithms.
    """

    def __init__(self, db: Session):
        self.db = db
        self.investigation_repo = InvestigationRepository(db)
        self.evaluation_repo = InvestigationEvaluationRepository(db)

    def get_evaluation(self, investigation_id: uuid.UUID) -> Optional[InvestigationEvaluation]:
        """Fetch the latest evaluation for an investigation."""
        return self.evaluation_repo.get_latest_by_investigation(investigation_id)

    def list_evaluations(self, skip: int = 0, limit: int = 50) -> Tuple[List[InvestigationEvaluation], int]:
        """Fetch paginated evaluations."""
        return self.evaluation_repo.list_with_count(skip=skip, limit=limit)

    def evaluate_investigation(
        self,
        investigation_id: uuid.UUID,
        force: bool = False,
    ) -> InvestigationEvaluation:
        """
        Calculates and persists deterministic heuristic quality scores for an investigation.
        Returns existing evaluation if present unless force=True.
        """
        investigation = self.investigation_repo.get(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation '{investigation_id}' not found.")

        existing = self.evaluation_repo.get_latest_by_investigation(investigation_id)
        if existing and not force:
            logger.info(f"Returning existing evaluation {existing.id} for investigation {investigation_id}")
            return existing

        # Extract data structures from investigation
        evidence_list = investigation.evidence or []
        hypotheses_list = investigation.hypotheses or []
        tool_calls_list = investigation.tool_calls or []
        steps_list = investigation.steps or []

        # ---------------------------------------------------------------------
        # 1. Evidence Support Score (0 - 100)
        # ---------------------------------------------------------------------
        ev_count = len(evidence_list)
        if ev_count == 0:
            evidence_count_score = 20.0
            avg_relevance = 0.0
        elif ev_count == 1:
            evidence_count_score = 55.0
            avg_relevance = sum((e.relevance_score or 0.5) for e in evidence_list) / ev_count
        elif ev_count == 2:
            evidence_count_score = 75.0
            avg_relevance = sum((e.relevance_score or 0.5) for e in evidence_list) / ev_count
        else:
            evidence_count_score = 90.0
            avg_relevance = sum((e.relevance_score or 0.5) for e in evidence_list) / ev_count

        evidence_score = round(0.4 * evidence_count_score + 0.6 * (avg_relevance * 100.0), 1)
        evidence_score = max(0.0, min(100.0, evidence_score))

        # ---------------------------------------------------------------------
        # 2. Hypothesis Quality Score (0 - 100)
        # ---------------------------------------------------------------------
        hyp_count = len(hypotheses_list)
        if hyp_count == 0:
            hyp_score_val = 20.0
        elif hyp_count == 1:
            hyp_score_val = 55.0  # Solo hypothesis: lack of competing hypotheses
        elif hyp_count == 2:
            hyp_score_val = 80.0  # Healthy competing pair
        else:
            hyp_score_val = 95.0  # Thorough exploration

        # Quality bonus for well-calibrated confidence
        has_calibrated_conf = any(h.confidence_score is not None for h in hypotheses_list)
        if has_calibrated_conf and hyp_count > 0:
            hyp_score_val = min(100.0, hyp_score_val + 5.0)

        hypothesis_score = round(hyp_score_val, 1)

        # ---------------------------------------------------------------------
        # 3. Verification Rigor Score (0 - 100)
        # ---------------------------------------------------------------------
        if hyp_count == 0:
            verification_score = 25.0
        else:
            evaluated_hyps = [h for h in hypotheses_list if h.status != "PENDING"]
            verified_ratio = len(evaluated_hyps) / hyp_count
            supported_count = sum(1 for h in hypotheses_list if h.status == "SUPPORTED")
            not_supported_count = sum(1 for h in hypotheses_list if h.status == "NOT_SUPPORTED")

            base_ver = verified_ratio * 70.0
            # Rigor bonus: ruling out an incorrect hypothesis shows rigorous negative testing
            if not_supported_count > 0:
                base_ver += 15.0
            # Rigor bonus: reaching definitive supported conclusion
            if supported_count > 0:
                base_ver += 15.0
            verification_score = round(min(100.0, max(15.0, base_ver)), 1)

        # ---------------------------------------------------------------------
        # 4. RAG Knowledge Relevance Score (0 - 100)
        # ---------------------------------------------------------------------
        rag_steps = [
            s for s in steps_list
            if any(term in s.title.lower() for term in ["rag", "knowledge", "runbook", "context"])
        ]
        if rag_steps:
            # Check if relevant content was mentioned in step output
            meaningful_rag = any(len(s.output_summary or "") > 40 for s in rag_steps)
            rag_score = 90.0 if meaningful_rag else 75.0
        else:
            # Investigation proceeded with baseline knowledge without runbooks
            rag_score = 50.0

        # ---------------------------------------------------------------------
        # 5. Tool Execution Efficiency Score (0 - 100)
        # ---------------------------------------------------------------------
        tc_count = len(tool_calls_list)
        if tc_count == 0:
            tool_efficiency_score = 30.0  # No diagnostic verification attempted
        else:
            successful_calls = sum(1 for t in tool_calls_list if t.status == "SUCCESS")
            success_rate = successful_calls / tc_count

            # Base score from success rate
            tool_base = success_rate * 85.0

            # Redundancy penalty: detect identical duplicate calls
            seen_signatures = set()
            duplicates = 0
            for t in tool_calls_list:
                sig = (t.tool_name, json.dumps(t.arguments or {}, sort_keys=True))
                if sig in seen_signatures:
                    duplicates += 1
                seen_signatures.add(sig)

            redundancy_penalty = duplicates * 12.0

            # Volume penalty: > 8 tool calls indicates exploration wandering
            volume_penalty = max(0.0, (tc_count - 8) * 3.0)

            tool_efficiency_score = round(min(100.0, max(20.0, tool_base + 15.0 - redundancy_penalty - volume_penalty)), 1)

        # ---------------------------------------------------------------------
        # Overall Weighted Score (0 - 100)
        # ---------------------------------------------------------------------
        weighted_score = (
            0.25 * evidence_score +
            0.20 * hypothesis_score +
            0.25 * verification_score +
            0.15 * rag_score +
            0.15 * tool_efficiency_score
        )

        # Outcome status adjustment
        outcome_factor = 1.0
        if investigation.status == "Inconclusive":
            # Inconclusive investigations have diagnostic value but missed root cause
            outcome_factor = 0.85
        elif investigation.status == "Failed":
            outcome_factor = 0.50

        overall_score = round(min(100.0, max(0.0, weighted_score * outcome_factor)), 1)

        # ---------------------------------------------------------------------
        # Explainable Reasoning Breakdown
        # ---------------------------------------------------------------------
        evidence_feedback = (
            f"Collected {ev_count} evidence items with an average relevance score of {avg_relevance:.2f}."
            if ev_count > 0 else "No structured evidence was collected."
        )
        hyp_feedback = (
            f"Formulated {hyp_count} competing hypotheses."
            if hyp_count > 1 else (
                f"Formulated {hyp_count} hypothesis. Additional competing hypotheses recommended."
                if hyp_count == 1 else "No hypotheses were formulated."
            )
        )
        ver_feedback = (
            f"Verification tested {len([h for h in hypotheses_list if h.status != 'PENDING'])}/{hyp_count} hypotheses."
            if hyp_count > 0 else "No verification testing conducted."
        )
        rag_feedback = (
            f"RAG knowledge engine actively referenced in {len(rag_steps)} investigation steps."
            if rag_steps else "Investigation proceeded without explicit runbook context."
        )
        tool_feedback = (
            f"Executed {tc_count} diagnostic tool calls ({sum(1 for t in tool_calls_list if t.status == 'SUCCESS')}/{tc_count} successful)."
            if tc_count > 0 else "No diagnostic tools were executed."
        )

        evaluation_reasoning = (
            f"Investigation Quality Score: {overall_score:.1f}/100 ({investigation.status}).\n"
            f"• Evidence Support: {evidence_score:.1f}/100 — {evidence_feedback}\n"
            f"• Hypothesis Quality: {hypothesis_score:.1f}/100 — {hyp_feedback}\n"
            f"• Verification Rigor: {verification_score:.1f}/100 — {ver_feedback}\n"
            f"• RAG Relevance: {rag_score:.1f}/100 — {rag_feedback}\n"
            f"• Tool Efficiency: {tool_efficiency_score:.1f}/100 — {tool_feedback}\n\n"
            f"Confidence: {(investigation.confidence_score or 0.0) * 100:.0f}%. "
            f"Probable Root Cause: {investigation.probable_root_cause or 'Inconclusive'}. "
            f"Note: Evaluated using deterministic heuristic engineering metrics."
        )

        metrics_breakdown = {
            "evidence": {
                "score": evidence_score,
                "weight": 0.25,
                "count": ev_count,
                "average_relevance": round(avg_relevance, 2),
                "feedback": evidence_feedback,
            },
            "hypothesis": {
                "score": hypothesis_score,
                "weight": 0.20,
                "count": hyp_count,
                "feedback": hyp_feedback,
            },
            "verification": {
                "score": verification_score,
                "weight": 0.25,
                "tested_count": len([h for h in hypotheses_list if h.status != "PENDING"]),
                "feedback": ver_feedback,
            },
            "rag": {
                "score": rag_score,
                "weight": 0.15,
                "steps_referencing_rag": len(rag_steps),
                "feedback": rag_feedback,
            },
            "tool_efficiency": {
                "score": tool_efficiency_score,
                "weight": 0.15,
                "total_calls": tc_count,
                "successful_calls": sum(1 for t in tool_calls_list if t.status == "SUCCESS"),
                "feedback": tool_feedback,
            },
            "outcome": {
                "status": investigation.status,
                "confidence_score": investigation.confidence_score,
                "factor_applied": outcome_factor,
            },
        }

        if existing and force:
            existing.overall_score = overall_score
            existing.evidence_score = evidence_score
            existing.hypothesis_score = hypothesis_score
            existing.verification_score = verification_score
            existing.rag_score = rag_score
            existing.tool_efficiency_score = tool_efficiency_score
            existing.evaluation_reasoning = evaluation_reasoning
            existing.metrics_breakdown = metrics_breakdown
            existing.created_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated evaluation {existing.id} for investigation {investigation_id}")
            return existing

        eval_record = InvestigationEvaluation(
            investigation_id=investigation_id,
            overall_score=overall_score,
            evidence_score=evidence_score,
            hypothesis_score=hypothesis_score,
            verification_score=verification_score,
            rag_score=rag_score,
            tool_efficiency_score=tool_efficiency_score,
            evaluation_reasoning=evaluation_reasoning,
            metrics_breakdown=metrics_breakdown,
            created_at=datetime.now(timezone.utc),
        )

        created = self.evaluation_repo.create(eval_record)
        logger.info(f"Created evaluation {created.id} for investigation {investigation_id}")
        return created
