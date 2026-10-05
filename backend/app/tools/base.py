"""
Base Tool Adapter

Provides the abstract base class for all engineering tool adapters.
Each adapter must implement tool methods that return standardized ToolResult objects.
The base class provides latency tracking, structured error handling, and
consistent JSON output formatting.
"""
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.logging import logger


class ToolResult(BaseModel):
    """
    Standardized result container for all tool adapter invocations.
    Captures tool name, arguments, output, status, and execution latency
    for audit trail and evidence collection purposes.
    """
    tool_name: str = Field(..., description="Name of the tool that was invoked")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    result: Dict[str, Any] = Field(default_factory=dict, description="Tool output payload")
    status: str = Field(default="Success", description="Execution status: Success, Error, Timeout")
    execution_time_ms: int = Field(default=0, description="Execution duration in milliseconds")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO-8601 UTC timestamp of execution",
    )

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


class BaseToolAdapter(ABC):
    """
    Abstract base class for all engineering tool adapters.

    Subclasses implement domain-specific tool methods. The base class provides:
    - Standardized ToolResult wrapping with latency measurement
    - Structured error handling that returns Error status instead of raising
    - Consistent logging for audit trail purposes
    """

    @property
    @abstractmethod
    def domain(self) -> str:
        """Return the tool domain name (e.g., 'observability', 'deployment')."""
        ...

    @property
    @abstractmethod
    def tools(self) -> List[str]:
        """Return list of tool names provided by this adapter."""
        ...

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Dispatches a tool call to the appropriate adapter method.
        Wraps execution with latency tracking and error handling.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: Dictionary of arguments to pass to the tool.

        Returns:
            ToolResult with status, output payload, and latency.
        """
        if tool_name not in self.tools:
            logger.error(f"Tool '{tool_name}' not found in {self.domain} adapter")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": f"Tool '{tool_name}' is not available in the {self.domain} adapter"},
                status="Error",
                execution_time_ms=0,
            )

        method = getattr(self, tool_name, None)
        if method is None or not callable(method):
            logger.error(f"Method '{tool_name}' not implemented in {self.domain} adapter")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": f"Method '{tool_name}' not implemented"},
                status="Error",
                execution_time_ms=0,
            )

        start_time = time.perf_counter()
        try:
            logger.info(f"Executing tool '{tool_name}' in {self.domain} adapter with args: {arguments}")
            output = method(**arguments)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Tool '{tool_name}' completed in {elapsed_ms}ms")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result=output,
                status="Success",
                execution_time_ms=elapsed_ms,
            )
        except TypeError as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Tool '{tool_name}' argument validation failed: {e}")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": f"Invalid arguments: {str(e)}"},
                status="Error",
                execution_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Tool '{tool_name}' execution failed: {e}")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": str(e)},
                status="Error",
                execution_time_ms=elapsed_ms,
            )
