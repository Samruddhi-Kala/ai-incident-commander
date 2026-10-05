from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.rag.service import RAGService
from app.rag.schemas import (
    RAGSearchRequest,
    RAGIngestRequest,
    RetrievalResponse,
    IngestionSummary,
)

router = APIRouter()


@router.post(
    "/search",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the knowledge base using vector, text, or hybrid retrieval",
)
def search_knowledge_base(
    request: RAGSearchRequest,
    db: Session = Depends(get_db),
):
    rag_svc = RAGService(db)
    results = rag_svc.search(
        query=request.query,
        top_k=request.top_k,
        mode=request.mode,
        service_id=request.service_id,
    )
    return RetrievalResponse(
        query=request.query,
        mode=request.mode,
        total_results=len(results),
        results=results,
    )


@router.post(
    "/ingest",
    response_model=IngestionSummary,
    status_code=status.HTTP_200_OK,
    summary="Trigger document ingestion from the knowledge base directory",
)
def ingest_knowledge_base(
    request: RAGIngestRequest,
    db: Session = Depends(get_db),
):
    rag_svc = RAGService(db)
    summary = rag_svc.ingest_directory(
        dir_path=request.directory_path,
        force=request.force,
    )
    return summary
