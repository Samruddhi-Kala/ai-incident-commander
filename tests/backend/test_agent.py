"""
Phase 6 Test Suite: LangGraph Incident Investigation Orchestrator

Validates:
1. Agent State: initialization, schema conformance, JSON serializability.
2. Intake Node: incident context normalization, missing incident handling, step persistence.
3. Planner Node: structured plan generation with tool cataloging and diagnostic queries.
4. RAG Node: knowledge retrieval, source attribution, and fallback handling.
5. Tools Node: registered tool execution, unknown tool rejection, investigation_id propagation.
6. Evidence Node: telemetry extraction, relevance scoring, database persistence.
7. Hypotheses Node: competing hypothesis formulation and database persistence.
8. Verification Node: evidence correlation, confidence updating, loop condition evaluation.
9. Root Cause Node: root cause synthesis, confidence rating, non-executable remediation proposals.
10. Graph Workflow: complete end-to-end orchestration and max-iteration loop guards.
11. Investigation API: POST /api/v1/investigations/{incident_id}/run and GET endpoints.
"""
import json
import uuid
import pytest
from app.agent.state import InvestigationState, create_initial_state
from app.agent.schemas import (
    InvestigationPlan,
    HypothesisItem,
    HypothesesPayload,
    VerificationItem,
    VerificationPayload,
    RootCauseResult,
)
from app.agent.llm import LLMService
from app.agent.nodes import (
    intake_node,
    planner_node,
    rag_node,
    tools_node,
    evidence_node,
    hypotheses_node,
    verification_node,
    root_cause_node,
)
from app.agent.graph import run_investigation_workflow, investigation_graph
from app.models.incident import Incident
from app.models.service import Service
from app.models.investigation import Investigation
from app.models.investigation_step import InvestigationStep
from app.models.evidence import Evidence
from app.models.hypothesis import Hypothesis
from app.models.tool_call import ToolCall
from app.models.audit_log import AuditLog
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.db.session import SessionLocal


@pytest.fixture
def db_session():
    """Database session fixture yielding an active SQLAlchemy session."""
    with SessionLocal() as session:
        yield session


@pytest.fixture
def default_service(db_session):
    """Creates a shared default service entity for incident testing."""
    svc = Service(
        name=f"svc-{uuid.uuid4().hex[:6]}",
        owner_team="Core Infrastructure",
        tier="Tier-1",
        dependencies=["db-primary"],
    )
    db_session.add(svc)
    db_session.commit()
    db_session.refresh(svc)
    return svc


# ---------------------------------------------------------------------------
# 1. State Tests
# ---------------------------------------------------------------------------

def test_state_creation_and_defaults():
    state = create_initial_state("test-inc-123", max_iterations=3)
    assert state["incident_id"] == "test-inc-123"
    assert state["max_iterations"] == 3
    assert state["iteration_count"] == 0
    assert state["tool_calls_count"] == 0
    assert state["status_outcome"] == "in_progress"
    assert state["need_more_evidence"] is False
    assert state["evidence"] == []
    assert state["hypotheses"] == []


def test_state_json_serializability():
    state = create_initial_state("test-inc-456")
    state["title"] = "Elevated API Latency"
    state["service_name"] = "payment-service"
    state["selected_tools"] = [{"tool_name": "get_error_rate", "arguments": {"service_name": "payment-service"}}]
    state["tool_results"] = [{"tool_name": "get_error_rate", "status": "Success", "data": {"error_rate_percent": 12.5}}]
    state["evidence"] = [{"id": str(uuid.uuid4()), "summary": "Error rate 12.5%", "relevance_score": 0.9}]

    # Validate JSON serializable
    serialized = json.dumps(state)
    deserialized = json.loads(serialized)
    assert deserialized["incident_id"] == "test-inc-456"
    assert deserialized["evidence"][0]["relevance_score"] == 0.9


# ---------------------------------------------------------------------------
# 2. Intake Node Tests
# ---------------------------------------------------------------------------

def test_intake_node_missing_incident():
    state = create_initial_state("")
    result = intake_node(state, config=None)
    assert result["status_outcome"] == "failed"
    assert "Missing incident_id" in result["errors"][0]


def test_intake_node_invalid_uuid(db_session):
    state = create_initial_state("not-a-uuid")
    config = {"configurable": {"db": db_session}}
    result = intake_node(state, config=config)
    assert result["status_outcome"] == "failed"
    assert "Invalid incident_id UUID" in result["errors"][0]


def test_intake_node_nonexistent_incident(db_session):
    fake_id = str(uuid.uuid4())
    state = create_initial_state(fake_id)
    config = {"configurable": {"db": db_session}}
    result = intake_node(state, config=config)
    assert result["status_outcome"] == "failed"
    assert "does not exist" in result["errors"][0]


def test_intake_node_success(db_session, default_service):
    inc = Incident(
        title="Payment Gateway Timeout Cascade",
        description="P99 latency surged over 2000ms with elevated 504 errors.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    config = {"configurable": {"db": db_session}}
    result = intake_node(state, config=config)

    assert result["title"] == "Payment Gateway Timeout Cascade"
    assert result["service_name"] == default_service.name
    assert result["service_tier"] == "Tier-1"
    assert result["service_dependencies"] == ["db-primary"]
    assert result["status_outcome"] == "in_progress"
    assert result["investigation_id"] != ""


# ---------------------------------------------------------------------------
# 3. Planner Node Tests
# ---------------------------------------------------------------------------

def test_planner_node_generation():
    state = create_initial_state("test-inc")
    state["title"] = "High Error Rate in Order Service"
    state["service_name"] = "order-service"
    state["service_tier"] = "Tier-1"
    state["service_dependencies"] = ["inventory-service"]

    config = {"configurable": {"llm": LLMService(provider="fake")}}
    result = planner_node(state, config=config)

    plan = result["investigation_plan"]
    assert plan is not None
    assert len(plan["questions"]) > 0
    assert len(plan["required_tools"]) > 0
    assert plan["requires_rag"] is True
    assert "order-service" in plan["reasoning"]


# ---------------------------------------------------------------------------
# 4. RAG Node Tests
# ---------------------------------------------------------------------------

def test_rag_node_retrieval_and_fallback():
    state = create_initial_state("test-inc")
    state["service_name"] = "payment-service"
    state["investigation_plan"] = {
        "rag_queries": ["payment-service runbook common failures"],
        "requires_rag": True,
    }

    config = {"configurable": {"db": None}}
    result = rag_node(state, config=config)

    assert result["retrieved_context"] is not None
    assert len(result["retrieved_sources"]) > 0
    assert "payment-service" in result["retrieved_sources"][0]["source_path"]


# ---------------------------------------------------------------------------
# 5. Tools Node Tests
# ---------------------------------------------------------------------------

def test_tools_node_execution_standalone():
    state = create_initial_state("test-inc")
    state["service_name"] = "payment-service"
    state["investigation_plan"] = {
        "required_tools": ["get_error_rate", "get_latency", "nonexistent_tool"],
    }

    config = {"configurable": {"db": None}}
    result = tools_node(state, config=config)

    assert result["current_step"] == "tools"
    assert result["tool_calls_count"] >= 2
    # Verify rejection of unregistered tool
    rejected = [r for r in result["tool_results"] if r.get("status") == "Rejected"]
    assert len(rejected) == 1
    assert "nonexistent_tool" in rejected[0]["tool_name"]


def test_tools_node_with_database_persistence(db_session, default_service):
    inc = Incident(
        title="DB Saturation Alert",
        description="DB connection pool saturated under elevated load.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()

    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = default_service.name
    state["investigation_plan"] = {"required_tools": ["get_error_rate", "search_logs"]}

    config = {"configurable": {"db": db_session}}
    result = tools_node(state, config=config)

    assert len(result["tool_results"]) == 2
    # Check persistence in tool_calls table
    persisted_calls = db_session.query(ToolCall).filter(ToolCall.investigation_id == inv.id).all()
    assert len(persisted_calls) == 2
    for call in persisted_calls:
        assert call.status == "Success"
        assert call.investigation_id == inv.id


# ---------------------------------------------------------------------------
# 6. Evidence Node Tests
# ---------------------------------------------------------------------------

def test_evidence_node_extraction_and_persistence(db_session, default_service):
    inc = Incident(
        title="Evidence Test Inc",
        description="Testing evidence collection and correlation.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["tool_results"] = [
        {
            "tool_name": "get_error_rate",
            "status": "Success",
            "data": {"error_rate_percent": 15.3, "baseline_percent": 0.5},
            "execution_time_ms": 45,
        },
        {
            "tool_name": "get_recent_deployments",
            "status": "Success",
            "data": {
                "deployments": [{"version": "v2.5.1", "environment": "prod", "deployed_at": "20m ago"}]
            },
            "execution_time_ms": 30,
        },
    ]

    config = {"configurable": {"db": db_session}}
    result = evidence_node(state, config=config)

    assert len(result["evidence"]) == 2
    # Verify in DB
    ev_db = db_session.query(Evidence).filter(Evidence.investigation_id == inv.id).all()
    assert len(ev_db) == 2
    assert any("15.3%" in e.summary for e in ev_db)


# ---------------------------------------------------------------------------
# 7. Hypotheses Node Tests
# ---------------------------------------------------------------------------

def test_hypotheses_node_generation(db_session, default_service):
    inc = Incident(
        title="Hypothesis Test",
        description="Testing competing hypothesis formulation.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["evidence"] = [
        {"id": str(uuid.uuid4()), "source_tool": "get_recent_deployments", "summary": "Deployment v2.5.1 released"}
    ]

    config = {"configurable": {"db": db_session, "llm": LLMService(provider="fake")}}
    result = hypotheses_node(state, config=config)

    assert len(result["hypotheses"]) >= 2
    # Verify in DB
    hypo_db = db_session.query(Hypothesis).filter(Hypothesis.investigation_id == inv.id).all()
    assert len(hypo_db) >= 2


# ---------------------------------------------------------------------------
# 8. Verification Node Tests
# ---------------------------------------------------------------------------

def test_verification_node_evaluation(db_session, default_service):
    inc = Incident(
        title="Verification Test",
        description="Testing hypothesis verification logic.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.flush()

    hypo_rec = Hypothesis(
        id=uuid.uuid4(),
        investigation_id=inv.id,
        hypothesis_text="Recent software deployment introduced connection exhaustion: deployment regression",
        status="Proposed",
    )
    db_session.add(hypo_rec)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["hypotheses"] = [{
        "id": str(hypo_rec.id),
        "title": "Recent software deployment introduced connection exhaustion and latency spike in payment-service",
        "description": "deployment regression",
        "confidence": 0.7,
    }]
    state["evidence"] = [
        {"source_tool": "get_recent_deployments", "summary": "Recent deployment v2.5.1 deployed"}
    ]

    config = {"configurable": {"db": db_session, "llm": LLMService(provider="fake")}}
    result = verification_node(state, config=config)

    assert result["current_step"] == "verification"
    assert result["need_more_evidence"] is False
    assert len(result["verification_results"]) == 1
    assert result["verification_results"][0]["status"] == "SUPPORTED"

    # Verify hypothesis record updated in DB
    db_session.refresh(hypo_rec)
    assert hypo_rec.status == "Verified_Strong"
    assert hypo_rec.confidence_score > 0.8


# ---------------------------------------------------------------------------
# 9. Root Cause Node Tests
# ---------------------------------------------------------------------------

def test_root_cause_node_synthesis(db_session, default_service):
    inc = Incident(
        title="RC Test Inc",
        description="Testing root cause analysis synthesis.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["verification_results"] = [
        {
            "hypothesis_title": "Deployment regression",
            "status": "SUPPORTED",
            "confidence": 0.88,
            "evidence_summaries": ["Deployment v2.5.1 was released ~20m ago"],
            "reasoning": "Matches telemetry logs",
        }
    ]

    config = {"configurable": {"db": db_session, "llm": LLMService(provider="fake")}}
    result = root_cause_node(state, config=config)

    assert result["probable_root_cause"] is not None
    assert result["confidence"] >= 0.8
    assert len(result["recommended_remediation"]) > 0
    assert result["status_outcome"] == "completed"

    # Verify investigation record updated in DB
    db_session.refresh(inv)
    assert inv.status == "Completed"
    assert inv.probable_root_cause is not None
    assert inv.confidence_score >= 0.8
    assert inv.completed_at is not None


# ---------------------------------------------------------------------------
# 10. Complete End-to-End Workflow & Loop Guard Tests
# ---------------------------------------------------------------------------

def test_complete_investigation_workflow_end_to_end(db_session, default_service):
    inc = Incident(
        title="Payment Service Cascading Outage",
        description="High HTTP 504 rates and connection timeouts following release.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.commit()

    final_state = run_investigation_workflow(
        incident_id=str(inc.id),
        max_iterations=3,
        db=db_session,
        llm=LLMService(provider="fake"),
    )

    assert final_state["status_outcome"] == "completed"
    assert final_state["current_step"] == "root_cause"
    assert final_state["probable_root_cause"] is not None
    assert final_state["confidence"] >= 0.8
    assert len(final_state["evidence"]) > 0
    assert len(final_state["hypotheses"]) > 0
    assert len(final_state["verification_results"]) > 0
    assert len(final_state["recommended_remediation"]) > 0

    # Verify steps recorded in DB
    inv_id = uuid.UUID(final_state["investigation_id"])
    steps = db_session.query(InvestigationStep).filter(InvestigationStep.investigation_id == inv_id).all()
    assert len(steps) >= 7  # Intake, Planner, RAG, Tools, Evidence, Hypotheses, Verification, Root Cause


def test_loop_guard_max_iterations():
    state = create_initial_state("test-loop", max_iterations=2)
    state["iteration_count"] = 2
    state["tool_calls_count"] = 10
    state["hypotheses"] = [{"title": "H1", "description": "D1", "confidence": 0.5}]

    # Verification node should force need_more_evidence to False when max iterations reached
    config = {"configurable": {"llm": LLMService(provider="fake")}}
    result = verification_node(state, config=config)
    assert result["need_more_evidence"] is False


# ---------------------------------------------------------------------------
# 11. API Endpoint Tests
# ---------------------------------------------------------------------------

def test_api_run_investigation_success(client, db_session, default_service):
    inc = Incident(
        title="Checkout API 500 Spike",
        description="Checkout response errors elevated to 22%.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.commit()

    resp = client.post(
        f"/api/v1/investigations/{inc.id}/run",
        json={"max_iterations": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_id"] == str(inc.id)
    assert data["status"] == "Completed"
    assert data["probable_root_cause"] is not None
    assert data["confidence_score"] is not None
    assert len(data["steps"]) >= 7
    assert len(data["evidence"]) > 0
    assert len(data["hypotheses"]) > 0
    assert len(data["tool_calls"]) > 0


def test_api_run_investigation_nonexistent_incident(client):
    fake_id = str(uuid.uuid4())
    resp = client.post(
        f"/api/v1/investigations/{fake_id}/run",
        json={"max_iterations": 3},
    )
    assert resp.status_code == 404


def test_api_get_investigation_endpoint(client, db_session, default_service):
    inc = Incident(
        title="Get Inv Test",
        description="Testing get investigation endpoint.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(
        incident_id=inc.id,
        investigation_number=f"INV-{uuid.uuid4().hex[:4]}",
        status="Completed",
        probable_root_cause="Test root cause",
        confidence_score=0.92,
    )
    db_session.add(inv)
    db_session.commit()

    resp = client.get(f"/api/v1/investigations/{inc.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["investigation_number"] == inv.investigation_number
    assert data["probable_root_cause"] == "Test root cause"
    assert data["confidence_score"] == 0.92


# ---------------------------------------------------------------------------
# 12. Inconclusive & Failure Outcome Handling Tests (Audit Follow-up)
# ---------------------------------------------------------------------------

def test_root_cause_all_hypotheses_inconclusive(db_session, default_service):
    inc = Incident(
        title="Inconclusive Hypo Test",
        description="Testing inconclusive outcome when no hypotheses are supported.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["verification_results"] = [
        {
            "hypothesis_title": "Database connection saturation",
            "status": "INCONCLUSIVE",
            "confidence": 0.50,
            "evidence_summaries": [],
            "reasoning": "Evidence is ambiguous",
        }
    ]

    config = {"configurable": {"db": db_session, "llm": LLMService(provider="fake")}}
    result = root_cause_node(state, config=config)

    assert result["status_outcome"] == "inconclusive"
    db_session.refresh(inv)
    assert inv.status == "Inconclusive"
    assert inv.probable_root_cause is not None


def test_root_cause_all_hypotheses_not_supported(db_session, default_service):
    inc = Incident(
        title="Not Supported Hypo Test",
        description="Testing inconclusive outcome when all hypotheses are ruled out.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["verification_results"] = [
        {
            "hypothesis_title": "Upstream gateway outage",
            "status": "NOT_SUPPORTED",
            "confidence": 0.15,
            "evidence_summaries": [],
            "reasoning": "Upstream is healthy",
        }
    ]

    config = {"configurable": {"db": db_session, "llm": LLMService(provider="fake")}}
    result = root_cause_node(state, config=config)

    assert result["status_outcome"] == "inconclusive"
    db_session.refresh(inv)
    assert inv.status == "Inconclusive"


def test_root_cause_low_confidence_inconclusive(db_session, default_service, monkeypatch):
    inc = Incident(
        title="Low Confidence Test",
        description="Testing inconclusive outcome when confidence is below 0.40.",
        severity="SEV-2",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(incident_id=inc.id, investigation_number=f"INV-{uuid.uuid4().hex[:4]}")
    db_session.add(inv)
    db_session.commit()

    state = create_initial_state(str(inc.id))
    state["investigation_id"] = str(inv.id)
    state["service_name"] = "payment-service"
    state["verification_results"] = [
        {
            "hypothesis_title": "Deployment regression",
            "status": "SUPPORTED",
            "confidence": 0.35,
            "evidence_summaries": [],
            "reasoning": "Weak signals",
        }
    ]

    # Mock LLMService to return RootCauseResult with confidence < 0.40
    fake_rc = RootCauseResult(
        probable_root_cause="Tentative unverified issue",
        confidence=0.32,
        supporting_evidence=[],
        alternative_explanations=[],
        recommended_remediation=["Continue monitoring"],
        reasoning="Insufficient evidence",
    )
    llm = LLMService(provider="fake")
    monkeypatch.setattr(llm, "analyze_root_cause", lambda **kwargs: fake_rc)

    config = {"configurable": {"db": db_session, "llm": llm}}
    result = root_cause_node(state, config=config)

    assert result["status_outcome"] == "inconclusive"
    db_session.refresh(inv)
    assert inv.status == "Inconclusive"
    assert inv.confidence_score == 0.32


def test_api_run_investigation_unexpected_exception_marks_failed(client, db_session, default_service, monkeypatch):
    inc = Incident(
        title="Crash Test Inc",
        description="Testing exception handling marks investigation Failed.",
        severity="SEV-1",
        service_id=default_service.id,
    )
    db_session.add(inc)
    db_session.flush()
    inv = Investigation(
        incident_id=inc.id,
        investigation_number=f"INV-{uuid.uuid4().hex[:4]}",
        status="Active",
    )
    db_session.add(inv)
    db_session.commit()

    def _crash_workflow(*args, **kwargs):
        raise RuntimeError("Simulated engine crash during investigation")

    import app.api.v1.routes.investigations as inv_routes
    monkeypatch.setattr(inv_routes, "run_investigation_workflow", _crash_workflow)

    resp = client.post(
        f"/api/v1/investigations/{inc.id}/run",
        json={"max_iterations": 2},
    )
    assert resp.status_code == 500
    assert "Simulated engine crash" in resp.json()["detail"]

    # Verify database status is Failed
    db_session.refresh(inv)
    assert inv.status == "Failed"
