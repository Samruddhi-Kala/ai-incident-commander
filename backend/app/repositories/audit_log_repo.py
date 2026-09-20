import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def list_by_incident(self, incident_id: uuid.UUID) -> List[AuditLog]:
        """
        List audit logs associated with a specific incident ID.
        """
        statement = select(AuditLog).where(AuditLog.incident_id == incident_id).order_by(AuditLog.created_at.desc())
        return list(self.db.scalars(statement).all())
