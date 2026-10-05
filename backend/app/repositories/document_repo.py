import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: Session):
        super().__init__(Document, db)

    def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """
        Get document by SHA-256 content hash for deduplication.
        """
        statement = select(Document).where(Document.content_hash == content_hash)
        return self.db.scalars(statement).first()

    def get_by_file_path(self, file_path: str) -> Optional[Document]:
        """
        Get document by source file path.
        """
        statement = select(Document).where(Document.file_path == file_path)
        return self.db.scalars(statement).first()

    def list_by_category(self, category: str) -> List[Document]:
        """
        List documents by category (runbook, architecture, incident, policy).
        """
        statement = select(Document).where(Document.category == category)
        return list(self.db.scalars(statement).all())
