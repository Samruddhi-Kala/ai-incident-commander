import math
import uuid
from typing import List, Tuple, Optional
from sqlalchemy import select, delete, func, text
from sqlalchemy.orm import Session, joinedload
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.base import BaseRepository
from app.core.logging import logger


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self, db: Session):
        super().__init__(DocumentChunk, db)

    def create_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Persists a batch of DocumentChunk records.
        """
        if not chunks:
            return []

        self.db.add_all(chunks)
        self.db.flush()
        return chunks

    def delete_by_document_id(self, document_id: uuid.UUID) -> int:
        """
        Deletes all chunks belonging to a document.
        """
        statement = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = self.db.execute(statement)
        return result.rowcount

    def search_by_vector(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        service_id: Optional[uuid.UUID] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Performs vector similarity search against DocumentChunk.embedding.
        Returns tuples of (DocumentChunk, score), where score is similarity in [0, 1].
        """
        dialect_name = self.db.bind.dialect.name if self.db.bind else "postgresql"

        if dialect_name == "postgresql":
            # PostgreSQL + pgvector native cosine distance (<=>)
            distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
            stmt = (
                select(DocumentChunk, distance_col)
                .options(joinedload(DocumentChunk.document))
            )

            if service_id is not None:
                stmt = stmt.join(Document, DocumentChunk.document_id == Document.id).where(
                    Document.associated_service_id == service_id
                )

            stmt = stmt.order_by(text("distance ASC")).limit(top_k)
            rows = self.db.execute(stmt).all()

            results: List[Tuple[DocumentChunk, float]] = []
            for chunk, distance in rows:
                # Cosine distance is in [0, 2]; similarity is 1.0 - (distance / 2.0) or max(0, 1 - distance)
                sim_score = max(0.0, 1.0 - float(distance))
                results.append((chunk, round(sim_score, 4)))

            return results
        else:
            # Fallback for non-Postgres environments (e.g. SQLite unit tests)
            stmt = select(DocumentChunk).options(joinedload(DocumentChunk.document))
            if service_id is not None:
                stmt = stmt.join(Document, DocumentChunk.document_id == Document.id).where(
                    Document.associated_service_id == service_id
                )
            all_chunks = list(self.db.scalars(stmt).all())

            scored = []
            for chunk in all_chunks:
                # Calculate cosine similarity in Python
                emb = chunk.embedding
                if isinstance(emb, (list, tuple)) and len(emb) == len(query_embedding):
                    dot = sum(a * b for a, b in zip(emb, query_embedding))
                    scored.append((chunk, round(max(0.0, dot), 4)))
                else:
                    scored.append((chunk, 0.0))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

    def search_by_text(
        self,
        query: str,
        top_k: int = 5,
        service_id: Optional[uuid.UUID] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Performs full-text keyword search against DocumentChunk.
        Returns tuples of (DocumentChunk, rank_score).
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        dialect_name = self.db.bind.dialect.name if self.db.bind else "postgresql"

        if dialect_name == "postgresql":
            # PostgreSQL full-text search using plainto_tsquery
            ts_query = func.plainto_tsquery("english", clean_query)
            # Use ts_vector column if present, or generate on the fly
            ts_vec_expr = func.coalesce(
                DocumentChunk.ts_vector,
                func.to_tsvector("english", DocumentChunk.content)
            )
            rank_col = func.ts_rank_cd(ts_vec_expr, ts_query).label("rank")

            stmt = (
                select(DocumentChunk, rank_col)
                .options(joinedload(DocumentChunk.document))
                .where(ts_vec_expr.op("@@")(ts_query))
            )

            if service_id is not None:
                stmt = stmt.join(Document, DocumentChunk.document_id == Document.id).where(
                    Document.associated_service_id == service_id
                )

            stmt = stmt.order_by(text("rank DESC")).limit(top_k)
            rows = self.db.execute(stmt).all()

            results: List[Tuple[DocumentChunk, float]] = []
            for chunk, rank in rows:
                results.append((chunk, round(float(rank), 4)))

            return results
        else:
            # Fallback for non-Postgres environments (e.g. SQLite unit tests)
            stmt = select(DocumentChunk).options(joinedload(DocumentChunk.document))
            if service_id is not None:
                stmt = stmt.join(Document, DocumentChunk.document_id == Document.id).where(
                    Document.associated_service_id == service_id
                )
            all_chunks = list(self.db.scalars(stmt).all())

            terms = clean_query.lower().split()
            scored = []
            for chunk in all_chunks:
                content_lower = chunk.content.lower()
                matches = sum(1 for term in terms if term in content_lower)
                if matches > 0:
                    score = matches / len(terms)
                    scored.append((chunk, round(score, 4)))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
