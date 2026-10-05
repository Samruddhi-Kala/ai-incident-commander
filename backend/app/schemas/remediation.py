"""
Pydantic Schemas for Phase 7: Remediation Actions and Human Approval Lifecycle
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class RemediationStatus(str, Enum):
    """Controlled remediation lifecycle states."""
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(str, Enum):
    """Standardized operational risk ratings."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RemediationActionType(str, Enum):
    """Allowed simulated remediation action types."""
    RESTART_SERVICE = "restart_service"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    SCALE_SERVICE = "scale_service"
    CLEAR_CACHE = "clear_cache"


class RemediationActionCreate(BaseModel):
    """Payload to create a new remediation proposal."""
    investigation_id: uuid.UUID
    action_name: str = Field(..., description="Action tool identifier (e.g., restart_service, rollback_deployment)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    reasoning: str = Field(..., description="Technical rationale for the proposed remediation")
    risk_level: RiskLevel = Field(default=RiskLevel.HIGH, description="Assessed risk level")
    description: Optional[str] = Field(None, description="Human-readable description of the remediation")
    expected_impact: Optional[str] = Field(None, description="Anticipated impact on service/users")
    rollback_plan: Optional[str] = Field(None, description="Contingency rollback plan")
    status: Optional[str] = Field(RemediationStatus.PROPOSED.value, description="Initial proposal status")


class RemediationApprovalRequest(BaseModel):
    """Payload for human authorization of an action."""
    approved_by: Optional[uuid.UUID] = Field(None, description="Approving human user ID")
    actor_type: str = Field("HUMAN_USER", description="Actor type initiating approval (must be HUMAN_USER)")
    comment: Optional[str] = Field(None, description="Optional sign-off comment or approval rationale")


class RemediationRejectionRequest(BaseModel):
    """Payload for rejecting a proposed action."""
    rejected_by: Optional[uuid.UUID] = Field(None, description="Rejecting human user ID")
    actor_type: str = Field("HUMAN_USER", description="Actor type initiating rejection")
    reason: str = Field(..., min_length=3, description="Mandatory explanation for rejection")


class RemediationSubmitRequest(BaseModel):
    """Payload for submitting a proposal for approval."""
    submitted_by: Optional[uuid.UUID] = Field(None, description="Submitting user or agent ID")
    comment: Optional[str] = Field(None, description="Submission note")


class RemediationExecutionResult(BaseModel):
    """Execution output payload."""
    status: str = Field(..., description="Outcome: COMPLETED or FAILED")
    action: str = Field(..., description="Action type executed")
    started_at: datetime = Field(..., description="Execution start timestamp")
    completed_at: datetime = Field(..., description="Execution completion timestamp")
    execution_time_ms: int = Field(default=0, description="Duration in milliseconds")
    output: Optional[Dict[str, Any]] = Field(None, description="Structured execution results")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    failure_reason: Optional[str] = Field(None, description="Root failure cause if failed")


class RemediationActionResponse(BaseModel):
    """Structured response representing a remediation action entity."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    investigation_id: uuid.UUID
    action_name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    reasoning: str
    risk_level: str
    approval_status: str
    expected_impact: Optional[str] = None
    rollback_plan: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    approval_timestamp: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_embedded_fields(cls, data: Any) -> Any:
        """Extract description, expected_impact, and rollback_plan from parameters if present."""
        if hasattr(data, "parameters") and isinstance(data.parameters, dict):
            params = data.parameters
            # If data is a SQLAlchemy model instance, convert to dict representation for extra attributes
            return {
                "id": getattr(data, "id", None),
                "investigation_id": getattr(data, "investigation_id", None),
                "action_name": getattr(data, "action_name", ""),
                "description": params.get("description") or getattr(data, "action_name", ""),
                "parameters": params,
                "reasoning": getattr(data, "reasoning", ""),
                "risk_level": getattr(data, "risk_level", "HIGH"),
                "approval_status": getattr(data, "approval_status", "PROPOSED"),
                "expected_impact": params.get("expected_impact"),
                "rollback_plan": params.get("rollback_plan"),
                "approved_by": getattr(data, "approved_by", None),
                "approval_timestamp": getattr(data, "approval_timestamp", None),
                "execution_result": getattr(data, "execution_result", None),
                "created_at": getattr(data, "created_at", None),
            }
        elif isinstance(data, dict):
            params = data.get("parameters", {})
            if isinstance(params, dict):
                data.setdefault("description", params.get("description") or data.get("action_name"))
                data.setdefault("expected_impact", params.get("expected_impact"))
                data.setdefault("rollback_plan", params.get("rollback_plan"))
        return data


class RemediationListResponse(BaseModel):
    """List response containing remediation actions."""
    items: List[RemediationActionResponse]
    total: int
