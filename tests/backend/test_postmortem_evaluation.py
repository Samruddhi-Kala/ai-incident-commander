"""
Phase 9 Test Suite: Postmortem Generation & AI Investigation Evaluation

Validates:
1. Postmortem creation grounded in persisted investigation data
2. Postmortem retrieval and 404 for missing investigations
3. Duplicate handling (idempotent retrieval vs regeneration)
4. Postmortem grounding for completed vs inconclusive investigations
5. Quantitative AI investigation evaluation (deterministic 0-100 heuristic scores)
6. Score components: evidence support, hypothesis quality, verification rigor, RAG relevance, tool efficiency
7. Explanations and metrics breakdown
8. Evaluations listing endpoint with pagination
9. Redundancy penalties in tool efficiency
"""
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.investigation_step import InvestigationStep
from app.models.evidence import Evidence
from app.models.hypothesis import Hypothesis
from app.models.tool_call import ToolCall
from app.models.remediation_action import RemediationAction
from app.models.postmortem import Postmortem
from app.models.investigation_evaluation import InvestigationEvaluation
from app.services.postmortem_service import PostmortemService
from app.services.evaluation_service import EvaluationService


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
    """Creates a base Service, Incident, and complete Investigation for testing."""
    svc_id = uuid.uuid4()
    svc = Service(
        id=svc_id,
        name=f"checkout-service-{uuid.uuid4().hex[:6]}",
        owner_team="Checkout Engineering",
        tier="Tier-1",
        dependencies=["payment-gateway", "inventory-db"],
    )
    db_session.add(svc)
    db_session.flush()

    inc_id = uuid.uuid4()
    inc = Incident(
        id=inc_id,
        title="Spike in Checkout HTTP 504 Deadlocks",
        description="Checkout latency surged to 8.4s causing cascading thread exhaustion in worker pool.",
        severity="SEV-1",
        status="Investigating",
        service_id=svc.id,
    )
    db_session.add(inc)
    db_session.flush()

    inv_id = uuid.uuid4()
    inv = Investigation(
        id=inv_id,
        incident_id=inc.id,
        investigation_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
        status="Completed",
        probable_root_cause="Database connection pool exhaustion caused by unindexed cart query in v2.4.1 deployment.",
        confidence_score=0.92,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(inv)
    db_session.flush()

    # Steps
    s1 = InvestigationStep(
        investigation_id=inv.id,
        step_order=1,
        title="Investigation Planning",
        status="Completed",
        output_summary="Identified high DB connection utilization on inventory-db.",
    )
    s2 = InvestigationStep(
        investigation_id=inv.id,
        step_order=2,
        title="RAG Runbook Retrieval",
        status="Completed",
        output_summary="Retrieved checkout service connection pool runbook and remediation playbooks.",
    )
    s3 = InvestigationStep(
        investigation_id=inv.id,
        step_order=3,
        title="Remediation Recommendation",
        status="Completed",
        output_summary="Rollback deployment to v2.4.0 and restart checkout service pool.",
    )
    db_session.add_all([s1, s2, s3])

    # Evidence
    e1 = Evidence(
        investigation_id=inv.id,
        source_tool="query_prometheus",
        summary="Pool saturation at 100% (50/50 connections active)",
        relevance_score=0.95,
        raw_payload={"metric": "db_connections_active", "value": 50},
    )
    e2 = Evidence(
        investigation_id=inv.id,
        source_tool="fetch_service_logs",
        summary="Deadlock detected on cart_items table during checkout write",
        relevance_score=0.90,
        raw_payload={"error": "deadlock detected"},
    )
    db_session.add_all([e1, e2])

    # Hypotheses
    h1 = Hypothesis(
        investigation_id=inv.id,
        hypothesis_text="Database pool exhaustion due to slow cart queries",
        status="SUPPORTED",
        confidence_score=0.92,
    )
    h2 = Hypothesis(
        investigation_id=inv.id,
        hypothesis_text="Upstream payment gateway timeout",
        status="NOT_SUPPORTED",
        confidence_score=0.10,
    )
    db_session.add_all([h1, h2])

    # Tool calls
    tc1 = ToolCall(
        investigation_id=inv.id,
        tool_name="query_prometheus",
        arguments={"query": "db_connections_active"},
        status="SUCCESS",
        execution_time_ms=45,
    )
    tc2 = ToolCall(
        investigation_id=inv.id,
        tool_name="fetch_service_logs",
        arguments={"service": "checkout-service", "level": "ERROR"},
        status="SUCCESS",
        execution_time_ms=62,
    )
    db_session.add_all([tc1, tc2])

    # Remediation proposal
    ra = RemediationAction(
        investigation_id=inv.id,
        action_name="rollback_deployment",
        parameters={"service": "checkout-service", "target_version": "v2.4.0"},
        reasoning="Rollback unindexed query deployment",
        risk_level="HIGH",
        approval_status="APPROVED",
    )
    db_session.add(ra)

    db_session.commit()
    db_session.refresh(inv)

    return {
        "service": svc,
        "incident": inc,
        "investigation": inv,
    }


def test_postmortem_generation_and_grounding(client, test_setup):
    """
    Test generating a postmortem creates a grounded document matching persisted investigation data.
    """
    inv = test_setup["investigation"]
    inc = test_setup["incident"]

    res = client.post(f"/api/v1/investigations/{inv.id}/postmortem")
    assert res.status_code == 201
    data = res.json()

    assert data["investigation_id"] == str(inv.id)
    assert inv.investigation_number in data["title"]
    assert inc.title in data["title"]
    assert data["root_cause"] == inv.probable_root_cause
    assert len(data["timeline"]) >= 3
    assert len(data["contributing_factors"]) >= 1
    assert data["remediation"]["proposals_count"] == 1
    assert len(data["lessons_learned"]) >= 2
    assert len(data["preventive_actions"]) >= 2
    assert "query_prometheus" in data["details"]["diagnostic_tools_used"]


def test_postmortem_retrieval(client, test_setup):
    """
    Test GET /api/v1/investigations/{id}/postmortem retrieves existing postmortem report.
    """
    inv = test_setup["investigation"]
    # Generate first
    res_gen = client.post(f"/api/v1/investigations/{inv.id}/postmortem")
    assert res_gen.status_code == 201

    # Fetch
    res_get = client.get(f"/api/v1/investigations/{inv.id}/postmortem")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == res_gen.json()["id"]


def test_postmortem_duplicate_handling(client, test_setup):
    """
    Test calling postmortem generation again returns the existing record without duplicates.
    """
    inv = test_setup["investigation"]
    res1 = client.post(f"/api/v1/investigations/{inv.id}/postmortem")
    assert res1.status_code == 201
    id1 = res1.json()["id"]

    # Second call returns existing
    res2 = client.post(f"/api/v1/investigations/{inv.id}/postmortem")
    assert res2.status_code == 201
    id2 = res2.json()["id"]
    assert id1 == id2

    # With regenerate=True
    res3 = client.post(f"/api/v1/investigations/{inv.id}/postmortem?regenerate=true")
    assert res3.status_code == 201
    id3 = res3.json()["id"]
    assert id1 == id3


def test_postmortem_missing_investigation(client):
    """
    Test postmortem creation and retrieval for non-existent investigation ID return 404.
    """
    random_id = uuid.uuid4()
    res_post = client.post(f"/api/v1/investigations/{random_id}/postmortem")
    assert res_post.status_code == 404

    res_get = client.get(f"/api/v1/investigations/{random_id}/postmortem")
    assert res_get.status_code == 404


def test_postmortem_inconclusive_investigation(client, db_session, test_setup):
    """
    Test generating postmortem for an Inconclusive investigation notes ambiguity and gap.
    """
    svc = test_setup["service"]
    inc = test_setup["incident"]

    inv_inc = Investigation(
        incident_id=inc.id,
        investigation_number=f"INV-INC-{uuid.uuid4().hex[:4].upper()}",
        status="Inconclusive",
        probable_root_cause=None,
        confidence_score=0.25,
    )
    db_session.add(inv_inc)
    db_session.commit()

    res = client.post(f"/api/v1/investigations/{inv_inc.id}/postmortem")
    assert res.status_code == 201
    data = res.json()
    assert "Inconclusive" in data["root_cause"] or "not definitively confirmed" in data["root_cause"]
    assert any("insufficient" in lesson.lower() for lesson in data["lessons_learned"])


def test_evaluation_calculation_and_grounding(client, test_setup):
    """
    Test evaluating an investigation produces deterministic 0-100 scores and explanations.
    """
    inv = test_setup["investigation"]
    res = client.post(f"/api/v1/investigations/{inv.id}/evaluate")
    assert res.status_code == 201
    data = res.json()

    assert data["investigation_id"] == str(inv.id)
    assert 0.0 <= data["overall_score"] <= 100.0
    assert 0.0 <= data["evidence_score"] <= 100.0
    assert 0.0 <= data["hypothesis_score"] <= 100.0
    assert 0.0 <= data["verification_score"] <= 100.0
    assert 0.0 <= data["rag_score"] <= 100.0
    assert 0.0 <= data["tool_efficiency_score"] <= 100.0

    # Verification was rigorous: 1 supported + 1 not supported
    assert data["verification_score"] >= 80.0
    assert "Investigation Quality Score" in data["evaluation_reasoning"]
    assert "metrics_breakdown" in data
    assert data["metrics_breakdown"]["evidence"]["count"] == 2


def test_evaluation_retrieval(client, test_setup):
    """
    Test GET /api/v1/investigations/{id}/evaluation retrieves evaluation record.
    """
    inv = test_setup["investigation"]
    res_gen = client.post(f"/api/v1/investigations/{inv.id}/evaluate")
    assert res_gen.status_code == 201

    res_get = client.get(f"/api/v1/investigations/{inv.id}/evaluation")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == res_gen.json()["id"]


def test_evaluations_list_endpoint(client, test_setup):
    """
    Test GET /api/v1/evaluations returns paginated list of evaluations.
    """
    inv = test_setup["investigation"]
    client.post(f"/api/v1/investigations/{inv.id}/evaluate")

    res = client.get("/api/v1/evaluations?skip=0&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(item["investigation_id"] == str(inv.id) for item in data["items"])


def test_evaluation_tool_efficiency_redundancy_penalty(client, db_session, test_setup):
    """
    Test that redundant duplicate tool calls decrease the tool efficiency score.
    """
    svc = test_setup["service"]
    inc = test_setup["incident"]

    inv = Investigation(
        incident_id=inc.id,
        investigation_number=f"INV-DUP-{uuid.uuid4().hex[:4].upper()}",
        status="Completed",
        probable_root_cause="Deadlock",
        confidence_score=0.85,
    )
    db_session.add(inv)
    db_session.flush()

    # Add 4 identical tool calls (3 duplicates)
    for _ in range(4):
        tc = ToolCall(
            investigation_id=inv.id,
            tool_name="query_prometheus",
            arguments={"query": "cpu_utilization"},
            status="SUCCESS",
            execution_time_ms=30,
        )
        db_session.add(tc)
    db_session.commit()

    service = EvaluationService(db_session)
    eval_rec = service.evaluate_investigation(inv.id)
    # Efficiency penalized due to 3 duplicate calls
    assert eval_rec.tool_efficiency_score < 80.0


def test_evaluation_inconclusive_penalty_factor(client, db_session, test_setup):
    """
    Test that inconclusive investigation applies the appropriate outcome adjustment.
    """
    inc = test_setup["incident"]

    inv = Investigation(
        incident_id=inc.id,
        investigation_number=f"INV-INC-EVAL-{uuid.uuid4().hex[:4].upper()}",
        status="Inconclusive",
        probable_root_cause=None,
        confidence_score=0.30,
    )
    db_session.add(inv)
    db_session.commit()

    service = EvaluationService(db_session)
    eval_rec = service.evaluate_investigation(inv.id)
    assert eval_rec.metrics_breakdown["outcome"]["factor_applied"] == 0.85
