"""
Tool Execution Service

Coordinates tool execution, database persistence, and audit logging.
Ensures every diagnostic tool invocation is recorded in `tool_calls`
and audited in `audit_logs` transactionally.
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.tool_call import ToolCall
from app.models.audit_log import AuditLog
from app.models.investigation import Investigation
from app.repositories.tool_call_repo import ToolCallRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.tools.base import ToolResult
from app.tools.registry import tool_registry, ToolRegistry
from app.core.logging import logger


class ToolService:
    """
    Service coordinating tool execution dispatch and transactional persistence.
    """

    def __init__(self, db: Session, registry: Optional[ToolRegistry] = None):
        self.db = db
        self.tool_call_repo = ToolCallRepository(db)
        self.audit_log_repo = AuditLogRepository(db)
        self.registry = registry or tool_registry

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        investigation_id: Optional[uuid.UUID] = None,
    ) -> Tuple[ToolResult, ToolCall]:
        """
        Executes a diagnostic tool and persists the execution and audit trail.

        1. Dispatches execution via ToolRegistry (calculates latency, captures errors).
        2. Persists the result into the `tool_calls` table.
        3. Records a structured audit event in the `audit_logs` table.
        4. Commits transaction and returns the ToolResult and persisted ToolCall entity.
        """
        # 1. Execute tool via pure registry
        result = self.registry.execute(tool_name=tool_name, arguments=arguments)

        # 2. Persist tool call record
        tool_call_id = uuid.uuid4()
        tool_call = ToolCall(
            id=tool_call_id,
            investigation_id=investigation_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result.result,
            status=result.status,
            execution_time_ms=result.execution_time_ms,
        )
        self.db.add(tool_call)
        self.db.flush()

        # 3. Lookup incident_id if investigation_id is provided
        incident_id = None
        if investigation_id:
            inv = self.db.get(Investigation, investigation_id)
            if inv:
                incident_id = inv.incident_id

        # 4. Record audit log
        audit_payload = {
            "tool_name": tool_name,
            "tool_call_id": str(tool_call.id),
            "investigation_id": str(investigation_id) if investigation_id else None,
            "status": result.status,
            "execution_time_ms": result.execution_time_ms,
            "arguments": arguments,
        }
        if result.status == "Error":
            audit_payload["error"] = result.result.get("error", "Unknown error")

        audit_log = AuditLog(
            incident_id=incident_id,
            actor_type="SYSTEM_AGENT",
            action_type="tool.execute",
            payload=audit_payload,
        )
        self.db.add(audit_log)

        # 5. Commit transactionally
        self.db.commit()
        self.db.refresh(tool_call)

        logger.info(
            f"Persisted tool_call {tool_call.id} ({tool_name}, status={result.status}, "
            f"latency={result.execution_time_ms}ms, investigation={investigation_id})"
        )

        return result, tool_call

    def execute_batch(
        self,
        tools: List[Dict[str, Any]],
        default_investigation_id: Optional[uuid.UUID] = None,
    ) -> List[Tuple[ToolResult, ToolCall]]:
        """
        Executes a sequence of tool calls, persisting each execution individually.
        """
        results = []
        for item in tools:
            tool_name = item.get("tool_name")
            arguments = item.get("arguments", {})
            item_inv_id = item.get("investigation_id") or default_investigation_id

            res, call = self.execute_tool(
                tool_name=tool_name,
                arguments=arguments,
                investigation_id=item_inv_id,
            )
            results.append((res, call))

        return results
