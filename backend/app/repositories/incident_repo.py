import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.incident import Incident
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, db: Session):
        super().__init__(Incident, db)

    def get_with_details(self, incident_id: uuid.UUID) -> Optional[Incident]:
        """
        Get incident by ID eagerly loading associated service and investigations.
        """
        statement = (
            select(Incident)
            .options(joinedload(Incident.service), selectinload(Incident.investigations))
            .where(Incident.id == incident_id)
        )
        return self.db.scalars(statement).first()

    def list_with_filters(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service_id: Optional[uuid.UUID] = None,
        assigned_to: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Incident], int]:
        """
        List incidents filtered by status, severity, service_id, assigned_to with pagination.
        Returns tuple of (items, total_count).
        """
        query = select(Incident).options(joinedload(Incident.service), selectinload(Incident.investigations))
        count_query = select(func.count()).select_from(Incident)

        filters = []
        if status:
            filters.append(Incident.status == status)
        if severity:
            filters.append(Incident.severity == severity)
        if service_id:
            filters.append(Incident.service_id == service_id)
        if assigned_to:
            filters.append(Incident.assigned_to == assigned_to)

        if filters:
            for cond in filters:
                query = query.where(cond)
                count_query = count_query.where(cond)

        query = query.order_by(Incident.created_at.desc()).offset(skip).limit(limit)

        total = self.db.scalar(count_query) or 0
        items = list(self.db.scalars(query).all())

        return items, total
