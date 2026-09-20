import uuid
import random
from typing import Optional
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.repositories.investigation_repo import InvestigationRepository
from app.core.logging import logger


class InvestigationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InvestigationRepository(db)

    def initialize_investigation(self, incident_id: uuid.UUID) -> Investigation:
        """
        Initializes a new active investigation session linked to an incident.
        Generates a unique readable investigation number (e.g. INV-8492).
        """
        existing = self.repo.get_by_incident_id(incident_id)
        if existing:
            return existing

        # Generate unique investigation number
        inv_number = f"INV-{random.randint(1000, 9999)}"
        while self.repo.get_by_number(inv_number) is not None:
            inv_number = f"INV-{random.randint(1000, 9999)}"

        investigation = Investigation(
            incident_id=incident_id,
            investigation_number=inv_number,
            status="Active",
        )
        created = self.repo.create(investigation)
        logger.info(f"Initialized investigation '{created.investigation_number}' for incident '{incident_id}'")
        return created

    def get_by_incident_id(self, incident_id: uuid.UUID) -> Optional[Investigation]:
        """
        Gets current investigation for an incident.
        """
        return self.repo.get_by_incident_id(incident_id)
