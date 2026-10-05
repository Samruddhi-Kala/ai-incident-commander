import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class ToolCall(Base):
    """
    Record of diagnostic and remediation tool calls.
    """
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    investigation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    arguments: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Success",
    )  # Success, Error, Timeout
    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    investigation: Mapped[Optional["Investigation"]] = relationship(
        "Investigation",
        back_populates="tool_calls",
    )
