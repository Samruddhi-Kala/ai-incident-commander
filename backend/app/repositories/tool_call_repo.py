import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.tool_call import ToolCall
from app.repositories.base import BaseRepository


class ToolCallRepository(BaseRepository[ToolCall]):
    """
    Repository for persisting and querying diagnostic and remediation tool call executions.
    """
    def __init__(self, db: Session):
        super().__init__(ToolCall, db)

    def list_by_investigation(self, investigation_id: uuid.UUID) -> List[ToolCall]:
        """
        List all tool calls associated with a specific investigation.
        """
        statement = (
            select(ToolCall)
            .where(ToolCall.investigation_id == investigation_id)
            .order_by(ToolCall.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_by_tool_name(self, tool_name: str, limit: int = 50) -> List[ToolCall]:
        """
        List recent tool calls for a given tool name.
        """
        statement = (
            select(ToolCall)
            .where(ToolCall.tool_name == tool_name)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
