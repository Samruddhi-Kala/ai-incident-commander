import uuid
from typing import List, Optional
from app.repositories.document_chunk_repo import DocumentChunkRepository
from app.rag.schemas import RetrievalResult


class FullTextSearcher:
    """
    Executes sparse full-text keyword queries using PostgreSQL text search.
    """

    def __init__(self, chunk_repo: DocumentChunkRepository):
        self.chunk_repo = chunk_repo

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_id: Optional[uuid.UUID] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieves top_k chunks matching text query based on keyword relevance.
        """
        rows = self.chunk_repo.search_by_text(
            query=query,
            top_k=top_k,
            service_id=service_id,
        )

        results: List[RetrievalResult] = []
        for chunk, score in rows:
            meta = chunk.chunk_metadata or {}
            source_path = meta.get("source_path") or (chunk.document.file_path if chunk.document else "")
            doc_type = meta.get("document_type") or (chunk.document.category if chunk.document else "general")
            title = meta.get("title") or (chunk.document.title if chunk.document else "")
            section_title = meta.get("section_title")

            results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    source_path=source_path,
                    document_type=doc_type,
                    title=title,
                    section_title=section_title,
                    score=score,
                    chunk_index=chunk.chunk_index,
                )
            )

        return results
