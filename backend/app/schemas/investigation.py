import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    investigation_number: str
    status: str
    probable_root_cause: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
