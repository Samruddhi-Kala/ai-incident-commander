import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class InvestigationEvaluation(Base):
    """
    Quantitative and qualitative evaluation of an AI incident investigation session.
    Calculates deterministic heuristic engineering metrics (0-100) across evidence support,
    hypothesis quality, verification rigor, RAG relevance, and tool execution efficiency.
    """
    __tablename__ = "investigation_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    evidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    hypothesis_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    verification_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    rag_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    tool_efficiency_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    evaluation_reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    metrics_breakdown: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="evaluations",
    )
