import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.models.user import User
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.evidence import Evidence
from app.models.hypothesis import Hypothesis
from app.repositories.service_repo import ServiceRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.investigation_repo import InvestigationRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.hypothesis_repo import HypothesisRepository


@pytest.fixture
def db_session():
    """
    Provides a clean SQLAlchemy session for database integration testing.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_service_repository_crud(db_session):
    """
    Test ServiceRepository create, lookup by name, and delete operations.
    """
    repo = ServiceRepository(db_session)
    unique_name = f"test-svc-{uuid.uuid4().hex[:8]}"

    # Create
    svc = Service(
        name=unique_name,
        description="Test microservice for repository unit tests",
        owner_team="Platform Team",
        tier="Tier-2",
        dependencies=["postgres-db"],
    )
    created_svc = repo.create(svc)
    assert created_svc.id is not None
    assert created_svc.name == unique_name

    # Lookup by name
    fetched_svc = repo.get_by_name(unique_name)
    assert fetched_svc is not None
    assert fetched_svc.id == created_svc.id

    # Cleanup
    deleted = repo.delete(created_svc.id)
    assert deleted is True


def test_incident_and_investigation_relationships(db_session):
    """
    Test creating Service -> Incident -> Investigation -> Evidence & Hypothesis chain.
    """
    svc_repo = ServiceRepository(db_session)
    inc_repo = IncidentRepository(db_session)
    inv_repo = InvestigationRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    hyp_repo = HypothesisRepository(db_session)

    # 1. Create parent service
    svc_name = f"payment-api-{uuid.uuid4().hex[:6]}"
    svc = svc_repo.create(Service(
        name=svc_name,
        owner_team="Payment Team",
        tier="Tier-0",
    ))

    # 2. Create Incident
    inc = inc_repo.create(Incident(
        title="Payment Error Rate Spike",
        description="Gateway timeouts elevated",
        severity="SEV-1",
        status="Investigating",
        service_id=svc.id,
    ))
    assert inc.id is not None
    assert inc.service_id == svc.id

    # 3. Create Investigation
    inv_num = f"INV-{uuid.uuid4().hex[:6].upper()}"
    inv = inv_repo.create(Investigation(
        incident_id=inc.id,
        investigation_number=inv_num,
        status="Active",
    ))
    assert inv.id is not None
    assert inv.incident_id == inc.id

    # 4. Create Evidence item
    evidence_item = ev_repo.create(Evidence(
        investigation_id=inv.id,
        source_tool="search_logs",
        summary="Logs show HTTP 504 gateway timeout errors",
        raw_payload={"error_code": 504, "count": 142},
        relevance_score=0.9,
    ))
    assert evidence_item.id is not None

    # 5. Create Hypothesis
    hypothesis_item = hyp_repo.create(Hypothesis(
        investigation_id=inv.id,
        hypothesis_text="Recent deployment changed gateway timeout setting",
        status="Proposed",
        supporting_evidence_ids=[evidence_item.id],
        confidence_score=0.85,
    ))
    assert hypothesis_item.id is not None
    assert evidence_item.id in hypothesis_item.supporting_evidence_ids

    # 6. Verify Relationships
    fetched_inv = inv_repo.get_by_id(inv.id)
    assert fetched_inv is not None
    assert len(fetched_inv.evidence) >= 1
    assert len(fetched_inv.hypotheses) >= 1
    assert fetched_inv.incident.title == "Payment Error Rate Spike"

    # Cleanup
    inc_repo.delete(inc.id)
    svc_repo.delete(svc.id)


def test_unique_constraint_enforcement(db_session):
    """
    Test duplicate service name triggers IntegrityError.
    """
    repo = ServiceRepository(db_session)
    name = f"dup-service-{uuid.uuid4().hex[:6]}"

    svc1 = Service(name=name, owner_team="Team A", tier="Tier-1")
    repo.create(svc1)

    svc2 = Service(name=name, owner_team="Team B", tier="Tier-2")
    with pytest.raises(IntegrityError):
        repo.create(svc2)
    db_session.rollback()

    # Cleanup
    repo.delete(svc1.id)
