import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class LoadedDocument(BaseModel):
    """
    Normalized in-memory representation of a loaded document before chunking.
    """
    title: str = Field(..., description="Document title extracted from header or filename")
    category: str = Field(..., description="Category inferred from directory (runbook, architecture, incident, policy)")
    file_path: str = Field(..., description="Relative or absolute file path to the source document")
    filename: str = Field(..., description="Source filename")
    content: str = Field(..., description="Cleaned or raw Markdown document content")
    content_hash: str = Field(..., description="SHA-256 hash of the content for deduplication")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional document-level metadata")
    associated_service_id: Optional[uuid.UUID] = Field(None, description="Linked service UUID if identified")


class ChunkMetadata(BaseModel):
    """
    Structured metadata stored inside each DocumentChunk JSONB column.
    """
    source_path: str
    document_type: str
    title: str
    chunk_index: int
    section_title: Optional[str] = None
    token_count: int
    character_count: int
    service_hint: Optional[str] = None


class DocumentChunkCreate(BaseModel):
    """
    Internal schema for creating a document chunk record with vector embedding.
    """
    document_id: uuid.UUID
    chunk_index: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: List[float]


class RetrievalResult(BaseModel):
    """
    Standardized result item returned by vector, text, or hybrid retrieval.
    """
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    source_path: str
    document_type: str
    title: str
    section_title: Optional[str] = None
    score: float = Field(..., description="Similarity or rank score (higher is more relevant)")
    chunk_index: int

    model_config = ConfigDict(from_attributes=True)


class RetrievalResponse(BaseModel):
    """
    Top-level response envelope for retrieval queries.
    """
    query: str
    mode: str
    total_results: int
    results: List[RetrievalResult]


class IngestionResult(BaseModel):
    """
    Result for a single ingested document file.
    """
    file_path: str
    title: str
    category: str
    status: str = Field(..., description="created | updated | skipped | failed")
    chunks_count: int = 0
    error: Optional[str] = None


class IngestionSummary(BaseModel):
    """
    Aggregate summary report after ingesting a directory of documents.
    """
    discovered_count: int
    processed_count: int
    skipped_count: int
    failed_count: int
    total_chunks: int
    details: List[IngestionResult] = Field(default_factory=list)


class RAGSearchRequest(BaseModel):
    """
    Request schema for knowledge retrieval API.
    """
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of relevant chunks to retrieve")
    mode: str = Field("vector", description="Retrieval mode: 'vector', 'text', or 'hybrid'")
    service_id: Optional[uuid.UUID] = Field(None, description="Optional service ID to filter results")


class RAGIngestRequest(BaseModel):
    """
    Request schema for triggering knowledge base ingestion.
    """
    directory_path: Optional[str] = Field(None, description="Directory path to ingest (defaults to configured KNOWLEDGE_BASE_DIR)")
    force: bool = Field(False, description="If true, re-ingest and overwrite documents even if content hash matches")
