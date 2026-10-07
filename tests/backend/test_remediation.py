"""
Phase 7 Test Suite: Human Approval & Remediation Engine

Validates:
1. Creation:
   - Proposing remediation actions with parameter validation
   - Unknown action types rejected
   - Missing required parameters rejected
   - Nonexistent investigation rejected
2. Lifecycle Transitions:
   - PROPOSED → PENDING_APPROVAL
   - PENDING_APPROVAL → APPROVED
   - PENDING_APPROVAL → REJECTED
   - APPROVED → EXECUTING → COMPLETED
   - APPROVED → EXECUTING → FAILED
3. Invalid Transitions:
   - REJECTED → EXECUTING prohibited
   - PENDING_APPROVAL → EXECUTING prohibited
   - PROPOSED → EXECUTING prohibited
   - COMPLETED → EXECUTING prohibited
   - FAILED → EXECUTING prohibited
   - REJECTED → APPROVED prohibited
   - COMPLETED → APPROVED prohibited
   - APPROVED → REJECTED prohibited
4. Human Approval Boundary:
   - AI (SYSTEM_AGENT) cannot approve actions
   - Explicit human authorization required
5. Simulated Remediation Actions:
   - restart_service, rollback_deployment, scale_service, clear_cache
   - Malformed parameters rejected
6. Audit Logging:
   - Full lineage recorded: proposal, approval, rejection, start, completed, failed
7. Integration with Phase 6:
   - Recommendations converted into PROPOSED actions
   - Phase 6 investigation remains read-only with no autonomous execution
8. Safety Guardrails:
   - Prohibits subprocess, shell, eval, exec, real infrastructure calls
9. API Endpoints:
   - POST /api/v1/remediations
   - GET /api/v1/remediations/{id}
   - GET /api/v1/investigations/{id}/remediations
   - POST /api/v1/remediations/{id}/submit
   - POST /api/v1/remediations/{id}/approve
   - POST /api/v1/remediations/{id}/reject
   - POST /api/v1/remediations/{id}/execute
   - POST /api/v1/investigations/{id}/remediations/propose
"""
import inspect
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.db.session import SessionLocal
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.investigation_step import InvestigationStep
from app.models.remediation_action import RemediationAction
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.remediation import (
    RemediationStatus,
    RiskLevel,
    RemediationActionCreate,
    RemediationApprovalRequest,
    RemediationRejectionRequest,
)
from app.services.remediation_service import RemediationService
from app.remediation.registry import RemediationRegistry, remediation_registry
from app.remediation.executor import RemediationExecutor
from app.remediation.actions import (
    RestartServiceAction,
    RollbackDeploymentAction,
    ScaleServiceAction,
    ClearCacheAction,
)
from app.remediation.exceptions import (
    RemediationNotFoundError,
    RemediationInvestigationNotFoundError,
    InvalidActionTypeError,
    RemediationParameterError,
    RemediationStateError,
    RemediationApprovalError,
    RemediationExecutionError,
)


@pytest.fixture
def db_session():
    """Database session fixture yielding an active SQLAlchemy session."""
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_setup(db_session):
    """Creates a base Service, Incident, and Investigation for testing."""
    svc_id = uuid.uuid4()
    svc = Service(
        id=svc_id,
        name=f"payment-service-{uuid.uuid4().hex[:6]}",
        owner_team="Core Payments",
        tier="Tier-1",
        dependencies=["auth-service", "db-primary"],
    )
    db_session.add(svc)
    db_session.flush()

    inc_id = uuid.uuid4()
    inc = Incident(
        id=inc_id,
        title="Payment Gateway Timeout Spike",
        description="P99 latency spiked past 1500ms following deployment v2.5.1",
        severity="SEV-1",
        status="Triggered",
        service_id=svc.id,
    )
    db_session.add(inc)
    db_session.flush()

    inv_id = uuid.uuid4()
    inv = Investigation(
        id=inv_id,
        incident_id=inc.id,
        investigation_number=f"INV-{uuid.uuid4().hex[:12]}",
        status="Completed",
        probable_root_cause="Deployment regression introduced connection exhaustion.",
        confidence_score=0.88,
    )
    db_session.add(inv)

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"oncall-{uuid.uuid4().hex[:6]}@example.com",
        full_name="On-Call Engineer",
        hashed_password="hashed_pw",
        role="Responder",
        is_active=True,
    )
    db_session.add(user)

    db_session.commit()
    db_session.refresh(svc)
    db_session.refresh(inc)
    db_session.refresh(inv)
    db_session.refresh(user)

    return {"service": svc, "incident": inc, "investigation": inv, "user": user}


# ===========================================================================
# 1. Remediation Proposal Creation Tests
# ===========================================================================

def test_create_remediation_proposal_success(db_session, test_setup):
    """Test successful creation of a remediation proposal in PROPOSED status."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service", "grace_period_seconds": 30},
        reasoning="Restart pods to recover exhausted connection pool.",
        risk_level=RiskLevel.MEDIUM,
        description="Graceful restart of payment service pods",
        expected_impact="Brief request queuing during rolling restart",
        rollback_plan="Readiness probes ensure healthy instances take traffic",
    )

    action = service.create_proposal(data=payload, actor_type="SYSTEM_AGENT")

    assert action.id is not None
    assert action.action_name == "restart_service"
    assert action.approval_status == RemediationStatus.PROPOSED.value
    assert action.risk_level == "MEDIUM"
    assert action.parameters["service"] == "payment-service"
    assert action.parameters["description"] == "Graceful restart of payment service pods"
    assert action.parameters["expected_impact"] == "Brief request queuing during rolling restart"
    assert action.parameters["rollback_plan"] == "Readiness probes ensure healthy instances take traffic"
    assert action.created_at is not None


def test_create_remediation_invalid_action_type(db_session, test_setup):
    """Test that proposing an unregistered action type is rejected."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="reboot_entire_datacenter",
        parameters={"datacenter": "us-east-1"},
        reasoning="Unregistered catastrophic action",
    )

    with pytest.raises(InvalidActionTypeError) as exc:
        service.create_proposal(data=payload)
    assert "Unknown remediation action type" in str(exc.value)


def test_create_remediation_missing_required_parameters(db_session, test_setup):
    """Test that missing required parameters are rejected upon proposal."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    # rollback_deployment requires target_version
    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="rollback_deployment",
        parameters={"service": "payment-service"},  # missing target_version
        reasoning="Missing target_version",
    )

    with pytest.raises(RemediationParameterError) as exc:
        service.create_proposal(data=payload)
    assert "target_version" in str(exc.value)


def test_create_remediation_nonexistent_investigation(db_session):
    """Test that proposing for a nonexistent investigation ID is rejected."""
    service = RemediationService(db_session)
    random_inv_id = uuid.uuid4()

    payload = RemediationActionCreate(
        investigation_id=random_inv_id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Ghost investigation",
    )

    with pytest.raises(RemediationInvestigationNotFoundError):
        service.create_proposal(data=payload)


# ===========================================================================
# 2. Lifecycle Transition Tests
# ===========================================================================

def test_lifecycle_proposed_to_pending_approval(db_session, test_setup):
    """Test lifecycle: PROPOSED → PENDING_APPROVAL."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Restart to recover memory",
    )
    action = service.create_proposal(data=payload)
    assert action.approval_status == RemediationStatus.PROPOSED.value

    # Transition to PENDING_APPROVAL
    updated = service.submit_for_approval(remediation_id=action.id, comment="Ready for on-call sign-off")
    assert updated.approval_status == RemediationStatus.PENDING_APPROVAL.value


def test_lifecycle_pending_approval_to_approved(db_session, test_setup):
    """Test lifecycle: PENDING_APPROVAL → APPROVED."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="rollback_deployment",
        parameters={"service": "payment-service", "target_version": "v2.5.0"},
        reasoning="Rollback to previous release",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)

    # Human approves
    human_user_id = test_setup["user"].id
    approved = service.approve_action(
        remediation_id=action.id,
        approved_by=human_user_id,
        actor_type="HUMAN_USER",
        comment="Approved by On-Call Lead",
    )

    assert approved.approval_status == RemediationStatus.APPROVED.value
    assert approved.approved_by == human_user_id
    assert approved.approval_timestamp is not None


def test_lifecycle_pending_approval_to_rejected(db_session, test_setup):
    """Test lifecycle: PENDING_APPROVAL → REJECTED."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="scale_service",
        parameters={"service": "payment-service", "replicas": 50},
        reasoning="Scale aggressively",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)

    # Human rejects
    human_user_id = test_setup["user"].id
    rejected = service.reject_action(
        remediation_id=action.id,
        rejected_by=human_user_id,
        reason="Cluster resource quota exceeded. Scale to 10 instead.",
    )

    assert rejected.approval_status == RemediationStatus.REJECTED.value
    assert rejected.execution_result is not None
    assert rejected.execution_result["status"] == "REJECTED"
    assert "quota exceeded" in rejected.execution_result["rejection_reason"]


def test_lifecycle_approved_to_executing_to_completed(db_session, test_setup):
    """Test lifecycle: APPROVED → EXECUTING → COMPLETED."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "payment-service", "cache_type": "redis"},
        reasoning="Flush poisoned cache keys",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.approve_action(remediation_id=action.id, actor_type="HUMAN_USER")

    # Execute approved action
    completed = service.execute_action(remediation_id=action.id)

    assert completed.approval_status == RemediationStatus.COMPLETED.value
    assert completed.execution_result is not None
    assert completed.execution_result["status"] == "COMPLETED"
    assert completed.execution_result["output"]["status"] == "success"
    assert completed.execution_result["output"]["action"] == "clear_cache"
    assert completed.execution_result["execution_time_ms"] >= 0


def test_lifecycle_approved_to_executing_to_failed(db_session, test_setup, monkeypatch):
    """Test lifecycle: APPROVED → EXECUTING → FAILED when execution encounters an error."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Restart with intentional failure simulation",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.approve_action(remediation_id=action.id, actor_type="HUMAN_USER")

    # Force simulated executor to fail
    def mock_execute(*args, **kwargs):
        raise RuntimeError("Simulated transient RPC timeout during service restart")

    monkeypatch.setattr(service.executor.registry.get("restart_service"), "execute", mock_execute)

    failed = service.execute_action(remediation_id=action.id)

    assert failed.approval_status == RemediationStatus.FAILED.value
    assert failed.execution_result is not None
    assert failed.execution_result["status"] == "FAILED"
    assert "Simulated transient RPC timeout" in failed.execution_result["failure_reason"]


# ===========================================================================
# 3. Invalid Transition Enforcement Tests
# ===========================================================================

def test_invalid_transition_rejected_to_execute(db_session, test_setup):
    """Enforce: REJECTED → EXECUTING is strictly prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Restart rejected proposal",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.reject_action(remediation_id=action.id, reason="Rejected by ops")

    with pytest.raises(RemediationStateError) as exc:
        service.execute_action(remediation_id=action.id)
    assert "Cannot execute a rejected remediation action" in str(exc.value)


def test_invalid_transition_pending_to_execute(db_session, test_setup):
    """Enforce: PENDING_APPROVAL → EXECUTING is prohibited without approval."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Pending approval execution attempt",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)

    with pytest.raises(RemediationStateError) as exc:
        service.execute_action(remediation_id=action.id)
    assert "Explicit human approval is required" in str(exc.value)


def test_invalid_transition_proposed_to_execute(db_session, test_setup):
    """Enforce: PROPOSED → EXECUTING directly is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Proposed execution attempt",
    )
    action = service.create_proposal(data=payload)

    with pytest.raises(RemediationStateError) as exc:
        service.execute_action(remediation_id=action.id)
    assert "Explicit human approval is required" in str(exc.value)


def test_invalid_transition_completed_to_execute(db_session, test_setup):
    """Enforce: COMPLETED → EXECUTING re-execution is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "payment-service"},
        reasoning="Clear cache",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.approve_action(remediation_id=action.id)
    service.execute_action(remediation_id=action.id)

    with pytest.raises(RemediationStateError) as exc:
        service.execute_action(remediation_id=action.id)
    assert "already completed" in str(exc.value)


def test_invalid_transition_failed_to_execute(db_session, test_setup):
    """Enforce: FAILED → EXECUTING re-execution without a new proposal is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "payment-service"},
        reasoning="Failed action retry attempt",
    )
    action = service.create_proposal(data=payload)
    action.approval_status = RemediationStatus.FAILED.value
    db_session.commit()

    with pytest.raises(RemediationStateError) as exc:
        service.execute_action(remediation_id=action.id)
    assert "Failed remediation cannot be re-executed without a new proposal" in str(exc.value)


def test_invalid_transition_rejected_to_approve(db_session, test_setup):
    """Enforce: REJECTED → APPROVED is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Action to be rejected then illegally approved",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.reject_action(remediation_id=action.id, reason="Rejected initially")

    with pytest.raises(RemediationStateError) as exc:
        service.approve_action(remediation_id=action.id)
    assert "Cannot approve an already rejected remediation" in str(exc.value)


def test_invalid_transition_completed_to_approve(db_session, test_setup):
    """Enforce: COMPLETED → APPROVED is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "payment-service"},
        reasoning="Completed action cannot be re-approved",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.approve_action(remediation_id=action.id)
    service.execute_action(remediation_id=action.id)

    with pytest.raises(RemediationStateError) as exc:
        service.approve_action(remediation_id=action.id)
    assert "terminal or active status" in str(exc.value)


def test_invalid_transition_approved_to_reject(db_session, test_setup):
    """Enforce: APPROVED → REJECTED is prohibited."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="Approved action cannot be rejected",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)
    service.approve_action(remediation_id=action.id)

    with pytest.raises(RemediationStateError) as exc:
        service.reject_action(remediation_id=action.id, reason="Attempt rejection after approval")
    assert "Cannot reject an already approved remediation" in str(exc.value)


# ===========================================================================
# 4. Human Approval Guard Tests
# ===========================================================================

def test_ai_cannot_approve_automatically(db_session, test_setup):
    """Enforce: The AI agent (SYSTEM_AGENT) cannot approve its own remediation."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "payment-service"},
        reasoning="AI attempting self-approval",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)

    with pytest.raises(RemediationApprovalError) as exc:
        service.approve_action(remediation_id=action.id, actor_type="SYSTEM_AGENT")
    assert "AI agents cannot approve remediation actions" in str(exc.value)


# ===========================================================================
# 5. Simulated Actions Tests
# ===========================================================================

def test_simulated_restart_service():
    """Verify RestartServiceAction schema and simulated execution output."""
    action = RestartServiceAction()
    assert action.action_name == "restart_service"
    assert action.default_risk_level == "MEDIUM"

    result = action.execute({"service": "order-service", "grace_period_seconds": 45})
    assert result.status == "success"
    assert result.output["service"] == "order-service"
    assert result.output["restarted_instances"] == 3
    assert result.output["grace_period_seconds"] == 45
    assert "completed" in result.message


def test_simulated_rollback_deployment():
    """Verify RollbackDeploymentAction schema and simulated execution output."""
    action = RollbackDeploymentAction()
    assert action.action_name == "rollback_deployment"
    assert action.default_risk_level == "HIGH"

    result = action.execute({"service": "auth-service", "target_version": "v1.4.2"})
    assert result.status == "success"
    assert result.output["target_version"] == "v1.4.2"
    assert result.output["traffic_shifted_pct"] == 100


def test_simulated_scale_service():
    """Verify ScaleServiceAction schema and simulated execution output."""
    action = ScaleServiceAction()
    assert action.action_name == "scale_service"
    assert action.default_risk_level == "MEDIUM"

    result = action.execute({"service": "search-service", "replicas": 8})
    assert result.status == "success"
    assert result.output["replicas"] == 8


def test_simulated_clear_cache():
    """Verify ClearCacheAction schema and simulated execution output."""
    action = ClearCacheAction()
    assert action.action_name == "clear_cache"
    assert action.default_risk_level == "LOW"

    result = action.execute({"service": "catalog-service", "cache_type": "memcached"})
    assert result.status == "success"
    assert result.output["cache_type"] == "memcached"
    assert result.output["keys_evicted"] == 1250


def test_simulated_action_malformed_parameters_rejected():
    """Verify validation rejects invalid parameter types."""
    scale = ScaleServiceAction()
    with pytest.raises(RemediationParameterError):
        scale.execute({"service": "payment-service", "replicas": 0})

    with pytest.raises(RemediationParameterError):
        scale.execute({"service": "payment-service", "replicas": 500})

    restart = RestartServiceAction()
    with pytest.raises(RemediationParameterError):
        restart.execute({"service": ""})


# ===========================================================================
# 6. Audit Logging Tests
# ===========================================================================

def test_remediation_audit_logging_full_trail(db_session, test_setup):
    """
    Verify complete audit logging trail across proposal, approval, execution start, and completion.
    """
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    inc = test_setup["incident"]

    payload = RemediationActionCreate(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "payment-service"},
        reasoning="Audit trail test",
    )
    action = service.create_proposal(data=payload)
    service.submit_for_approval(remediation_id=action.id)

    human_id = test_setup["user"].id
    service.approve_action(remediation_id=action.id, approved_by=human_id, comment="Approved for test")
    service.execute_action(remediation_id=action.id)

    # Retrieve audit logs for this incident
    logs = db_session.scalars(
        select(AuditLog)
        .where(AuditLog.remediation_action_id == action.id)
        .order_by(AuditLog.created_at.asc())
    ).all()

    action_types = [l.action_type for l in logs]
    assert "remediation.proposed" in action_types
    assert "remediation.submitted_for_approval" in action_types
    assert "remediation.approved" in action_types
    assert "remediation.execution_started" in action_types
    assert "remediation.execution_completed" in action_types

    # Verify actor metadata on approval log
    approval_log = next(l for l in logs if l.action_type == "remediation.approved")
    assert approval_log.actor_id == human_id
    assert approval_log.actor_type == "HUMAN_USER"
    assert approval_log.payload["comment"] == "Approved for test"


# ===========================================================================
# 7. Phase 6 Integration Tests
# ===========================================================================

def test_convert_phase6_recommendations_to_proposals(db_session, test_setup):
    """
    Verify Phase 6 recommendations can be converted into PROPOSED actions,
    and confirm they remain PROPOSED without executing.
    """
    service = RemediationService(db_session)
    inv = test_setup["investigation"]

    # Add a Phase 6 investigation step with recommendations
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=8,
        title="Step 8 — Root Cause Synthesis & Remediation Guidance",
        status="Completed",
        output_summary=(
            "Probable root cause: Deployment v2.5.1 caused memory leak. "
            "Recommendations: Roll back payment-service to v2.5.0 and restart replicas."
        ),
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)

    assert len(proposals) >= 2
    action_names = [p.action_name for p in proposals]
    assert "rollback_deployment" in action_names
    assert "restart_service" in action_names

    # CRITICAL: Verify they are created as PROPOSED and NOT executed
    for p in proposals:
        assert p.approval_status == RemediationStatus.PROPOSED.value
        assert p.execution_result is None


def test_recommendation_mapping_rollback(db_session, test_setup):
    """1. Recognized rollback recommendation → rollback proposal created in PROPOSED status."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Recommend rollback to previous stable release v2.5.0 immediately.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert len(proposals) == 1
    assert proposals[0].action_name == "rollback_deployment"
    assert proposals[0].approval_status == RemediationStatus.PROPOSED.value
    assert proposals[0].parameters["target_version"] == "v2.5.0"
    assert proposals[0].execution_result is None


def test_recommendation_mapping_restart(db_session, test_setup):
    """2. Recognized restart recommendation → restart proposal created in PROPOSED status."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Recommend graceful restart of service instances to clear memory leak.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert len(proposals) == 1
    assert proposals[0].action_name == "restart_service"
    assert proposals[0].approval_status == RemediationStatus.PROPOSED.value
    assert proposals[0].parameters["grace_period_seconds"] == 30
    assert proposals[0].execution_result is None


def test_recommendation_mapping_scale(db_session, test_setup):
    """3. Recognized scale recommendation → scale proposal created in PROPOSED status."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Elevated traffic volume detected; scale service replicas to absorb load.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert len(proposals) == 1
    assert proposals[0].action_name == "scale_service"
    assert proposals[0].approval_status == RemediationStatus.PROPOSED.value
    assert proposals[0].parameters["replicas"] == 5
    assert proposals[0].execution_result is None


def test_recommendation_mapping_cache(db_session, test_setup):
    """4. Recognized cache recommendation → clear_cache proposal created in PROPOSED status."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Stale session cache entries identified; recommend flush cache.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert len(proposals) == 1
    assert proposals[0].action_name == "clear_cache"
    assert proposals[0].approval_status == RemediationStatus.PROPOSED.value
    assert proposals[0].parameters["cache_type"] == "redis"
    assert proposals[0].execution_result is None


def test_recommendation_mapping_unrecognized_creates_zero_proposals(db_session, test_setup):
    """5. Unrecognized recommendation → ZERO remediation proposals created (no guessing or fallback to restart)."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Notify executive stakeholders and schedule debrief.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert proposals == []
    assert len(proposals) == 0

    # Verify zero remediation records created in the database
    actions = db_session.scalars(
        select(RemediationAction).where(RemediationAction.investigation_id == inv.id)
    ).all()
    assert len(actions) == 0


def test_unrecognized_recommendation_cannot_cause_execution(db_session, test_setup):
    """6. Unrecognized recommendation cannot cause execution or dispatch."""
    service = RemediationService(db_session)
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Notify executive stakeholders and schedule debrief.",
    )
    db_session.add(step)
    db_session.commit()

    proposals = service.create_proposals_from_investigation(investigation_id=inv.id)
    assert proposals == []

    # Verify no execution can occur: no proposals exist, and non-existent IDs raise RemediationNotFoundError
    with pytest.raises(RemediationNotFoundError):
        service.execute_action(remediation_id=uuid.uuid4())



# ===========================================================================
# 8. Safety & Subprocess Verification
# ===========================================================================

def test_safety_no_dangerous_execution_primitives():
    """
    Verifies that remediation modules do not import or call dangerous primitives:
    subprocess, os.system, os.popen, eval, exec, shutil.rmtree.
    """
    import app.remediation.base as rem_base
    import app.remediation.executor as rem_exec
    import app.remediation.registry as rem_reg
    import app.remediation.actions.restart_service as rem_restart
    import app.remediation.actions.rollback_deployment as rem_rollback
    import app.remediation.actions.scale_service as rem_scale
    import app.remediation.actions.clear_cache as rem_cache
    import app.services.remediation_service as rem_svc

    import ast

    modules = [
        rem_base,
        rem_exec,
        rem_reg,
        rem_restart,
        rem_rollback,
        rem_scale,
        rem_cache,
        rem_svc,
    ]

    for mod in modules:
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in ("subprocess", "shutil"), f"Forbidden import {alias.name} in {mod.__name__}"
            elif isinstance(node, ast.ImportFrom):
                assert node.module not in ("subprocess", "shutil"), f"Forbidden import from {node.module} in {mod.__name__}"
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in ("eval", "exec"), f"Forbidden call {node.func.id} in {mod.__name__}"
                elif isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in ("system", "popen"), f"Forbidden call {node.func.attr} in {mod.__name__}"


# ===========================================================================
# 9. API Endpoints Tests
# ===========================================================================

def test_api_remediation_full_flow(client, db_session, test_setup):
    """
    End-to-end HTTP API test covering proposal creation, retrieval,
    submission, approval, and execution.
    """
    inv = test_setup["investigation"]

    # 1. POST /api/v1/remediations (Create proposal)
    create_payload = {
        "investigation_id": str(inv.id),
        "action_name": "restart_service",
        "parameters": {"service": "payment-service", "grace_period_seconds": 20},
        "reasoning": "Restart service to clear transient deadlocks",
        "risk_level": "MEDIUM",
        "description": "Restart payment service pods",
    }
    res = client.post("/api/v1/remediations", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    remediation_id = data["id"]
    assert data["approval_status"] == "PROPOSED"
    assert data["action_name"] == "restart_service"

    # 2. GET /api/v1/remediations/{id}
    res = client.get(f"/api/v1/remediations/{remediation_id}")
    assert res.status_code == 200
    assert res.json()["id"] == remediation_id

    # 3. GET /api/v1/investigations/{investigation_id}/remediations
    res = client.get(f"/api/v1/investigations/{inv.id}/remediations")
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == remediation_id for item in list_data["items"])

    # 4. Attempt to execute while still PROPOSED (must fail 400)
    res = client.post(f"/api/v1/remediations/{remediation_id}/execute")
    assert res.status_code == 400

    # 5. POST /api/v1/remediations/{id}/submit (Submit for approval)
    res = client.post(
        f"/api/v1/remediations/{remediation_id}/submit",
        json={"comment": "Ready for approval"},
    )
    assert res.status_code == 200
    assert res.json()["approval_status"] == "PENDING_APPROVAL"

    # 6. Attempt execution while PENDING_APPROVAL (must fail 400)
    res = client.post(f"/api/v1/remediations/{remediation_id}/execute")
    assert res.status_code == 400

    # 7. POST /api/v1/remediations/{id}/approve (Human approval)
    user_id = str(test_setup["user"].id)
    res = client.post(
        f"/api/v1/remediations/{remediation_id}/approve",
        json={"approved_by": user_id, "actor_type": "HUMAN_USER", "comment": "Approved by on-call"},
    )
    assert res.status_code == 200
    assert res.json()["approval_status"] == "APPROVED"
    assert res.json()["approved_by"] == user_id

    # 8. POST /api/v1/remediations/{id}/execute (Execute approved action)
    res = client.post(f"/api/v1/remediations/{remediation_id}/execute")
    assert res.status_code == 200
    exec_data = res.json()
    assert exec_data["approval_status"] == "COMPLETED"
    assert exec_data["execution_result"]["status"] == "COMPLETED"
    assert exec_data["execution_result"]["output"]["status"] == "success"


def test_api_remediation_rejection_flow(client, test_setup):
    """Test API flow for rejecting a proposed remediation action."""
    inv = test_setup["investigation"]

    create_payload = {
        "investigation_id": str(inv.id),
        "action_name": "rollback_deployment",
        "parameters": {"service": "payment-service", "target_version": "v1.0.0"},
        "reasoning": "Rollback to outdated release",
        "risk_level": "HIGH",
    }
    res = client.post("/api/v1/remediations", json=create_payload)
    assert res.status_code == 201
    remediation_id = res.json()["id"]

    # Submit for approval
    client.post(f"/api/v1/remediations/{remediation_id}/submit")

    # Reject
    reject_payload = {
        "rejected_by": str(test_setup["user"].id),
        "reason": "Target version v1.0.0 has deprecated schema migrations.",
    }
    res = client.post(f"/api/v1/remediations/{remediation_id}/reject", json=reject_payload)
    assert res.status_code == 200
    assert res.json()["approval_status"] == "REJECTED"

    # Verify execution is blocked
    res = client.post(f"/api/v1/remediations/{remediation_id}/execute")
    assert res.status_code == 400


def test_api_propose_from_investigation_endpoint(client, db_session, test_setup):
    """Test POST /api/v1/investigations/{id}/remediations/propose with recognized recommendations."""
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Roll back deployment v2.5.1 and restart service to clear deadlock.",
    )
    db_session.add(step)
    db_session.commit()

    res = client.post(f"/api/v1/investigations/{inv.id}/remediations/propose")
    assert res.status_code == 201
    data = res.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["approval_status"] == "PROPOSED"


def test_api_propose_from_investigation_endpoint_unrecognized(client, db_session, test_setup):
    """Test POST /api/v1/investigations/{id}/remediations/propose with unrecognized recommendations yields 0 proposals."""
    inv = test_setup["investigation"]
    step = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Remediation Guidance",
        status="Completed",
        output_summary="Notify executive stakeholders and schedule debrief.",
    )
    db_session.add(step)
    db_session.commit()

    res = client.post(f"/api/v1/investigations/{inv.id}/remediations/propose")
    assert res.status_code == 201
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_api_list_remediations_pagination_and_total_count(client, db_session, test_setup):
    """
    Test GET /api/v1/remediations respects skip and limit, and total represents
    the actual count of matching records.
    """
    inv = test_setup["investigation"]
    # Create 3 distinct remediation proposals
    actions = []
    for i in range(3):
        r = RemediationAction(
            investigation_id=inv.id,
            action_name="restart_service",
            parameters={"service": f"service-{i}"},
            reasoning=f"Reason {i}",
            risk_level="LOW",
            approval_status="PROPOSED",
        )
        db_session.add(r)
        actions.append(r)
    db_session.commit()

    # Query all with default pagination
    res_all = client.get("/api/v1/remediations")
    assert res_all.status_code == 200
    data_all = res_all.json()
    total_records = data_all["total"]
    assert total_records >= 3

    # Query with skip=1, limit=1
    res_paginated = client.get("/api/v1/remediations?skip=1&limit=1")
    assert res_paginated.status_code == 200
    data_paginated = res_paginated.json()
    assert len(data_paginated["items"]) == 1
    # total must reflect the overall count of matching records, not the page slice size
    assert data_paginated["total"] == total_records


def test_api_list_remediations_status_filter_and_total_count(client, db_session, test_setup):
    """
    Test GET /api/v1/remediations with status filter returns only matching items,
    respects skip and limit, and total represents the actual count of matching status records.
    """
    inv = test_setup["investigation"]
    # Add 2 with PROPOSED, 1 with APPROVED
    p1 = RemediationAction(
        investigation_id=inv.id,
        action_name="restart_service",
        parameters={"service": "auth-service"},
        reasoning="Auth service memory leak",
        risk_level="LOW",
        approval_status="PROPOSED",
    )
    p2 = RemediationAction(
        investigation_id=inv.id,
        action_name="clear_cache",
        parameters={"service": "cache-service"},
        reasoning="Stale keys",
        risk_level="LOW",
        approval_status="PROPOSED",
    )
    p3 = RemediationAction(
        investigation_id=inv.id,
        action_name="scale_service",
        parameters={"service": "worker-service", "replicas": 4},
        reasoning="High queue backlog",
        risk_level="MEDIUM",
        approval_status="APPROVED",
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Filter for APPROVED
    res_approved = client.get("/api/v1/remediations?status=APPROVED")
    assert res_approved.status_code == 200
    data_approved = res_approved.json()
    assert data_approved["total"] >= 1
    for item in data_approved["items"]:
        assert item["approval_status"] == "APPROVED"

    # Filter for PROPOSED with pagination skip=1, limit=1
    res_prop_all = client.get("/api/v1/remediations?status=PROPOSED")
    assert res_prop_all.status_code == 200
    total_proposed = res_prop_all.json()["total"]
    assert total_proposed >= 2

    res_prop_page = client.get("/api/v1/remediations?status=PROPOSED&skip=1&limit=1")
    assert res_prop_page.status_code == 200
    data_prop_page = res_prop_page.json()
    assert len(data_prop_page["items"]) == 1
    assert data_prop_page["items"][0]["approval_status"] == "PROPOSED"
    # total must equal the total number of PROPOSED records, NOT 1 (the slice size)
    assert data_prop_page["total"] == total_proposed


