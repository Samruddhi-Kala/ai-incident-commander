import uuid
from typing import TYPE_CHECKING, Any, Optional
from sqlalchemy import Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(Base):
    """
    Document text chunks with dense vector embeddings for RAG retrieval.
    """
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index(
            "idx_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "idx_chunks_ts_vector",
            "ts_vector",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Using 'metadata' as DB column name while naming Python property 'chunk_metadata' to avoid conflict with Base.metadata
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    embedding: Mapped[Any] = mapped_column(
        Vector(1536),
        nullable=False,
    )
    ts_vector: Mapped[Optional[Any]] = mapped_column(
        TSVECTOR,
        nullable=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )
