import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.evidence import Evidence
from app.repositories.base import BaseRepository


class EvidenceRepository(BaseRepository[Evidence]):
    def __init__(self, db: Session):
        super().__init__(Evidence, db)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[Evidence]:
        """
        List all telemetry evidence items collected for an investigation.
        """
        statement = select(Evidence).where(Evidence.investigation_id == investigation_id).order_by(Evidence.collected_at.asc())
        return list(self.db.scalars(statement).all())
