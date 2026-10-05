"""
Engineering Tools API Routes

REST endpoints for tool discovery, execution, and schema generation.
These endpoints expose the simulated engineering tool adapters to the
API layer for both direct invocation and agent-driven investigation workflows.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.tool_service import ToolService
from app.tools.registry import tool_registry
from app.tools.schemas import (
    ToolExecuteRequest,
    ToolBatchExecuteRequest,
    ToolResultResponse,
    ToolBatchResultResponse,
    ToolListResponse,
    ToolInfoResponse,
    ToolSchemaResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ToolListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all available engineering tools",
)
def list_tools():
    """
    Returns a catalog of all registered engineering tools organized by domain.
    Useful for discovering available diagnostic capabilities.
    """
    tools = tool_registry.list_tools()
    domains = tool_registry.list_domains()
    return ToolListResponse(
        total_tools=len(tools),
        domains=domains,
        tools=[
            ToolInfoResponse(
                tool_name=t["tool_name"],
                domain=t["domain"],
                description=t["description"],
            )
            for t in tools
        ],
    )


@router.get(
    "/schemas",
    response_model=ToolSchemaResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tool schemas for LLM function calling",
)
def get_tool_schemas():
    """
    Returns tool schemas with parameter specifications suitable for
    LLM function calling interfaces (OpenAI, Anthropic, etc.).
    """
    schemas = tool_registry.get_tool_schemas()
    return ToolSchemaResponse(
        total_tools=len(schemas),
        schemas=schemas,
    )


@router.post(
    "/execute",
    response_model=ToolResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a single engineering tool",
)
def execute_tool(
    request: ToolExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a single engineering tool by name with the provided arguments.
    Persists execution record to `tool_calls` table and logs audit event to `audit_logs`.
    Returns structured result with status, output payload, and execution latency.
    """
    service = ToolService(db)
    result, tool_call = service.execute_tool(
        tool_name=request.tool_name,
        arguments=request.arguments,
        investigation_id=request.investigation_id,
    )
    domain = tool_registry.get_tool_domain(request.tool_name)
    return ToolResultResponse(
        tool_name=result.tool_name,
        domain=domain,
        arguments=result.arguments,
        result=result.result,
        status=result.status,
        execution_time_ms=result.execution_time_ms,
        timestamp=result.timestamp,
        investigation_id=tool_call.investigation_id,
        tool_call_id=tool_call.id,
    )


@router.post(
    "/execute/batch",
    response_model=ToolBatchResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multiple engineering tools in sequence",
)
def execute_tools_batch(
    request: ToolBatchExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Execute multiple engineering tools sequentially.
    Persists each execution individually to `tool_calls` and `audit_logs`.
    Returns ordered results with individual and total execution times.
    """
    service = ToolService(db)
    batch_items = [
        {
            "tool_name": item.tool_name,
            "arguments": item.arguments,
            "investigation_id": item.investigation_id,
        }
        for item in request.tools
    ]
    results = service.execute_batch(
        tools=batch_items,
        default_investigation_id=request.investigation_id,
    )

    response_items = []
    total_time = 0
    for res, call in results:
        domain = tool_registry.get_tool_domain(res.tool_name)
        total_time += res.execution_time_ms
        response_items.append(
            ToolResultResponse(
                tool_name=res.tool_name,
                domain=domain,
                arguments=res.arguments,
                result=res.result,
                status=res.status,
                execution_time_ms=res.execution_time_ms,
                timestamp=res.timestamp,
                investigation_id=call.investigation_id,
                tool_call_id=call.id,
            )
        )

    return ToolBatchResultResponse(
        total_tools=len(response_items),
        total_execution_time_ms=total_time,
        results=response_items,
    )
