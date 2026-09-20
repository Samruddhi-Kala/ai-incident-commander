from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.service import Service
from app.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: Session):
        super().__init__(Service, db)

    def get_by_name(self, name: str) -> Optional[Service]:
        """
        Lookup service by canonical name (e.g. payment-service).
        """
        statement = select(Service).where(Service.name == name)
        return self.db.scalars(statement).first()
