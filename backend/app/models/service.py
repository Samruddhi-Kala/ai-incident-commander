import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.document import Document


class Service(Base):
    """
    Service catalog detailing microservices, databases, and dependencies.
    """
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )  # e.g., payment-service
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    owner_team: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Tier-2",
    )  # Tier-0, Tier-1, Tier-2
    repository_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    dependencies: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )  # Array of upstream service names
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="associated_service",
    )
