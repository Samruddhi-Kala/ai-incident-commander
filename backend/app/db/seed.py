import sys
import os
import uuid
from typing import Dict, Any

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation


def seed_development_data() -> Dict[str, Any]:
    """
    Seeds initial development sample data (users, services, incidents).
    Returns created entity IDs.
    """
    db = SessionLocal()
    try:
        # 1. Seed Sample Users
        user_alex = db.query(User).filter_by(email="alex.sre@dev.local").first()
        if not user_alex:
            user_alex = User(
                email="alex.sre@dev.local",
                full_name="Alex (Dev SRE)",
                hashed_password="dev_password_hash_placeholder",
                role="Responder",
                is_active=True,
            )
            db.add(user_alex)

        user_priya = db.query(User).filter_by(email="priya.ic@dev.local").first()
        if not user_priya:
            user_priya = User(
                email="priya.ic@dev.local",
                full_name="Priya (Dev IC)",
                hashed_password="dev_password_hash_placeholder",
                role="IncidentCommander",
                is_active=True,
            )
            db.add(user_priya)

        db.flush()

        # 2. Seed Sample Services
        payment_service = db.query(Service).filter_by(name="payment-service").first()
        if not payment_service:
            payment_service = Service(
                name="payment-service",
                description="Core payment processing microservice (DEV MOCK)",
                owner_team="Payment Core",
                tier="Tier-0",
                repository_url="https://github.com/mock-org/payment-service",
                dependencies=["auth-service", "database-cluster"],
            )
            db.add(payment_service)

        auth_service = db.query(Service).filter_by(name="auth-service").first()
        if not auth_service:
            auth_service = Service(
                name="auth-service",
                description="User authentication service (DEV MOCK)",
                owner_team="Identity",
                tier="Tier-1",
                repository_url="https://github.com/mock-org/auth-service",
                dependencies=["database-cluster"],
            )
            db.add(auth_service)

        db.flush()

        # 3. Seed Sample Incidents
        incident_1 = db.query(Incident).filter_by(title="Payment API elevated 504 error rate").first()
        if not incident_1:
            incident_1 = Incident(
                title="Payment API elevated 504 error rate",
                description="Alert: payment-service gateway error rate spiked from 0.1% to 18.4% following deployment.",
                severity="SEV-1",
                status="Investigating",
                service_id=payment_service.id,
                assigned_to=user_alex.id,
            )
            db.add(incident_1)
            db.flush()

            # Seed associated Investigation
            investigation_1 = Investigation(
                incident_id=incident_1.id,
                investigation_number="INV-1042",
                status="Active",
                probable_root_cause=None,
                confidence_score=None,
            )
            db.add(investigation_1)

        db.commit()
        return {
            "user_ids": [str(user_alex.id), str(user_priya.id)],
            "service_ids": [str(payment_service.id), str(auth_service.id)],
            "incident_ids": [str(incident_1.id)],
        }
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding development data...")
    res = seed_development_data()
    print("Development data seeded successfully:", res)
