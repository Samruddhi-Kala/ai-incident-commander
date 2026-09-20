import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import PaginatedResponse
from app.schemas.service import ServiceResponse
from app.schemas.investigation import InvestigationResponse


class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Short incident title")
    description: str = Field(..., min_length=1, description="Full incident/alert description")
    severity: str = Field("SEV-2", description="Severity level: SEV-1, SEV-2, SEV-3, SEV-4")
    status: str = Field("Triggered", description="Status: Triggered, Investigating, Mitigated, Resolved")


class IncidentCreate(IncidentBase):
    service_id: uuid.UUID = Field(..., description="ID of the affected service")
    assigned_to: Optional[uuid.UUID] = Field(None, description="ID of assigned responder user")


class IncidentIngest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    severity: str = Field("SEV-2", description="SEV-1, SEV-2, SEV-3, SEV-4")
    service_name: str = Field(..., min_length=1, max_length=100, description="Canonical service name, e.g. payment-service")
    source: Optional[str] = Field("monitoring", description="Source platform name, e.g. Datadog, CloudWatch")


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    severity: Optional[str] = Field(None, description="SEV-1, SEV-2, SEV-3, SEV-4")
    status: Optional[str] = Field(None, description="Triggered, Investigating, Mitigated, Resolved")
    service_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    service: Optional[ServiceResponse] = None
    investigation: Optional[InvestigationResponse] = None


class IncidentListResponse(PaginatedResponse[IncidentResponse]):
    pass
