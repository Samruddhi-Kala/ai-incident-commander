"""
Remediation Service

Coordinates the complete remediation lifecycle:
PROPOSED → PENDING_APPROVAL → APPROVED / REJECTED → EXECUTING → COMPLETED / FAILED

Enforces:
- AI proposes; human approves.
- Strictly prohibited: AI self-approval, autonomous execution, unapproved execution.
- Only registered actions may execute.
- Append-only transactional audit logging for all lifecycle transitions.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.remediation_action import RemediationAction
from app.models.investigation import Investigation
from app.models.incident import Incident
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.remediation_action_repo import RemediationActionRepository
from app.repositories.investigation_repo import InvestigationRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.remediation.registry import RemediationRegistry, remediation_registry
from app.remediation.executor import RemediationExecutor
from app.remediation.exceptions import (
    RemediationNotFoundError,
    RemediationInvestigationNotFoundError,
    InvalidActionTypeError,
    RemediationParameterError,
    RemediationStateError,
    RemediationApprovalError,
    RemediationExecutionError,
)
from app.schemas.remediation import (
    RemediationStatus,
    RiskLevel,
    RemediationActionCreate,
    RemediationExecutionResult,
)
from app.core.logging import logger


class RemediationService:
    """
    Service managing remediation proposals, approval barriers, execution dispatch, and audit trails.
    """

    def __init__(
        self,
        db: Session,
        registry: Optional[RemediationRegistry] = None,
        executor: Optional[RemediationExecutor] = None,
    ):
        self.db = db
        self.remediation_repo = RemediationActionRepository(db)
        self.investigation_repo = InvestigationRepository(db)
        self.audit_log_repo = AuditLogRepository(db)
        self.registry = registry or remediation_registry
        self.executor = executor or RemediationExecutor(self.registry)

    def _resolve_user_id(self, user_id: Optional[uuid.UUID]) -> Optional[uuid.UUID]:
        """Verify user existence in DB to respect foreign key constraints safely."""
        if not user_id:
            return None
        user = self.db.get(User, user_id)
        return user.id if user else None

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get_action(self, remediation_id: uuid.UUID) -> RemediationAction:
        """Retrieve remediation action by ID or raise RemediationNotFoundError."""
        action = self.remediation_repo.get(remediation_id)
        if not action:
            raise RemediationNotFoundError(
                f"Remediation action with ID '{remediation_id}' not found.",
                details={"remediation_id": str(remediation_id)},
            )
        return action

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[RemediationAction]:
        """List all remediation actions for a specific investigation."""
        inv = self.investigation_repo.get(investigation_id)
        if not inv:
            raise RemediationInvestigationNotFoundError(
                f"Investigation '{investigation_id}' not found.",
                details={"investigation_id": str(investigation_id)},
            )
        return self.remediation_repo.list_by_investigation(investigation_id)

    # -------------------------------------------------------------------------
    # 1. Proposal Creation (PROPOSED)
    # -------------------------------------------------------------------------

    def create_proposal(
        self,
        data: RemediationActionCreate,
        actor_type: str = "SYSTEM_AGENT",
        actor_id: Optional[uuid.UUID] = None,
    ) -> RemediationAction:
        """
        Create a new remediation action proposal.

        Validates:
        - Investigation existence
        - Action registration in catalog
        - Parameter conformance to schema
        """
        # Validate investigation
        inv = self.investigation_repo.get(data.investigation_id)
        if not inv:
            raise RemediationInvestigationNotFoundError(
                f"Investigation '{data.investigation_id}' not found.",
                details={"investigation_id": str(data.investigation_id)},
            )

        # Validate action registration
        action_adapter = self.registry.get(data.action_name)
        if not action_adapter:
            raise InvalidActionTypeError(
                f"Unknown remediation action type '{data.action_name}'. "
                f"Must be one of: {[a['action_name'] for a in self.registry.list_actions()]}"
            )

        # Validate parameters against action adapter schema
        action_adapter.validate_parameters(data.parameters)

        # Embed extra context into parameters payload for persistence
        persisted_params = dict(data.parameters)
        if data.description:
            persisted_params["description"] = data.description
        if data.expected_impact:
            persisted_params["expected_impact"] = data.expected_impact
        if data.rollback_plan:
            persisted_params["rollback_plan"] = data.rollback_plan

        initial_status = data.status or RemediationStatus.PROPOSED.value
        # Ensure status is valid initial state (PROPOSED or PENDING_APPROVAL)
        if initial_status not in (RemediationStatus.PROPOSED.value, RemediationStatus.PENDING_APPROVAL.value):
            initial_status = RemediationStatus.PROPOSED.value

        action = RemediationAction(
            id=uuid.uuid4(),
            investigation_id=data.investigation_id,
            action_name=data.action_name,
            parameters=persisted_params,
            reasoning=data.reasoning,
            risk_level=data.risk_level.value if isinstance(data.risk_level, RiskLevel) else data.risk_level,
            approval_status=initial_status,
        )
        self.db.add(action)
        self.db.flush()

        # Audit log entry
        audit_payload = {
            "remediation_id": str(action.id),
            "investigation_id": str(data.investigation_id),
            "action_name": data.action_name,
            "risk_level": action.risk_level,
            "status": action.approval_status,
            "parameters": data.parameters,
            "reasoning": data.reasoning,
        }
        resolved_actor_id = self._resolve_user_id(actor_id)
        audit = AuditLog(
            incident_id=inv.incident_id,
            actor_id=resolved_actor_id,
            remediation_action_id=action.id,
            actor_type=actor_type,
            action_type="remediation.proposed",
            payload=audit_payload,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(action)

        logger.info(
            f"Created remediation proposal {action.id} ('{action.action_name}', "
            f"risk={action.risk_level}, status={action.approval_status})"
        )
        return action

    # -------------------------------------------------------------------------
    # 2. Lifecycle Transition: Submit for Approval (PROPOSED → PENDING_APPROVAL)
    # -------------------------------------------------------------------------

    def submit_for_approval(
        self,
        remediation_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
        actor_type: str = "HUMAN_USER",
        comment: Optional[str] = None,
    ) -> RemediationAction:
        """
        Transition a proposal from PROPOSED to PENDING_APPROVAL.
        """
        action = self.get_action(remediation_id)

        if action.approval_status != RemediationStatus.PROPOSED.value:
            raise RemediationStateError(
                f"Cannot submit remediation with status '{action.approval_status}' for approval. "
                f"Only PROPOSED actions can be submitted."
            )

        action.approval_status = RemediationStatus.PENDING_APPROVAL.value
        self.db.flush()

        incident_id = action.investigation.incident_id if action.investigation else None
        resolved_actor_id = self._resolve_user_id(actor_id)
        audit = AuditLog(
            incident_id=incident_id,
            actor_id=resolved_actor_id,
            remediation_action_id=action.id,
            actor_type=actor_type,
            action_type="remediation.submitted_for_approval",
            payload={
                "remediation_id": str(action.id),
                "action_name": action.action_name,
                "previous_status": RemediationStatus.PROPOSED.value,
                "new_status": RemediationStatus.PENDING_APPROVAL.value,
                "comment": comment,
            },
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(action)

        logger.info(f"Remediation {action.id} submitted for approval (status=PENDING_APPROVAL)")
        return action

    # -------------------------------------------------------------------------
    # 3. Human Approval (PENDING_APPROVAL → APPROVED)
    # -------------------------------------------------------------------------

    def approve_action(
        self,
        remediation_id: uuid.UUID,
        approved_by: Optional[uuid.UUID] = None,
        actor_type: str = "HUMAN_USER",
        comment: Optional[str] = None,
    ) -> RemediationAction:
        """
        Explicit human approval of a pending remediation action.

        Strict Rules:
        - AI cannot approve actions (SYSTEM_AGENT is rejected).
        - Action must be in PENDING_APPROVAL status.
        - Already approved actions cannot be re-approved.
        - Rejected actions cannot be approved.
        - Completed/failed actions cannot be approved.
        """
        if actor_type == "SYSTEM_AGENT":
            raise RemediationApprovalError(
                "AI agents cannot approve remediation actions. Explicit human approval is required."
            )

        action = self.get_action(remediation_id)

        if action.approval_status == RemediationStatus.APPROVED.value:
            raise RemediationStateError("Remediation action is already approved.")
        if action.approval_status == RemediationStatus.REJECTED.value:
            raise RemediationStateError("Cannot approve an already rejected remediation.")
        if action.approval_status in (
            RemediationStatus.COMPLETED.value,
            RemediationStatus.FAILED.value,
            RemediationStatus.EXECUTING.value,
        ):
            raise RemediationStateError(
                f"Cannot approve remediation in terminal or active status '{action.approval_status}'."
            )
        if action.approval_status == RemediationStatus.PROPOSED.value:
            raise RemediationStateError(
                "Remediation action must be in PENDING_APPROVAL status before it can be approved. "
                "Submit it for approval first."
            )

        now = datetime.now(timezone.utc)
        resolved_approver_id = self._resolve_user_id(approved_by)
        action.approval_status = RemediationStatus.APPROVED.value
        action.approved_by = resolved_approver_id
        action.approval_timestamp = now
        self.db.flush()

        incident_id = action.investigation.incident_id if action.investigation else None
        audit = AuditLog(
            incident_id=incident_id,
            actor_id=resolved_approver_id,
            remediation_action_id=action.id,
            actor_type="HUMAN_USER",
            action_type="remediation.approved",
            payload={
                "remediation_id": str(action.id),
                "action_name": action.action_name,
                "approved_by": str(approved_by) if approved_by else None,
                "approval_timestamp": now.isoformat(),
                "comment": comment,
            },
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(action)

        logger.info(f"Remediation {action.id} APPROVED by user '{approved_by}'")
        return action

    # -------------------------------------------------------------------------
    # 4. Human Rejection (PENDING_APPROVAL → REJECTED)
    # -------------------------------------------------------------------------

    def reject_action(
        self,
        remediation_id: uuid.UUID,
        rejected_by: Optional[uuid.UUID] = None,
        actor_type: str = "HUMAN_USER",
        reason: str = "",
    ) -> RemediationAction:
        """
        Explicit rejection of a proposed remediation action.

        Rules:
        - Reason is required.
        - Cannot reject an already approved action.
        - Cannot reject an already completed or failed action.
        """
        if not reason or not reason.strip():
            raise RemediationParameterError("Rejection requires an explicit explanation reason.")

        action = self.get_action(remediation_id)

        if action.approval_status == RemediationStatus.APPROVED.value:
            raise RemediationStateError("Cannot reject an already approved remediation.")
        if action.approval_status == RemediationStatus.REJECTED.value:
            raise RemediationStateError("Remediation action is already rejected.")
        if action.approval_status in (
            RemediationStatus.COMPLETED.value,
            RemediationStatus.FAILED.value,
            RemediationStatus.EXECUTING.value,
        ):
            raise RemediationStateError(
                f"Cannot reject remediation in status '{action.approval_status}'."
            )

        now = datetime.now(timezone.utc)
        action.approval_status = RemediationStatus.REJECTED.value
        action.execution_result = {
            "status": "REJECTED",
            "rejection_reason": reason.strip(),
            "rejected_by": str(rejected_by) if rejected_by else None,
            "rejected_at": now.isoformat(),
        }
        self.db.flush()

        incident_id = action.investigation.incident_id if action.investigation else None
        resolved_rejecter_id = self._resolve_user_id(rejected_by)
        audit = AuditLog(
            incident_id=incident_id,
            actor_id=resolved_rejecter_id,
            remediation_action_id=action.id,
            actor_type=actor_type,
            action_type="remediation.rejected",
            payload={
                "remediation_id": str(action.id),
                "action_name": action.action_name,
                "rejected_by": str(rejected_by) if rejected_by else None,
                "rejection_reason": reason.strip(),
                "timestamp": now.isoformat(),
            },
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(action)

        logger.info(f"Remediation {action.id} REJECTED: {reason}")
        return action

    # -------------------------------------------------------------------------
    # 5. Execution (APPROVED → EXECUTING → COMPLETED / FAILED)
    # -------------------------------------------------------------------------

    def execute_action(
        self,
        remediation_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
        actor_type: str = "HUMAN_USER",
    ) -> RemediationAction:
        """
        Execute an approved simulated remediation action.

        Guarantees:
        - Only APPROVED actions can execute.
        - Transitions to EXECUTING before dispatch.
        - Persists COMPLETED or FAILED outcome, duration, and output.
        - Logs audit events for execution start, completion, or failure.
        - Never leaves record stuck in EXECUTING.
        """
        action = self.get_action(remediation_id)

        # Enforce lifecycle transition rules
        if action.approval_status == RemediationStatus.REJECTED.value:
            raise RemediationStateError("Cannot execute a rejected remediation action.")
        if action.approval_status in (RemediationStatus.PROPOSED.value, RemediationStatus.PENDING_APPROVAL.value):
            raise RemediationStateError(
                f"Cannot execute unapproved remediation in status '{action.approval_status}'. "
                f"Explicit human approval is required before execution."
            )
        if action.approval_status == RemediationStatus.COMPLETED.value:
            raise RemediationStateError("Remediation action has already completed.")
        if action.approval_status == RemediationStatus.FAILED.value:
            raise RemediationStateError("Failed remediation cannot be re-executed without a new proposal.")
        if action.approval_status == RemediationStatus.EXECUTING.value:
            raise RemediationStateError("Remediation action is already executing.")

        # Transition to EXECUTING
        now = datetime.now(timezone.utc)
        action.approval_status = RemediationStatus.EXECUTING.value
        action.execution_result = {
            "status": "EXECUTING",
            "started_at": now.isoformat(),
        }
        self.db.flush()

        incident_id = action.investigation.incident_id if action.investigation else None
        resolved_actor_id = self._resolve_user_id(actor_id)
        audit_start = AuditLog(
            incident_id=incident_id,
            actor_id=resolved_actor_id,
            remediation_action_id=action.id,
            actor_type=actor_type,
            action_type="remediation.execution_started",
            payload={
                "remediation_id": str(action.id),
                "action_name": action.action_name,
                "started_at": now.isoformat(),
            },
        )
        self.db.add(audit_start)
        self.db.commit()

        # Dispatch execution
        try:
            exec_result: RemediationExecutionResult = self.executor.execute(
                action_name=action.action_name,
                parameters=action.parameters,
                approval_status=RemediationStatus.APPROVED.value,
            )

            if exec_result.status == RemediationStatus.COMPLETED.value:
                action.approval_status = RemediationStatus.COMPLETED.value
                action.execution_result = exec_result.model_dump(mode="json")
                self.db.flush()

                audit_done = AuditLog(
                    incident_id=incident_id,
                    actor_id=resolved_actor_id,
                    remediation_action_id=action.id,
                    actor_type=actor_type,
                    action_type="remediation.execution_completed",
                    payload={
                        "remediation_id": str(action.id),
                        "action_name": action.action_name,
                        "status": RemediationStatus.COMPLETED.value,
                        "execution_time_ms": exec_result.execution_time_ms,
                        "output": exec_result.output,
                    },
                )
                self.db.add(audit_done)
                self.db.commit()
                self.db.refresh(action)
                return action

            else:
                # Executor returned FAILED
                action.approval_status = RemediationStatus.FAILED.value
                action.execution_result = exec_result.model_dump(mode="json")
                self.db.flush()

                audit_fail = AuditLog(
                    incident_id=incident_id,
                    actor_id=resolved_actor_id,
                    remediation_action_id=action.id,
                    actor_type=actor_type,
                    action_type="remediation.execution_failed",
                    payload={
                        "remediation_id": str(action.id),
                        "action_name": action.action_name,
                        "status": RemediationStatus.FAILED.value,
                        "failure_reason": exec_result.failure_reason,
                        "error": exec_result.error,
                    },
                )
                self.db.add(audit_fail)
                self.db.commit()
                self.db.refresh(action)
                return action

        except Exception as exc:
            logger.error(f"Unexpected exception during remediation execution: {exc}")
            self.db.rollback()
            # Reload and record failure state
            action = self.remediation_repo.get(remediation_id)
            if action:
                action.approval_status = RemediationStatus.FAILED.value
                action.execution_result = {
                    "status": "FAILED",
                    "failure_reason": str(exc),
                    "error": str(exc),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
                audit_fail = AuditLog(
                    incident_id=incident_id,
                    actor_id=actor_id,
                    remediation_action_id=action.id,
                    actor_type=actor_type,
                    action_type="remediation.execution_failed",
                    payload={
                        "remediation_id": str(action.id),
                        "action_name": action.action_name,
                        "status": "FAILED",
                        "failure_reason": str(exc),
                    },
                )
                self.db.add(action)
                self.db.add(audit_fail)
                self.db.commit()
                self.db.refresh(action)
            return action

    # -------------------------------------------------------------------------
    # 6. Phase 6 Integration: Convert Recommendations to Proposals
    # -------------------------------------------------------------------------

    def create_proposals_from_investigation(
        self,
        investigation_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> List[RemediationAction]:
        """
        Examine an investigation's recommended remediation text (from Phase 6)
        and formulate structured RemediationAction proposals in PROPOSED status.

        Crucial boundary:
        - Phase 6 agent is read-only and never executes actions.
        - Proposals are created in PROPOSED status awaiting human review.
        """
        inv = self.investigation_repo.get(investigation_id)
        if not inv:
            raise RemediationInvestigationNotFoundError(
                f"Investigation '{investigation_id}' not found.",
                details={"investigation_id": str(investigation_id)},
            )

        # Discover service name from incident
        service_name = "target-service"
        if inv.incident and inv.incident.service:
            service_name = inv.incident.service.name

        # Extract recommendations from investigation steps
        recommendation_texts: List[str] = []
        for step in inv.steps:
            if "remediation" in step.title.lower() or "root cause" in step.title.lower():
                summary = step.output_summary or ""
                recommendation_texts.append(summary)

        # If no step text found, fallback to probable_root_cause
        if not recommendation_texts and inv.probable_root_cause:
            recommendation_texts.append(inv.probable_root_cause)

        combined_text = " ".join(recommendation_texts).lower()
        proposals_to_create: List[RemediationActionCreate] = []

        # Heuristic mapping from diagnostic recommendations to safe registered proposals
        if "rollback" in combined_text or "roll back" in combined_text or "revert" in combined_text:
            proposals_to_create.append(
                RemediationActionCreate(
                    investigation_id=investigation_id,
                    action_name="rollback_deployment",
                    parameters={"service": service_name, "target_version": "v2.5.0"},
                    reasoning=f"Investigation identified regression introduced in recent deployment on '{service_name}'.",
                    risk_level=RiskLevel.HIGH,
                    description=f"Roll back deployment of '{service_name}' to previous verified version v2.5.0.",
                    expected_impact="Restores baseline application binary and connection pool configuration.",
                    rollback_plan=f"Re-deploy original release if rollback fails to stabilize metrics.",
                )
            )

        if "restart" in combined_text:
            proposals_to_create.append(
                RemediationActionCreate(
                    investigation_id=investigation_id,
                    action_name="restart_service",
                    parameters={"service": service_name, "grace_period_seconds": 30},
                    reasoning=f"Graceful restart to clear degraded instances and unblock socket exhaustion on '{service_name}'.",
                    risk_level=RiskLevel.MEDIUM,
                    description=f"Graceful rolling restart of '{service_name}' pods/instances.",
                    expected_impact="Brief reallocation of active requests across remaining healthy instances.",
                    rollback_plan="Instances restart sequentially with readiness probes.",
                )
            )

        if "scale" in combined_text or "capacity" in combined_text:
            proposals_to_create.append(
                RemediationActionCreate(
                    investigation_id=investigation_id,
                    action_name="scale_service",
                    parameters={"service": service_name, "replicas": 5},
                    reasoning=f"Scale capacity for '{service_name}' to accommodate elevated processing queue.",
                    risk_level=RiskLevel.MEDIUM,
                    description=f"Scale '{service_name}' replica count to 5.",
                    expected_impact="Increased compute capacity and reduced queuing delays.",
                    rollback_plan="Scale back to baseline replicas once error rate normalizes.",
                )
            )

        if "cache" in combined_text:
            proposals_to_create.append(
                RemediationActionCreate(
                    investigation_id=investigation_id,
                    action_name="clear_cache",
                    parameters={"service": service_name, "cache_type": "redis"},
                    reasoning=f"Flush stale cached state or connection entries for '{service_name}'.",
                    risk_level=RiskLevel.LOW,
                    description=f"Clear redis cache keys for '{service_name}'.",
                    expected_impact="Temporary increase in database cache misses as keys repopulate.",
                    rollback_plan="Cache naturally warms up as requests arrive.",
                )
            )

        # If no recognized operational remediation keywords were matched, safely skip proposal creation
        if not proposals_to_create:
            logger.info(
                f"No recognized operational remediation keywords found for investigation {investigation_id}. "
                f"Skipping remediation proposal creation."
            )
            return []

        created_records: List[RemediationAction] = []
        for prop in proposals_to_create:
            created = self.create_proposal(
                data=prop,
                actor_type="SYSTEM_AGENT",
                actor_id=actor_id,
            )
            created_records.append(created)

        logger.info(
            f"Converted recommendations for investigation {investigation_id} into "
            f"{len(created_records)} proposed actions."
        )
        return created_records
