"""
Pydantic schemas for Phase 9: AI Investigation Evaluation
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationMetricsBreakdown(BaseModel):
    """Detailed score components and rationales."""
    evidence: Dict[str, Any] = Field(default_factory=dict)
    hypothesis: Dict[str, Any] = Field(default_factory=dict)
    verification: Dict[str, Any] = Field(default_factory=dict)
    rag: Dict[str, Any] = Field(default_factory=dict)
    tool_efficiency: Dict[str, Any] = Field(default_factory=dict)
    outcome: Dict[str, Any] = Field(default_factory=dict)


class InvestigationEvaluationResponse(BaseModel):
    """Structured response for an investigation quality evaluation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    investigation_id: uuid.UUID
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall normalized quality score (0-100)")
    evidence_score: float = Field(..., ge=0.0, le=100.0, description="Evidence support quality (0-100)")
    hypothesis_score: float = Field(..., ge=0.0, le=100.0, description="Hypothesis formation quality (0-100)")
    verification_score: float = Field(..., ge=0.0, le=100.0, description="Verification testing rigor (0-100)")
    rag_score: float = Field(..., ge=0.0, le=100.0, description="RAG knowledge retrieval relevance (0-100)")
    tool_efficiency_score: float = Field(..., ge=0.0, le=100.0, description="Diagnostic tool execution efficiency (0-100)")
    evaluation_reasoning: str = Field(..., description="Explainable diagnostic breakdown of the score")
    metrics_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Granular heuristic metrics details")
    created_at: datetime


class EvaluationListResponse(BaseModel):
    """Paginated list of investigation evaluations."""
    items: List[InvestigationEvaluationResponse]
    total: int
