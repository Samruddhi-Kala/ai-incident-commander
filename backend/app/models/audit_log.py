import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User
    from app.models.remediation_action import RemediationAction


class AuditLog(Base):
    """
    Append-only application audit log for security and investigation history.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    remediation_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("remediation_actions.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # SYSTEM_AGENT, HUMAN_USER
    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident",
        back_populates="audit_logs",
    )
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )
    remediation_action: Mapped[Optional["RemediationAction"]] = relationship(
        "RemediationAction",
        back_populates="audit_logs",
    )
