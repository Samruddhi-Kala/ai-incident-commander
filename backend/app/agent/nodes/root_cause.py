"""
Root Cause Analyzer Node

Synthesizes empirical evidence and verification findings into a probable root-cause
determination, articulates alternative explanations, notes uncertainty, and provides
non-executable remediation advice for human operator review (Phase 7 boundary).
Persists the final investigation conclusion to the database.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.agent.llm import LLMService
from app.agent.schemas import VerificationPayload, VerificationItem
from app.models.investigation import Investigation
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.core.logging import logger


def root_cause_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Root Cause Analyzer node:
    1. Compiles verified hypotheses and telemetry evidence.
    2. Synthesizes probable root cause, confidence, and alternative explanations.
    3. Updates investigation record with final status, root cause, and confidence.
    4. Records the final investigation step into the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "root_cause"}

    db = config.get("configurable", {}).get("db") if config else None
    llm = config.get("configurable", {}).get("llm") if config else None
    if llm is None:
        llm = LLMService()

    inv_id_str = state.get("investigation_id")
    inv_uuid = uuid.UUID(inv_id_str) if inv_id_str else None

    # Reconstruct verification payload from state
    verif_items = []
    for v in state.get("verification_results", []):
        verif_items.append(
            VerificationItem(
                hypothesis_title=v.get("hypothesis_title", ""),
                status=v.get("status", "INCONCLUSIVE"),
                confidence=v.get("confidence", 0.5),
                evidence_summaries=v.get("evidence_summaries", []),
                reasoning=v.get("reasoning", ""),
            )
        )
    verif_payload = VerificationPayload(
        verifications=verif_items,
        need_more_evidence=False,
        additional_tools=[],
        reasoning="Verification completed.",
    )

    # Synthesize root cause
    root_cause_result = llm.analyze_root_cause(
        title=state.get("title", ""),
        service_name=state.get("service_name"),
        verification_payload=verif_payload,
        evidence_list=state.get("evidence", []),
    )

    # Determine whether causality was established or remains inconclusive
    verification_results = state.get("verification_results", [])
    has_supported_hypothesis = any(
        v.get("status") in ("SUPPORTED", "PARTIALLY_SUPPORTED")
        for v in verification_results
    )
    is_inconclusive = (not has_supported_hypothesis) or (root_cause_result.confidence < 0.40)

    outcome_status = "Inconclusive" if is_inconclusive else "Completed"
    outcome_state = "inconclusive" if is_inconclusive else "completed"

    # Persist final investigation outcome in database
    if db and inv_uuid:
        investigation = db.get(Investigation, inv_uuid)
        if investigation:
            investigation.status = outcome_status
            investigation.probable_root_cause = root_cause_result.probable_root_cause
            investigation.confidence_score = root_cause_result.confidence
            investigation.completed_at = datetime.now(timezone.utc)
            db.flush()

        step_repo = InvestigationStepRepository(db)
        verdict_text = "Inconclusive root cause" if is_inconclusive else "Determined probable root cause"
        summary = (
            f"{verdict_text} (confidence: {root_cause_result.confidence:.2f}, status: {outcome_status}): "
            f"'{root_cause_result.probable_root_cause}'. "
            f"Formulated {len(root_cause_result.recommended_remediation)} non-executable remediation proposals."
        )
        step_repo.record_step(
            investigation_id=inv_uuid,
            step_order=8,
            title="Step 8 — Root Cause Synthesis & Remediation Guidance",
            status="Completed",
            output_summary=summary,
        )
        db.commit()

    logger.info(
        f"Root cause node completed. Status: {outcome_status}, "
        f"confidence: {root_cause_result.confidence:.2f}."
    )

    return {
        "probable_root_cause": root_cause_result.probable_root_cause,
        "confidence": root_cause_result.confidence,
        "recommended_remediation": root_cause_result.recommended_remediation,
        "analysis_reasoning": root_cause_result.reasoning,
        "status_outcome": outcome_state,
        "current_step": "root_cause",
    }
