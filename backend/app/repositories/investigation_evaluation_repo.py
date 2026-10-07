import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.investigation_evaluation import InvestigationEvaluation
from app.repositories.base import BaseRepository


class InvestigationEvaluationRepository(BaseRepository[InvestigationEvaluation]):
    """
    Repository for persisting and querying investigation evaluation records.
    """
    def __init__(self, db: Session):
        super().__init__(InvestigationEvaluation, db)

    def get_latest_by_investigation(self, investigation_id: uuid.UUID) -> Optional[InvestigationEvaluation]:
        """Retrieve the latest evaluation record for an investigation."""
        statement = (
            select(InvestigationEvaluation)
            .where(InvestigationEvaluation.investigation_id == investigation_id)
            .order_by(InvestigationEvaluation.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def list_with_count(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[InvestigationEvaluation], int]:
        """List evaluations with pagination, returning (items, total_count)."""
        count_stmt = select(func.count()).select_from(InvestigationEvaluation)
        total = self.db.scalar(count_stmt) or 0

        items_stmt = (
            select(InvestigationEvaluation)
            .order_by(InvestigationEvaluation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.scalars(items_stmt).all())
        return items, total
