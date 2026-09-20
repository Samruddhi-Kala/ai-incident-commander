import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.service_service import ServiceService
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service in the catalog",
)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
):
    service_svc = ServiceService(db)
    return service_svc.create_service(service_in)


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get service by ID",
)
def get_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service_svc = ServiceService(db)
    return service_svc.get_service(service_id)


@router.get(
    "",
    response_model=ServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List services with pagination",
)
def list_services(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    service_svc = ServiceService(db)
    items, total = service_svc.list_services(page=page, page_size=page_size)
    return ServiceListResponse.create(items=items, page=page, page_size=page_size, total=total)


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing service",
)
def update_service(
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    db: Session = Depends(get_db),
):
    service_svc = ServiceService(db)
    return service_svc.update_service(service_id, service_in)
