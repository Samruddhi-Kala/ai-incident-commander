import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.postmortem import Postmortem
from app.repositories.base import BaseRepository


class PostmortemRepository(BaseRepository[Postmortem]):
    """
    Repository for persisting and querying postmortem records.
    """
    def __init__(self, db: Session):
        super().__init__(Postmortem, db)

    def get_by_investigation(self, investigation_id: uuid.UUID) -> Optional[Postmortem]:
        """Retrieve the postmortem associated with a given investigation."""
        statement = select(Postmortem).where(Postmortem.investigation_id == investigation_id)
        return self.db.scalars(statement).first()
