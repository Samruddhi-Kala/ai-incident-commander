import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.hypothesis import Hypothesis
from app.repositories.base import BaseRepository


class HypothesisRepository(BaseRepository[Hypothesis]):
    def __init__(self, db: Session):
        super().__init__(Hypothesis, db)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[Hypothesis]:
        """
        List diagnostic hypotheses evaluated for an investigation.
        """
        statement = select(Hypothesis).where(Hypothesis.investigation_id == investigation_id).order_by(Hypothesis.confidence_score.desc())
        return list(self.db.scalars(statement).all())
