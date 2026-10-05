import os
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from app.rag.schemas import LoadedDocument, IngestionResult, IngestionSummary
from app.rag.loaders.markdown_loader import MarkdownLoader
from app.rag.processing.cleaner import TextCleaner
from app.rag.processing.chunker import HeadingChunker
from app.rag.processing.metadata import extract_service_hint
from app.rag.embeddings.service import EmbeddingService
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories.document_repo import DocumentRepository
from app.repositories.document_chunk_repo import DocumentChunkRepository
from app.repositories.service_repo import ServiceRepository
from app.core.config import settings
from app.core.logging import logger


class IngestionPipeline:
    """
    Orchestrates the end-to-end document ingestion workflow:
    Discovery -> Parsing -> Cleaning -> Chunking -> Embedding -> Database Persistence.
    """

    def __init__(
        self,
        db: Session,
        loader: Optional[MarkdownLoader] = None,
        cleaner: Optional[TextCleaner] = None,
        chunker: Optional[HeadingChunker] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.db = db
        self.loader = loader or MarkdownLoader()
        self.cleaner = cleaner or TextCleaner()
        self.chunker = chunker or HeadingChunker()
        self.embedding_service = embedding_service or EmbeddingService()

        self.document_repo = DocumentRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        self.service_repo = ServiceRepository(db)

    def ingest_document(self, file_path: str | Path, force: bool = False) -> IngestionResult:
        """
        Ingests a single Markdown document into PostgreSQL + pgvector.
        Idempotent: skips if content hash matches and force is False.
        """
        path = Path(file_path).resolve()
        try:
            # 1. Load document
            raw_doc = self.loader.load_file(path)

            # 2. Clean text content
            cleaned_content = self.cleaner.clean(raw_doc.content)
            content_hash = self.loader.compute_hash(cleaned_content)

            # 3. Check for existing document in database by file path
            existing_doc = self.document_repo.get_by_file_path(raw_doc.file_path)

            if existing_doc and not force:
                if existing_doc.content_hash == content_hash:
                    logger.info(
                        f"Skipping document '{raw_doc.title}' ({raw_doc.file_path}): content hash unchanged."
                    )
                    return IngestionResult(
                        file_path=raw_doc.file_path,
                        title=raw_doc.title,
                        category=raw_doc.category,
                        status="skipped",
                        chunks_count=len(existing_doc.chunks) if existing_doc.chunks else 0,
                    )

            # 4. Check for associated service in catalog
            associated_service_id = None
            service_hint = extract_service_hint(cleaned_content, raw_doc.file_path)
            if service_hint:
                svc = self.service_repo.get_by_name(service_hint)
                if svc:
                    associated_service_id = svc.id
                    logger.debug(f"Linked document '{raw_doc.file_path}' to service '{svc.name}'")

            # 5. Split into heading-aware chunks
            doc_to_chunk = LoadedDocument(
                title=raw_doc.title,
                category=raw_doc.category,
                file_path=raw_doc.file_path,
                filename=raw_doc.filename,
                content=cleaned_content,
                content_hash=content_hash,
                associated_service_id=associated_service_id,
            )
            chunks_data = self.chunker.chunk(doc_to_chunk)

            if not chunks_data:
                logger.warning(f"No chunks extracted from '{raw_doc.file_path}'.")
                return IngestionResult(
                    file_path=raw_doc.file_path,
                    title=raw_doc.title,
                    category=raw_doc.category,
                    status="skipped",
                    chunks_count=0,
                )

            # 6. Generate vector embeddings for all chunks
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = self.embedding_service.embed_texts(chunk_texts)

            # 7. Persist Document and DocumentChunks atomically
            if existing_doc:
                # Remove existing chunks for clean replacement
                self.chunk_repo.delete_by_document_id(existing_doc.id)
                existing_doc.title = raw_doc.title
                existing_doc.category = raw_doc.category
                existing_doc.content_hash = content_hash
                if associated_service_id:
                    existing_doc.associated_service_id = associated_service_id
                doc_record = existing_doc
                status = "updated"
            else:
                new_doc = Document(
                    title=raw_doc.title,
                    category=raw_doc.category,
                    file_path=raw_doc.file_path,
                    content_hash=content_hash,
                    associated_service_id=associated_service_id,
                )
                self.db.add(new_doc)
                self.db.flush()
                doc_record = new_doc
                status = "created"

            chunk_records = [
                DocumentChunk(
                    document_id=doc_record.id,
                    chunk_index=chunk_dict["chunk_index"],
                    content=chunk_dict["content"],
                    chunk_metadata=chunk_dict["metadata"],
                    embedding=emb,
                )
                for chunk_dict, emb in zip(chunks_data, embeddings)
            ]

            self.chunk_repo.create_chunks(chunk_records)
            self.db.commit()

            logger.info(
                f"Successfully {status} document '{raw_doc.title}' with {len(chunk_records)} chunks."
            )
            return IngestionResult(
                file_path=raw_doc.file_path,
                title=raw_doc.title,
                category=raw_doc.category,
                status=status,
                chunks_count=len(chunk_records),
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during ingestion of '{file_path}': {str(e)}")
            return IngestionResult(
                file_path=str(file_path),
                title=path.stem,
                category="general",
                status="failed",
                chunks_count=0,
                error=str(e),
            )

    def ingest_directory(self, directory_path: str | Path, force: bool = False) -> IngestionSummary:
        """
        Recursively ingests all Markdown files found in the directory.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            logger.error(f"Target directory '{directory_path}' is not a directory.")
            return IngestionSummary(
                discovered_count=0,
                processed_count=0,
                skipped_count=0,
                failed_count=0,
                total_chunks=0,
                details=[],
            )

        md_files = sorted(dir_path.rglob("*.md"))
        valid_files = [f for f in md_files if not any(part.startswith(".") for part in f.parts)]

        discovered = len(valid_files)
        processed = 0
        skipped = 0
        failed = 0
        total_chunks = 0
        details: List[IngestionResult] = []

        logger.info(f"Starting ingestion of {discovered} Markdown file(s) from '{dir_path}'...")

        for file_path in valid_files:
            result = self.ingest_document(file_path, force=force)
            details.append(result)

            if result.status in ("created", "updated"):
                processed += 1
                total_chunks += result.chunks_count
            elif result.status == "skipped":
                skipped += 1
                total_chunks += result.chunks_count
            elif result.status == "failed":
                failed += 1

        summary = IngestionSummary(
            discovered_count=discovered,
            processed_count=processed,
            skipped_count=skipped,
            failed_count=failed,
            total_chunks=total_chunks,
            details=details,
        )

        logger.info(
            f"Ingestion complete: {processed} processed, {skipped} skipped, {failed} failed. "
            f"Total chunks: {total_chunks}"
        )
        return summary
