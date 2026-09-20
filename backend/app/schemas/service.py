import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import PaginatedResponse


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Canonical service name, e.g. payment-service")
    description: Optional[str] = Field(None, description="Human-readable summary of the service")
    owner_team: str = Field(..., min_length=1, max_length=100, description="Responsible engineering team")
    tier: str = Field("Tier-2", description="Service criticality tier (Tier-0, Tier-1, Tier-2)")
    repository_url: Optional[str] = Field(None, max_length=255, description="Git repository URL")
    dependencies: List[str] = Field(default_factory=list, description="Array of upstream service dependencies")


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    owner_team: Optional[str] = Field(None, min_length=1, max_length=100)
    tier: Optional[str] = None
    repository_url: Optional[str] = None
    dependencies: Optional[List[str]] = None


class ServiceResponse(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(PaginatedResponse[ServiceResponse]):
    pass
