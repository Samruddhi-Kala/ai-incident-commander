import uuid
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from app.rag.schemas import (
    RetrievalResult,
    IngestionResult,
    IngestionSummary,
)
from app.rag.embeddings.service import EmbeddingService
from app.rag.ingestion.pipeline import IngestionPipeline
from app.rag.retrieval.vector_search import VectorSearcher
from app.rag.retrieval.full_text_search import FullTextSearcher
from app.rag.retrieval.retriever import KnowledgeRetriever
from app.rag.context.builder import ContextBuilder
from app.repositories.document_chunk_repo import DocumentChunkRepository
from app.core.config import settings
from app.core.logging import logger


class RAGService:
    """
    Top-level RAG facade providing a clean, cohesive interface for both
    document ingestion and multi-modal knowledge retrieval.
    Hides internal chunking, vector, and SQL query mechanics from downstream agents.
    """

    def __init__(
        self,
        db: Session,
        embedding_service: Optional[EmbeddingService] = None,
        retriever: Optional[KnowledgeRetriever] = None,
        context_builder: Optional[ContextBuilder] = None,
        pipeline: Optional[IngestionPipeline] = None,
    ):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        self.chunk_repo = DocumentChunkRepository(db)

        if retriever:
            self.retriever = retriever
        else:
            vector_searcher = VectorSearcher(self.chunk_repo)
            text_searcher = FullTextSearcher(self.chunk_repo)
            self.retriever = KnowledgeRetriever(
                embedding_service=self.embedding_service,
                vector_searcher=vector_searcher,
                text_searcher=text_searcher,
            )

        self.context_builder = context_builder or ContextBuilder()
        self.pipeline = pipeline or IngestionPipeline(
            db=db,
            embedding_service=self.embedding_service,
        )

    def ingest_directory(
        self,
        dir_path: Optional[str] = None,
        force: bool = False,
    ) -> IngestionSummary:
        """
        Discovers and ingests all Markdown files from the knowledge base directory.
        """
        target_dir = dir_path or settings.KNOWLEDGE_BASE_DIR

        # If relative, resolve relative to project root (2 levels up from app)
        path = Path(target_dir)
        if not path.is_absolute():
            # Try workspace root
            root_candidate = Path(__file__).resolve().parent.parent.parent.parent / target_dir
            if root_candidate.is_dir():
                path = root_candidate

        logger.info(f"RAGService initiating directory ingestion from: '{path}'")
        return self.pipeline.ingest_directory(directory_path=path, force=force)

    def ingest_file(
        self,
        file_path: str,
        force: bool = False,
    ) -> IngestionResult:
        """
        Ingests a specific Markdown document file into the knowledge base.
        """
        return self.pipeline.ingest_document(file_path=file_path, force=force)

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "vector",
        service_id: Optional[uuid.UUID] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieves relevant document chunks using vector, text, or hybrid retrieval.
        """
        return self.retriever.search(
            query=query,
            top_k=top_k,
            mode=mode,
            service_id=service_id,
        )

    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "vector",
        service_id: Optional[uuid.UUID] = None,
    ) -> str:
        """
        Retrieves relevant document chunks and returns a formatted context block
        complete with source citations, ready for LLM prompt assembly.
        """
        results = self.search(
            query=query,
            top_k=top_k,
            mode=mode,
            service_id=service_id,
        )
        return self.context_builder.build(results)
