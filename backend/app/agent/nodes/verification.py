"""
Verification Node

Evaluates each diagnostic hypothesis against empirical telemetry evidence,
updating hypothesis confidence and determining whether additional evidence collection
is strictly required or if causality has been established.
"""
import uuid
from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.agent.llm import LLMService
from app.core.config import settings
from app.core.logging import logger
from app.models.hypothesis import Hypothesis
from app.repositories.investigation_step_repo import InvestigationStepRepository


_STATUS_MAP = {
    "SUPPORTED": "Verified_Strong",
    "PARTIALLY_SUPPORTED": "Verified_Weak",
    "NOT_SUPPORTED": "Ruled_Out",
    "INCONCLUSIVE": "Proposed",
}


def verification_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Verification node:
    1. Compares competing hypotheses against collected telemetry evidence.
    2. Updates hypothesis verification status and confidence scores.
    3. Persists verification outcomes to the database.
    4. Evaluates if more evidence is required, enforcing iteration and tool limits.
    5. Records the diagnostic step into the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "verification"}

    db = config.get("configurable", {}).get("db") if config else None
    llm = config.get("configurable", {}).get("llm") if config else None
    if llm is None:
        llm = LLMService()

    inv_id_str = state.get("investigation_id")
    inv_uuid = uuid.UUID(inv_id_str) if inv_id_str else None

    hypotheses = state.get("hypotheses", [])
    evidence_list = state.get("evidence", [])

    verification_payload = llm.verify_hypotheses(
        title=state.get("title", ""),
        service_name=state.get("service_name"),
        hypotheses=hypotheses,
        evidence_list=evidence_list,
    )

    verif_results: List[Dict[str, Any]] = []

    # Map verification results back to database hypotheses
    for v_item in verification_payload.verifications:
        db_status = _STATUS_MAP.get(v_item.status.upper(), "Proposed")

        # Find matching hypothesis in state
        matched_h = None
        for h in hypotheses:
            if h.get("title") == v_item.hypothesis_title or v_item.hypothesis_title in h.get("title", ""):
                matched_h = h
                break

        hypo_id = matched_h.get("id") if matched_h else None

        if db and hypo_id:
            try:
                hypo_uuid = uuid.UUID(hypo_id)
                db_hypo = db.get(Hypothesis, hypo_uuid)
                if db_hypo:
                    db_hypo.status = db_status
                    db_hypo.confidence_score = v_item.confidence
                    db.flush()
            except Exception as e:
                logger.warning(f"Failed to update hypothesis {hypo_id} status: {e}")

        verif_results.append({
            "hypothesis_title": v_item.hypothesis_title,
            "hypothesis_id": hypo_id,
            "status": v_item.status,
            "db_status": db_status,
            "confidence": v_item.confidence,
            "evidence_summaries": v_item.evidence_summaries,
            "reasoning": v_item.reasoning,
        })

    if db:
        db.commit()

    # Determine loop condition with strict safety guards
    current_iter = state.get("iteration_count", 1)
    max_iter = state.get("max_iterations") or settings.AGENT_MAX_ITERATIONS
    current_calls = state.get("tool_calls_count", 0)
    max_calls = settings.AGENT_MAX_TOOL_CALLS

    need_more = verification_payload.need_more_evidence
    if need_more:
        if current_iter >= max_iter:
            logger.info(f"Loop guard: Reached max iterations ({current_iter}/{max_iter}); forcing root cause analysis.")
            need_more = False
        elif current_calls >= max_calls:
            logger.info(f"Loop guard: Reached max tool calls ({current_calls}/{max_calls}); forcing root cause analysis.")
            need_more = False

    # Record investigation step in database
    if db and inv_uuid:
        step_repo = InvestigationStepRepository(db)
        supported_count = sum(1 for v in verif_results if "SUPPORTED" in v["status"])
        summary = (
            f"Evaluated {len(verif_results)} hypotheses against {len(evidence_list)} evidence items. "
            f"{supported_count} supported. Need more evidence: {need_more}. "
            f"Reasoning: {verification_payload.reasoning[:160]}..."
        )
        step_repo.record_step(
            investigation_id=inv_uuid,
            step_order=7,
            title="Step 7 — Hypothesis Verification & Evidence Correlation",
            status="Completed",
            output_summary=summary,
        )

    logger.info(f"Verification node completed. Need more evidence: {need_more}.")

    return {
        "verification_results": verif_results,
        "need_more_evidence": need_more,
        "additional_tools": verification_payload.additional_tools if need_more else [],
        "current_step": "verification",
    }
