"""
Investigation Agent API Endpoints

Provides endpoints to trigger and monitor automated LangGraph incident investigations.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.incident_service import IncidentService
from app.services.investigation_service import InvestigationService
from app.services.remediation_service import RemediationService
from app.schemas.remediation import RemediationListResponse, RemediationActionResponse
from app.agent.graph import run_investigation_workflow
from app.agent.schemas import (
    InvestigationRunRequest,
    InvestigationRunResponse,
    InvestigationStepInfo,
    EvidenceInfo,
    HypothesisInfo,
    ToolCallInfo,
)
from app.core.logging import logger

router = APIRouter()


def _format_investigation_response(
    investigation,
    analysis_reasoning: Optional[str] = None,
    recommended_remediation: Optional[list] = None,
    retrieved_sources: Optional[list] = None,
) -> InvestigationRunResponse:
    """Formats an Investigation ORM model and related entities into InvestigationRunResponse."""
    steps_info = [
        InvestigationStepInfo(
            step_order=s.step_order,
            title=s.title,
            status=s.status,
            output_summary=s.output_summary,
            created_at=s.created_at,
        )
        for s in (investigation.steps or [])
    ]

    evidence_info = [
        EvidenceInfo(
            id=e.id,
            source_tool=e.source_tool,
            summary=e.summary,
            relevance_score=e.relevance_score,
            raw_payload=e.raw_payload or {},
            collected_at=e.collected_at,
        )
        for e in (investigation.evidence or [])
    ]

    hypotheses_info = [
        HypothesisInfo(
            id=h.id,
            hypothesis_text=h.hypothesis_text,
            status=h.status,
            confidence_score=h.confidence_score,
            supporting_evidence_ids=h.supporting_evidence_ids or [],
            opposing_evidence_ids=h.opposing_evidence_ids or [],
            created_at=h.created_at,
        )
        for h in (investigation.hypotheses or [])
    ]

    tool_calls_info = [
        ToolCallInfo(
            id=t.id,
            tool_name=t.tool_name,
            arguments=t.arguments or {},
            status=t.status,
            execution_time_ms=t.execution_time_ms,
            created_at=t.created_at,
        )
        for t in (investigation.tool_calls or [])
    ]

    return InvestigationRunResponse(
        investigation_id=investigation.id,
        incident_id=investigation.incident_id,
        investigation_number=investigation.investigation_number,
        status=investigation.status,
        probable_root_cause=investigation.probable_root_cause,
        confidence_score=investigation.confidence_score,
        analysis_reasoning=analysis_reasoning,
        recommended_remediation=recommended_remediation or [],
        steps=steps_info,
        evidence=evidence_info,
        hypotheses=hypotheses_info,
        tool_calls=tool_calls_info,
        retrieved_sources=retrieved_sources or [],
        created_at=investigation.created_at,
        completed_at=investigation.completed_at,
    )


@router.post(
    "/{incident_id}/run",
    response_model=InvestigationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger automated LangGraph investigation for an incident",
)
def run_investigation(
    incident_id: uuid.UUID,
    run_req: Optional[InvestigationRunRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Executes the full LangGraph investigation graph for the given incident:
    1. Validates the incident exists.
    2. Initializes or retrieves the investigation record.
    3. Executes the stateful graph (intake, planning, rag, tools, evidence, hypotheses, verification, root cause).
    4. Persists all diagnostic steps, telemetry findings, competing hypotheses, and root cause.
    5. Returns the comprehensive structured investigation response.
    """
    incident_svc = IncidentService(db)
    # Validate incident exists (raises 404 EntityNotFoundException if missing)
    incident = incident_svc.get_incident(incident_id)

    max_iter = run_req.max_iterations if run_req and run_req.max_iterations else 5

    logger.info(f"API triggering investigation run for incident {incident_id} (max_iter={max_iter})")

    # Run LangGraph workflow with robust failure handling
    try:
        final_state = run_investigation_workflow(
            incident_id=str(incident.id),
            max_iterations=max_iter,
            db=db,
        )
    except Exception as e:
        logger.error(f"Unexpected investigation workflow exception for incident {incident_id}: {e}", exc_info=True)
        # Roll back potentially corrupted transaction state
        try:
            db.rollback()
        except Exception:
            pass

        # Persist failure status to investigation record
        try:
            inv_svc = InvestigationService(db)
            investigation = inv_svc.get_by_incident_id(incident.id)
            if investigation:
                investigation.status = "Failed"
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update investigation status to Failed: {db_err}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation workflow failed: {str(e)}",
        )

    if final_state.get("status_outcome") == "failed":
        err_msg = "; ".join(final_state.get("errors", ["Unknown investigation failure"]))
        # Persist failure status to investigation record
        try:
            inv_svc = InvestigationService(db)
            investigation = inv_svc.get_by_incident_id(incident.id)
            if investigation:
                investigation.status = "Failed"
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update investigation status to Failed: {db_err}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation workflow failed: {err_msg}",
        )

    # Reload investigation record with relationships refreshed
    inv_svc = InvestigationService(db)
    investigation = inv_svc.get_by_incident_id(incident.id)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation for incident {incident_id} not found.",
        )

    db.refresh(investigation)

    return _format_investigation_response(
        investigation=investigation,
        analysis_reasoning=final_state.get("analysis_reasoning"),
        recommended_remediation=final_state.get("recommended_remediation", []),
        retrieved_sources=final_state.get("retrieved_sources", []),
    )


@router.get(
    "/{incident_id}",
    response_model=InvestigationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current investigation details for an incident",
)
def get_investigation(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieves the active or completed investigation for an incident, including
    steps, collected evidence, hypotheses, and executed tool calls.
    """
    incident_svc = IncidentService(db)
    incident = incident_svc.get_incident(incident_id)

    inv_svc = InvestigationService(db)
    investigation = inv_svc.get_by_incident_id(incident.id)
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No investigation found for incident {incident_id}.",
        )

    db.refresh(investigation)
    return _format_investigation_response(investigation=investigation)


@router.get(
    "/{investigation_id}/remediations",
    response_model=RemediationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all remediation proposals for an investigation",
)
def list_investigation_remediations(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    List all remediation action proposals associated with the specified investigation.
    """
    remediation_svc = RemediationService(db)
    actions = remediation_svc.list_by_investigation(investigation_id)
    return RemediationListResponse(
        items=[RemediationActionResponse.model_validate(a) for a in actions],
        total=len(actions),
    )


@router.post(
    "/{investigation_id}/remediations/propose",
    response_model=RemediationListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate remediation proposals from investigation recommendations",
)
def propose_investigation_remediations(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Examines investigation conclusions and converts recommended remediation advice into
    formal RemediationAction proposals in PROPOSED status.
    AI creates proposals only; actions cannot execute without human approval.
    """
    remediation_svc = RemediationService(db)
    proposals = remediation_svc.create_proposals_from_investigation(investigation_id)
    return RemediationListResponse(
        items=[RemediationActionResponse.model_validate(p) for p in proposals],
        total=len(proposals),
    )

