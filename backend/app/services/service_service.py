import uuid
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.service import Service
from app.repositories.service_repo import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.core.exceptions import ServiceNotFoundError, DuplicateServiceError
from app.core.logging import logger


class ServiceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServiceRepository(db)

    def create_service(self, service_in: ServiceCreate) -> Service:
        """
        Creates a new service in the catalog after verifying uniqueness.
        """
        existing = self.repo.get_by_name(service_in.name)
        if existing:
            raise DuplicateServiceError(f"Service with name '{service_in.name}' already exists.")

        service = Service(
            name=service_in.name,
            description=service_in.description,
            owner_team=service_in.owner_team,
            tier=service_in.tier,
            repository_url=service_in.repository_url,
            dependencies=service_in.dependencies,
        )
        created = self.repo.create(service)
        logger.info(f"Service created: '{created.name}' [ID: {created.id}]")
        return created

    def get_service(self, service_id: uuid.UUID) -> Service:
        """
        Retrieves a single service by ID or raises ServiceNotFoundError.
        """
        service = self.repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFoundError(f"Service with ID '{service_id}' not found.")
        return service

    def list_services(self, page: int = 1, page_size: int = 20) -> Tuple[List[Service], int]:
        """
        Lists services with pagination metadata.
        """
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size)
        total = self.repo.count()
        return items, total

    def update_service(self, service_id: uuid.UUID, service_in: ServiceUpdate) -> Service:
        """
        Updates fields on an existing service.
        """
        service = self.get_service(service_id)

        if service_in.name and service_in.name != service.name:
            existing = self.repo.get_by_name(service_in.name)
            if existing and existing.id != service_id:
                raise DuplicateServiceError(f"Service with name '{service_in.name}' already exists.")

        update_dict = service_in.model_dump(exclude_unset=True)
        updated = self.repo.update(service, update_dict)
        logger.info(f"Service updated: '{updated.name}' [ID: {updated.id}]")
        return updated
