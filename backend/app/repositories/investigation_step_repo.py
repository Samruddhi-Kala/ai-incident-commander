import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.investigation_step import InvestigationStep
from app.repositories.base import BaseRepository


class InvestigationStepRepository(BaseRepository[InvestigationStep]):
    """
    Repository for persisting and querying agent investigation workflow steps.
    """
    def __init__(self, db: Session):
        super().__init__(InvestigationStep, db)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[InvestigationStep]:
        """
        List all steps recorded for an investigation ordered by step_order.
        """
        statement = (
            select(InvestigationStep)
            .where(InvestigationStep.investigation_id == investigation_id)
            .order_by(InvestigationStep.step_order.asc())
        )
        return list(self.db.scalars(statement).all())

    def record_step(
        self,
        investigation_id: uuid.UUID,
        step_order: int,
        title: str,
        status: str = "Completed",
        output_summary: Optional[str] = None,
    ) -> InvestigationStep:
        """
        Creates and persists an investigation step entry.
        """
        step = InvestigationStep(
            investigation_id=investigation_id,
            step_order=step_order,
            title=title,
            status=status,
            output_summary=output_summary,
        )
        return self.create(step)
