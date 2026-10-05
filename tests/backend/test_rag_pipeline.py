import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.rag.ingestion.pipeline import IngestionPipeline
from app.rag.service import RAGService
from app.rag.schemas import LoadedDocument, RetrievalResult
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def test_pipeline_ingest_single_document():
    """
    Test IngestionPipeline loads, cleans, chunks, embeds, and saves a new document.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "test-runbook.md"
        doc_path.write_text("# Test Runbook\n\nDiagnostic steps for test.", encoding="utf-8")

        mock_db = MagicMock(spec=Session)

        pipeline = IngestionPipeline(db=mock_db)
        # Mock document_repo get_by_file_path to return None (new doc)
        pipeline.document_repo.get_by_file_path = MagicMock(return_value=None)
        pipeline.document_repo.create = MagicMock(side_effect=lambda d: d)
        pipeline.chunk_repo.create_chunks = MagicMock(side_effect=lambda c: c)

        result = pipeline.ingest_document(doc_path)

        assert result.status == "created"
        assert result.title == "Test Runbook"
        assert result.chunks_count >= 1
        assert result.error is None
        mock_db.commit.assert_called_once()


def test_pipeline_idempotency_skip():
    """
    Test IngestionPipeline skips unchanged documents when content hash matches.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "stable-runbook.md"
        content = "# Stable Runbook\n\nNo changes here."
        doc_path.write_text(content, encoding="utf-8")

        mock_db = MagicMock(spec=Session)
        pipeline = IngestionPipeline(db=mock_db)

        # Mock existing document with same content hash
        clean_content = pipeline.cleaner.clean(content)
        content_hash = pipeline.loader.compute_hash(clean_content)

        existing_doc = Document(
            id=uuid.uuid4(),
            title="Stable Runbook",
            category="general",
            file_path=str(doc_path),
            content_hash=content_hash,
        )
        existing_doc.chunks = [DocumentChunk(id=uuid.uuid4(), chunk_index=0, content="chunk", embedding=[0.0]*1536)]
        pipeline.document_repo.get_by_file_path = MagicMock(return_value=existing_doc)
        pipeline.chunk_repo.create_chunks = MagicMock()

        result = pipeline.ingest_document(doc_path, force=False)

        assert result.status == "skipped"
        assert result.chunks_count == 1
        # Should not create chunks or commit
        pipeline.chunk_repo.create_chunks.assert_not_called()


def test_pipeline_force_reingest():
    """
    Test IngestionPipeline re-chunks and updates document when force=True.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "force-runbook.md"
        content = "# Force Runbook\n\nContent to reingest."
        doc_path.write_text(content, encoding="utf-8")

        mock_db = MagicMock(spec=Session)
        pipeline = IngestionPipeline(db=mock_db)

        clean_content = pipeline.cleaner.clean(content)
        content_hash = pipeline.loader.compute_hash(clean_content)

        existing_doc = Document(
            id=uuid.uuid4(),
            title="Force Runbook",
            category="general",
            file_path=str(doc_path),
            content_hash=content_hash,
        )
        pipeline.document_repo.get_by_file_path = MagicMock(return_value=existing_doc)
        pipeline.chunk_repo.delete_by_document_id = MagicMock(return_value=1)
        pipeline.chunk_repo.create_chunks = MagicMock(side_effect=lambda c: c)

        result = pipeline.ingest_document(doc_path, force=True)

        assert result.status == "updated"
        pipeline.chunk_repo.delete_by_document_id.assert_called_once_with(existing_doc.id)
        mock_db.commit.assert_called_once()


def test_pipeline_rollback_on_failure():
    """
    Test transaction rollback when embedding generation or DB write fails.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "error-doc.md"
        doc_path.write_text("# Error Doc\n\nThis will trigger an error.", encoding="utf-8")

        mock_db = MagicMock(spec=Session)
        pipeline = IngestionPipeline(db=mock_db)
        pipeline.document_repo.get_by_file_path = MagicMock(return_value=None)
        # Simulate embedding service failure
        pipeline.embedding_service.embed_texts = MagicMock(side_effect=RuntimeError("Simulated embedding error"))

        result = pipeline.ingest_document(doc_path)

        assert result.status == "failed"
        assert "Simulated embedding error" in (result.error or "")
        mock_db.rollback.assert_called_once()


def test_rag_service_retrieve_context():
    """
    Test RAGService facade returns formatted context block.
    """
    mock_db = MagicMock(spec=Session)
    rag_svc = RAGService(db=mock_db)

    # Mock search
    fake_results = [
        RetrievalResult(
            chunk_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            content="Check payment gateway timeout.",
            source_path="knowledge_base/runbooks/payment-service.md",
            document_type="runbook",
            title="Payment Service Runbook",
            section_title="Diagnostic Steps",
            score=0.95,
            chunk_index=0,
        )
    ]
    rag_svc.retriever.search = MagicMock(return_value=fake_results)

    context = rag_svc.retrieve_context("payment timeout", mode="vector")

    assert "SOURCE: knowledge_base/runbooks/payment-service.md" in context
    assert "Check payment gateway timeout." in context
