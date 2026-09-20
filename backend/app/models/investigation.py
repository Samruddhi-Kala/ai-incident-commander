import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.investigation_step import InvestigationStep
    from app.models.evidence import Evidence
    from app.models.hypothesis import Hypothesis
    from app.models.tool_call import ToolCall
    from app.models.remediation_action import RemediationAction


class Investigation(Base):
    """
    Represents an active or historical agent investigation session.
    """
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    investigation_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )  # e.g., INV-1042
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Active",
    )  # Active, Awaiting_Approval, Completed, Failed
    probable_root_cause: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="investigations",
    )
    steps: Mapped[List["InvestigationStep"]] = relationship(
        "InvestigationStep",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationStep.step_order",
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    hypotheses: Mapped[List["Hypothesis"]] = relationship(
        "Hypothesis",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    tool_calls: Mapped[List["ToolCall"]] = relationship(
        "ToolCall",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    remediation_actions: Mapped[List["RemediationAction"]] = relationship(
        "RemediationAction",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
