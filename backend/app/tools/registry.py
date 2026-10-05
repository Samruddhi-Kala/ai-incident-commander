"""
Tool Registry

Central registry that manages all available engineering tool adapters.
Provides tool discovery, execution dispatch, and schema generation
for the LangGraph agent to use during investigation workflows.
"""
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter, ToolResult
from app.tools.observability import ObservabilityAdapter
from app.tools.deployment import DeploymentAdapter
from app.tools.git import GitAdapter
from app.tools.incident_history import IncidentHistoryAdapter
from app.tools.infrastructure import InfrastructureAdapter
from app.core.logging import logger


class ToolRegistry:
    """
    Central registry managing all available engineering tool adapters.

    Provides:
    - Tool discovery: list all available tools and their domains
    - Execution dispatch: route tool calls to the correct adapter
    - Schema generation: provide tool signatures for LLM function calling
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseToolAdapter] = {}
        self._tool_to_domain: Dict[str, str] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all built-in V1 simulated adapters."""
        self.register_adapter(ObservabilityAdapter())
        self.register_adapter(DeploymentAdapter())
        self.register_adapter(GitAdapter())
        self.register_adapter(IncidentHistoryAdapter())
        self.register_adapter(InfrastructureAdapter())

    def register_adapter(self, adapter: BaseToolAdapter) -> None:
        """
        Register a tool adapter and index its tools by name.

        Args:
            adapter: A BaseToolAdapter subclass instance.
        """
        self._adapters[adapter.domain] = adapter
        for tool_name in adapter.tools:
            if tool_name in self._tool_to_domain:
                logger.warning(
                    f"Tool '{tool_name}' already registered under domain "
                    f"'{self._tool_to_domain[tool_name]}' — overwriting with '{adapter.domain}'"
                )
            self._tool_to_domain[tool_name] = adapter.domain
        logger.info(
            f"Registered {adapter.domain} adapter with tools: {adapter.tools}"
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their domain and available arguments.

        Returns:
            List of dicts describing each tool.
        """
        tools = []
        for domain, adapter in self._adapters.items():
            for tool_name in adapter.tools:
                method = getattr(adapter, tool_name, None)
                doc = method.__doc__ if method and method.__doc__ else "No description available."
                tools.append({
                    "tool_name": tool_name,
                    "domain": domain,
                    "description": doc.strip(),
                })
        return tools

    def list_domains(self) -> List[str]:
        """Return list of registered adapter domains."""
        return list(self._adapters.keys())

    def get_tools_by_domain(self, domain: str) -> List[str]:
        """
        Get tool names for a specific domain.

        Args:
            domain: The adapter domain name.

        Returns:
            List of tool names in that domain.
        """
        adapter = self._adapters.get(domain)
        if adapter:
            return adapter.tools
        return []

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool by name, routing to the correct adapter.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.

        Returns:
            ToolResult with status, output, and latency.
        """
        domain = self._tool_to_domain.get(tool_name)
        if domain is None:
            logger.error(f"Tool '{tool_name}' not found in registry")
            return ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result={"error": f"Tool '{tool_name}' is not registered in the tool registry"},
                status="Error",
                execution_time_ms=0,
            )

        adapter = self._adapters[domain]
        return adapter.execute(tool_name, arguments)

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered."""
        return tool_name in self._tool_to_domain

    def get_tool_domain(self, tool_name: str) -> Optional[str]:
        """Get the domain for a given tool name."""
        return self._tool_to_domain.get(tool_name)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Generate tool schemas suitable for LLM function calling interfaces.
        Each schema includes the tool name, description, domain, and
        parameter specifications extracted from method signatures.

        Returns:
            List of tool schema dicts for LLM consumption.
        """
        import inspect

        schemas = []
        for domain, adapter in self._adapters.items():
            for tool_name in adapter.tools:
                method = getattr(adapter, tool_name, None)
                if method is None:
                    continue

                sig = inspect.signature(method)
                params = {}
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue
                    param_info: Dict[str, Any] = {"type": "string"}
                    if param.annotation != inspect.Parameter.empty:
                        type_name = getattr(param.annotation, "__name__", str(param.annotation))
                        param_info["type"] = type_name
                    if param.default != inspect.Parameter.empty:
                        param_info["default"] = param.default
                        param_info["required"] = False
                    else:
                        param_info["required"] = True
                    params[param_name] = param_info

                doc = method.__doc__ if method.__doc__ else "No description."
                schemas.append({
                    "name": tool_name,
                    "domain": domain,
                    "description": doc.strip(),
                    "parameters": params,
                })

        return schemas


# Module-level singleton for convenient access
tool_registry = ToolRegistry()
