import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.remediation_action import RemediationAction
from app.repositories.base import BaseRepository


class RemediationActionRepository(BaseRepository[RemediationAction]):
    """
    Repository for persisting and querying remediation action entities.
    """
    def __init__(self, db: Session):
        super().__init__(RemediationAction, db)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[RemediationAction]:
        """
        List all remediation proposals formulated for an investigation.
        """
        statement = (
            select(RemediationAction)
            .where(RemediationAction.investigation_id == investigation_id)
            .order_by(RemediationAction.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_by_status(self, status: str) -> List[RemediationAction]:
        """
        List remediation actions matching a specific lifecycle status.
        """
        statement = (
            select(RemediationAction)
            .where(RemediationAction.approval_status == status)
            .order_by(RemediationAction.created_at.desc())
        )
        return list(self.db.scalars(statement).all())
