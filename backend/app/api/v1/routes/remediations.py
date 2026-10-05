"""
Remediation Action API Endpoints

Provides endpoints for creating, retrieving, approving, rejecting, and executing remediation actions.
Enforces human authorization barriers and simulated safe execution.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.remediation_service import RemediationService
from app.schemas.remediation import (
    RemediationActionCreate,
    RemediationActionResponse,
    RemediationApprovalRequest,
    RemediationRejectionRequest,
    RemediationSubmitRequest,
    RemediationStatus,
)
from app.remediation.exceptions import RemediationExecutionError
from app.core.logging import logger

router = APIRouter()


@router.post(
    "",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a remediation proposal",
)
def create_remediation(
    payload: RemediationActionCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new remediation proposal in PROPOSED status for an active investigation.
    Validates the action name and parameters against the registered actions catalog.
    """
    service = RemediationService(db)
    action = service.create_proposal(data=payload, actor_type="HUMAN_USER")
    return action


@router.get(
    "/{remediation_id}",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve remediation action details",
)
def get_remediation(
    remediation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieves full details of a remediation action including its lifecycle status,
    parameters, reasoning, risk level, approver, and execution results.
    """
    service = RemediationService(db)
    action = service.get_action(remediation_id)
    return action


@router.post(
    "/{remediation_id}/submit",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a proposed remediation for human approval",
)
def submit_remediation_for_approval(
    remediation_id: uuid.UUID,
    payload: Optional[RemediationSubmitRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Transitions an action from PROPOSED to PENDING_APPROVAL.
    """
    service = RemediationService(db)
    submitted_by = payload.submitted_by if payload else None
    comment = payload.comment if payload else None
    action = service.submit_for_approval(
        remediation_id=remediation_id,
        actor_id=submitted_by,
        comment=comment,
    )
    return action


@router.post(
    "/{remediation_id}/approve",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a pending remediation action",
)
def approve_remediation(
    remediation_id: uuid.UUID,
    payload: Optional[RemediationApprovalRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Explicit human authorization of a remediation action in PENDING_APPROVAL status.
    AI agents cannot approve actions (SYSTEM_AGENT actor is rejected).
    """
    service = RemediationService(db)
    approved_by = payload.approved_by if payload else None
    actor_type = payload.actor_type if payload else "HUMAN_USER"
    comment = payload.comment if payload else None

    action = service.approve_action(
        remediation_id=remediation_id,
        approved_by=approved_by,
        actor_type=actor_type,
        comment=comment,
    )
    return action


@router.post(
    "/{remediation_id}/reject",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a pending remediation action",
)
def reject_remediation(
    remediation_id: uuid.UUID,
    payload: RemediationRejectionRequest,
    db: Session = Depends(get_db),
):
    """
    Explicit rejection of a proposed remediation action.
    A rejection reason is required and prevents subsequent execution.
    """
    service = RemediationService(db)
    action = service.reject_action(
        remediation_id=remediation_id,
        rejected_by=payload.rejected_by,
        actor_type=payload.actor_type,
        reason=payload.reason,
    )
    return action


@router.post(
    "/{remediation_id}/execute",
    response_model=RemediationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an approved remediation action",
)
def execute_remediation(
    remediation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Executes an action that has received explicit human approval (status == APPROVED).
    Executes deterministically in simulated mode with zero side-effects.
    Fails safely if status != APPROVED or if simulation fails.
    """
    service = RemediationService(db)
    action = service.execute_action(remediation_id=remediation_id)

    # If execution failed, raise RemediationExecutionError to yield HTTP 500
    if action.approval_status == RemediationStatus.FAILED.value:
        fail_reason = "Unknown execution error"
        if isinstance(action.execution_result, dict):
            fail_reason = action.execution_result.get("failure_reason") or action.execution_result.get("error") or fail_reason
        raise RemediationExecutionError(
            message=f"Remediation execution failed: {fail_reason}",
            details={"remediation_id": str(remediation_id), "execution_result": action.execution_result},
        )

    return action
