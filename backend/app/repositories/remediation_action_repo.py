import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
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

    def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[RemediationAction]:
        """
        List remediation actions matching a specific lifecycle status with optional pagination.
        """
        status_val = status.value if hasattr(status, "value") else str(status).strip()
        statement = (
            select(RemediationAction)
            .where(func.upper(RemediationAction.approval_status) == status_val.upper())
            .order_by(RemediationAction.created_at.desc())
            .offset(skip)
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement).all())

    def list_with_count(
        self,
        skip: int = 0,
        limit: Optional[int] = 50,
        status: Optional[str] = None,
    ) -> Tuple[List[RemediationAction], int]:
        """
        List remediation actions with pagination and optional status filter, returning (items, total_count).
        """
        base_stmt = select(RemediationAction)
        count_stmt = select(func.count()).select_from(RemediationAction)

        if status:
            status_val = status.value if hasattr(status, "value") else str(status).strip()
            base_stmt = base_stmt.where(func.upper(RemediationAction.approval_status) == status_val.upper())
            count_stmt = count_stmt.where(func.upper(RemediationAction.approval_status) == status_val.upper())

        total = self.db.scalar(count_stmt) or 0
        items_stmt = (
            base_stmt
            .order_by(RemediationAction.created_at.desc())
            .offset(skip)
        )
        if limit is not None:
            items_stmt = items_stmt.limit(limit)
        items = list(self.db.scalars(items_stmt).all())
        return items, total
