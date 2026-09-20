import uuid
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.repositories.incident_repo import IncidentRepository
from app.repositories.service_repo import ServiceRepository
from app.services.investigation_service import InvestigationService
from app.schemas.incident import IncidentCreate, IncidentIngest, IncidentUpdate
from app.core.exceptions import (
    IncidentNotFoundError,
    ServiceNotFoundError,
    InvalidIncidentStateError,
)
from app.core.logging import logger

VALID_SEVERITIES = {"SEV-1", "SEV-2", "SEV-3", "SEV-4"}
VALID_STATUSES = {"Triggered", "Investigating", "Mitigated", "Resolved"}


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = IncidentRepository(db)
        self.service_repo = ServiceRepository(db)
        self.investigation_service = InvestigationService(db)

    def create_incident(self, incident_in: IncidentCreate) -> Incident:
        """
        Creates a new incident, verifies service existence, and initializes investigation session.
        """
        service = self.service_repo.get_by_id(incident_in.service_id)
        if not service:
            raise ServiceNotFoundError(f"Service with ID '{incident_in.service_id}' not found.")

        if incident_in.severity not in VALID_SEVERITIES:
            raise InvalidIncidentStateError(f"Invalid severity '{incident_in.severity}'. Must be one of {VALID_SEVERITIES}")

        if incident_in.status not in VALID_STATUSES:
            raise InvalidIncidentStateError(f"Invalid status '{incident_in.status}'. Must be one of {VALID_STATUSES}")

        incident = Incident(
            title=incident_in.title,
            description=incident_in.description,
            severity=incident_in.severity,
            status=incident_in.status,
            service_id=incident_in.service_id,
            assigned_to=incident_in.assigned_to,
        )
        created_incident = self.repo.create(incident)

        # Initialize initial investigation session
        self.investigation_service.initialize_investigation(created_incident.id)

        logger.info(f"Incident created: '{created_incident.title}' [ID: {created_incident.id}, Severity: {created_incident.severity}]")
        return self.get_incident(created_incident.id)

    def ingest_incident(self, ingest_in: IncidentIngest) -> Incident:
        """
        Handles incident ingestion from external monitoring triggers.
        Looks up service by name; rejects if service does not exist.
        """
        service = self.service_repo.get_by_name(ingest_in.service_name)
        if not service:
            raise ServiceNotFoundError(
                f"Cannot ingest incident. Service '{ingest_in.service_name}' not found in catalog."
            )

        if ingest_in.severity not in VALID_SEVERITIES:
            raise InvalidIncidentStateError(f"Invalid severity '{ingest_in.severity}'. Must be one of {VALID_SEVERITIES}")

        source_label = ingest_in.source.upper() if ingest_in.source else "MONITORING"
        description_text = f"[{source_label} ALERT] {ingest_in.description}"

        incident = Incident(
            title=ingest_in.title,
            description=description_text,
            severity=ingest_in.severity,
            status="Triggered",
            service_id=service.id,
        )
        created_incident = self.repo.create(incident)

        # Initialize initial investigation session
        self.investigation_service.initialize_investigation(created_incident.id)

        logger.info(f"Ingested alert into incident '{created_incident.title}' [Service: {service.name}]")
        return self.get_incident(created_incident.id)

    def get_incident(self, incident_id: uuid.UUID) -> Incident:
        """
        Retrieves incident by ID with service and investigation details.
        """
        incident = self.repo.get_with_details(incident_id)
        if not incident:
            raise IncidentNotFoundError(f"Incident with ID '{incident_id}' not found.")
        return incident

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service_id: Optional[uuid.UUID] = None,
        assigned_to: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Incident], int]:
        """
        Lists incidents with filtering and pagination.
        """
        skip = (page - 1) * page_size
        return self.repo.list_with_filters(
            status=status,
            severity=severity,
            service_id=service_id,
            assigned_to=assigned_to,
            skip=skip,
            limit=page_size,
        )

    def update_incident(self, incident_id: uuid.UUID, incident_in: IncidentUpdate) -> Incident:
        """
        Updates an existing incident.
        """
        incident = self.get_incident(incident_id)

        if incident_in.service_id and incident_in.service_id != incident.service_id:
            service = self.service_repo.get_by_id(incident_in.service_id)
            if not service:
                raise ServiceNotFoundError(f"Service with ID '{incident_in.service_id}' not found.")

        if incident_in.severity and incident_in.severity not in VALID_SEVERITIES:
            raise InvalidIncidentStateError(f"Invalid severity '{incident_in.severity}'. Must be one of {VALID_SEVERITIES}")

        if incident_in.status and incident_in.status not in VALID_STATUSES:
            raise InvalidIncidentStateError(f"Invalid status '{incident_in.status}'. Must be one of {VALID_STATUSES}")

        update_data = incident_in.model_dump(exclude_unset=True)

        # Handle automatic resolved_at timestamp when status transitions to Resolved
        if incident_in.status == "Resolved" and incident.resolved_at is None and "resolved_at" not in update_data:
            update_data["resolved_at"] = datetime.now(timezone.utc)

        updated = self.repo.update(incident, update_data)
        logger.info(f"Updated incident '{updated.id}' [Status: {updated.status}]")
        return self.get_incident(updated.id)
