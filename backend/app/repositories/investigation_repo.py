import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.repositories.base import BaseRepository


class InvestigationRepository(BaseRepository[Investigation]):
    def __init__(self, db: Session):
        super().__init__(Investigation, db)

    def get_by_incident_id(self, incident_id: uuid.UUID) -> Optional[Investigation]:
        """
        Get active investigation session for an incident.
        """
        statement = select(Investigation).where(Investigation.incident_id == incident_id).order_by(Investigation.created_at.desc())
        return self.db.scalars(statement).first()

    def get_by_number(self, investigation_number: str) -> Optional[Investigation]:
        """
        Lookup investigation by investigation number (e.g. INV-1042).
        """
        statement = select(Investigation).where(Investigation.investigation_number == investigation_number)
        return self.db.scalars(statement).first()
