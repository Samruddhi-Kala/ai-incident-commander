"""
Pydantic schemas for Phase 9: Incident Postmortem Document
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PostmortemTimelineItem(BaseModel):
    """Structured event in the postmortem incident timeline."""
    timestamp: Optional[str] = None
    stage: str
    description: str
    source: Optional[str] = None


class PostmortemCreate(BaseModel):
    """Payload to trigger postmortem generation for an investigation."""
    investigation_id: uuid.UUID
    regenerate: bool = Field(default=False, description="Whether to re-generate if a postmortem already exists")


class PostmortemResponse(BaseModel):
    """Structured representation of a persisted incident postmortem."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    investigation_id: uuid.UUID
    title: str
    summary: str
    impact: str
    timeline: List[Dict[str, Any]]
    root_cause: str
    contributing_factors: List[str]
    remediation: Dict[str, Any]
    lessons_learned: List[str]
    preventive_actions: List[str]
    details: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime
