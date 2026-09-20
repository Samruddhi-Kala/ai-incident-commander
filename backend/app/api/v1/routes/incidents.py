import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.incident_service import IncidentService
from app.schemas.incident import (
    IncidentCreate,
    IncidentIngest,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
)
from app.schemas.investigation import InvestigationResponse

router = APIRouter()


def _format_incident_response(incident) -> IncidentResponse:
    """
    Formats ORM Incident model into IncidentResponse schema attaching primary investigation if available.
    """
    resp = IncidentResponse.model_validate(incident)
    if incident.investigations:
        primary_inv = incident.investigations[0]
        resp.investigation = InvestigationResponse.model_validate(primary_inv)
    return resp


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident",
)
def create_incident(
    incident_in: IncidentCreate,
    db: Session = Depends(get_db),
):
    incident_svc = IncidentService(db)
    incident = incident_svc.create_incident(incident_in)
    return _format_incident_response(incident)


@router.post(
    "/ingest",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest incident from external monitoring trigger",
)
def ingest_incident(
    ingest_in: IncidentIngest,
    db: Session = Depends(get_db),
):
    incident_svc = IncidentService(db)
    incident = incident_svc.ingest_incident(ingest_in)
    return _format_incident_response(incident)


@router.get(
    "",
    response_model=IncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List incidents with filtering and pagination",
)
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Triggered, Investigating, Mitigated, Resolved)"),
    severity_filter: Optional[str] = Query(None, alias="severity", description="Filter by severity (SEV-1, SEV-2, SEV-3, SEV-4)"),
    service_id: Optional[uuid.UUID] = Query(None, description="Filter by service ID"),
    assigned_to: Optional[uuid.UUID] = Query(None, description="Filter by assigned user ID"),
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    incident_svc = IncidentService(db)
    items, total = incident_svc.list_incidents(
        status=status_filter,
        severity=severity_filter,
        service_id=service_id,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size,
    )
    formatted_items = [_format_incident_response(item) for item in items]
    return IncidentListResponse.create(items=formatted_items, page=page, page_size=page_size, total=total)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get incident details by ID",
)
def get_incident(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    incident_svc = IncidentService(db)
    incident = incident_svc.get_incident(incident_id)
    return _format_incident_response(incident)


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing incident",
)
def update_incident(
    incident_id: uuid.UUID,
    incident_in: IncidentUpdate,
    db: Session = Depends(get_db),
):
    incident_svc = IncidentService(db)
    incident = incident_svc.update_incident(incident_id, incident_in)
    return _format_incident_response(incident)
