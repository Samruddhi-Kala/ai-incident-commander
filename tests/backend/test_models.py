import uuid
from app.models.user import User
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation


def test_user_model_instantiation():
    """
    Test User model creation and field attributes.
    """
    user = User(
        email="test@domain.com",
        full_name="Test User",
        hashed_password="hashed_secret",
        role="Responder",
        is_active=True,
    )
    assert user.email == "test@domain.com"
    assert user.role == "Responder"
    assert user.is_active is True


def test_service_model_instantiation():
    """
    Test Service model creation and JSONB default dependencies.
    """
    service = Service(
        name="test-service",
        owner_team="Core Team",
        tier="Tier-1",
        dependencies=["auth-service"],
    )
    assert service.name == "test-service"
    assert service.tier == "Tier-1"
    assert "auth-service" in service.dependencies


def test_incident_model_instantiation():
    """
    Test Incident model fields.
    """
    service_id = uuid.uuid4()
    incident = Incident(
        title="Elevated Error Rate",
        description="Service returning 500 status codes",
        severity="SEV-2",
        status="Triggered",
        service_id=service_id,
    )
    assert incident.title == "Elevated Error Rate"
    assert incident.severity == "SEV-2"
    assert incident.status == "Triggered"
    assert incident.service_id == service_id
