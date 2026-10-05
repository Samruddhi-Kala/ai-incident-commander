"""
Pydantic Schemas for Tool Adapter API

Request and response models for the engineering tools REST endpoints.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class ToolExecuteRequest(BaseModel):
    """Request body for executing a single tool."""
    tool_name: str = Field(..., description="Name of the tool to execute (e.g., 'get_metrics', 'search_logs')")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")
    investigation_id: Optional[uuid.UUID] = Field(default=None, description="Optional investigation ID to associate the tool execution with")


class ToolBatchExecuteRequest(BaseModel):
    """Request body for executing multiple tools in sequence."""
    tools: List[ToolExecuteRequest] = Field(..., min_length=1, max_length=10, description="List of tool calls to execute")
    investigation_id: Optional[uuid.UUID] = Field(default=None, description="Optional default investigation ID for all tool calls in the batch")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class ToolResultResponse(BaseModel):
    """Response model for a single tool execution result."""
    tool_name: str = Field(..., description="Name of the tool that was invoked")
    domain: Optional[str] = Field(None, description="Domain of the tool adapter")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments that were passed to the tool")
    result: Dict[str, Any] = Field(default_factory=dict, description="Tool output payload")
    status: str = Field(..., description="Execution status: Success, Error, Timeout")
    execution_time_ms: int = Field(..., description="Execution duration in milliseconds")
    timestamp: datetime = Field(..., description="ISO-8601 UTC timestamp of execution")
    investigation_id: Optional[uuid.UUID] = Field(None, description="Associated investigation ID if provided")
    tool_call_id: Optional[uuid.UUID] = Field(None, description="Primary key UUID of the persisted tool_call row in the database")


class ToolBatchResultResponse(BaseModel):
    """Response model for batch tool execution."""
    total_tools: int = Field(..., description="Number of tools executed")
    total_execution_time_ms: int = Field(..., description="Total execution time for all tools")
    results: List[ToolResultResponse] = Field(..., description="Ordered list of tool execution results")


class ToolInfoResponse(BaseModel):
    """Response model for tool discovery."""
    tool_name: str = Field(..., description="Tool name")
    domain: str = Field(..., description="Tool adapter domain")
    description: str = Field(..., description="Tool description")


class ToolListResponse(BaseModel):
    """Response model for listing all available tools."""
    total_tools: int = Field(..., description="Total number of registered tools")
    domains: List[str] = Field(..., description="Available tool domains")
    tools: List[ToolInfoResponse] = Field(..., description="List of all available tools")


class ToolSchemaResponse(BaseModel):
    """Response model for tool schemas (for LLM function calling)."""
    total_tools: int = Field(..., description="Total number of tool schemas")
    schemas: List[Dict[str, Any]] = Field(..., description="Tool schemas for LLM consumption")
