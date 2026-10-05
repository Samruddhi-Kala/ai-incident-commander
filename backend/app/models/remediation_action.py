import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation
    from app.models.user import User
    from app.models.audit_log import AuditLog


class RemediationAction(Base):
    """
    Proposed, approved, rejected, or executed remediation actions.
    """
    __tablename__ = "remediation_actions"

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
    action_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., rollback_deployment, restart_service
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="HIGH",
    )  # LOW, MEDIUM, HIGH, CRITICAL
    approval_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PROPOSED",
        index=True,
    )  # PROPOSED, PENDING_APPROVAL, APPROVED, REJECTED, EXECUTING, COMPLETED, FAILED
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    execution_result: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="remediation_actions",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="approved_remediations",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="remediation_action",
    )
