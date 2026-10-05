"""
Engineering Tool Adapters Package

Provides a standardized tool calling interface for system queries across
five diagnostic domains: Observability, Deployment, Git, Incident History,
and Infrastructure. All V1 adapters return deterministic simulated data
for reproducible local development and testing.
"""
from app.tools.base import BaseToolAdapter, ToolResult
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.observability import ObservabilityAdapter
from app.tools.deployment import DeploymentAdapter
from app.tools.git import GitAdapter
from app.tools.incident_history import IncidentHistoryAdapter
from app.tools.infrastructure import InfrastructureAdapter

__all__ = [
    "BaseToolAdapter",
    "ToolResult",
    "ToolRegistry",
    "tool_registry",
    "ObservabilityAdapter",
    "DeploymentAdapter",
    "GitAdapter",
    "IncidentHistoryAdapter",
    "InfrastructureAdapter",
]
