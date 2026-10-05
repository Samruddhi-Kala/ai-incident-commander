import uuid
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing basic CRUD database access patterns.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """
        Retrieves a single model instance by primary key UUID.
        """
        return self.db.get(self.model, id)

    def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """
        Alias for get_by_id.
        """
        return self.get_by_id(id)

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Lists model instances with pagination offset and limit.
        """
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())

    def count(self) -> int:
        """
        Returns total count of model instances in table.
        """
        statement = select(func.count()).select_from(self.model)
        return self.db.scalar(statement) or 0

    def create(self, instance: ModelType) -> ModelType:
        """
        Persists a new model instance.
        """
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, instance: ModelType, update_data: dict[str, Any]) -> ModelType:
        """
        Updates fields on an existing model instance.
        """
        for field, value in update_data.items():
            if hasattr(instance, field) and value is not None:
                setattr(instance, field, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: uuid.UUID) -> bool:
        """
        Deletes a model instance by ID. Returns True if deleted, False if not found.
        """
        instance = self.get_by_id(id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True
