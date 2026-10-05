import os
import sys
import argparse
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.rag.service import RAGService
from app.core.config import settings
from app.core.logging import setup_logging, logger


def run_ingest(directory: str | None = None, force: bool = False) -> None:
    """
    Executes knowledge base ingestion from the command line.
    """
    setup_logging()

    db = SessionLocal()
    try:
        rag_svc = RAGService(db)
        print("\n" + "=" * 65)
        print("  AI INCIDENT COMMANDER — KNOWLEDGE BASE INGESTION")
        print("=" * 65)

        target_dir = directory or settings.KNOWLEDGE_BASE_DIR
        print(f"Target directory   : {target_dir}")
        print(f"Force re-ingest    : {force}")
        print(f"Embedding provider : {settings.EMBEDDING_PROVIDER} ({settings.EMBEDDING_DIMENSION} dims)")
        print(f"Chunk size/overlap : {settings.RAG_CHUNK_SIZE} / {settings.RAG_CHUNK_OVERLAP}")
        print("-" * 65)

        summary = rag_svc.ingest_directory(dir_path=target_dir, force=force)

        print("\nIngestion Results:")
        print(f"  • Documents discovered : {summary.discovered_count}")
        print(f"  • Documents processed  : {summary.processed_count}")
        print(f"  • Documents skipped    : {summary.skipped_count}")
        print(f"  • Documents failed     : {summary.failed_count}")
        print(f"  • Total chunks stored  : {summary.total_chunks}")
        print("-" * 65)

        print("Document Breakdown:")
        for doc in summary.details:
            status_icon = "✓" if doc.status in ("created", "updated", "skipped") else "✗"
            print(f"  [{status_icon}] {doc.title:<35} | {doc.category:<12} | {doc.status:<8} | {doc.chunks_count} chunks")
            if doc.error:
                print(f"      Error: {doc.error}")

        print("=" * 65 + "\n")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest Markdown knowledge base into PostgreSQL + pgvector.")
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Custom directory path containing Markdown files (defaults to settings.KNOWLEDGE_BASE_DIR).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of documents even if content hash is unchanged.",
    )
    args = parser.parse_args()
    run_ingest(directory=args.dir, force=args.force)


if __name__ == "__main__":
    main()
