import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.service import Service
    from app.models.user import User
    from app.models.investigation import Investigation
    from app.models.audit_log import AuditLog


class Incident(Base):
    """
    Primary entity recording ingested production alerts and incidents.
    """
    __tablename__ = "incidents"
    __table_args__ = (
        Index("idx_incidents_status_severity", "status", "severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SEV-2",
    )  # SEV-1, SEV-2, SEV-3, SEV-4
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Triggered",
    )  # Triggered, Investigating, Mitigated, Resolved
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="incidents",
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_incidents",
    )
    investigations: Mapped[List["Investigation"]] = relationship(
        "Investigation",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="incident",
    )
