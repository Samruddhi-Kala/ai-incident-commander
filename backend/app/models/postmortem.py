import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class Postmortem(Base):
    """
    Structured postmortem document generated from completed or inconclusive investigations.
    Grounded in persisted incident, investigation, evidence, and remediation data.
    """
    __tablename__ = "postmortems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    impact: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    timeline: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    root_cause: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    contributing_factors: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    remediation: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    lessons_learned: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    preventive_actions: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="postmortem",
    )
