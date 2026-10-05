"""
Agent Configuration

Exposes agent-specific configuration parameters derived from centralized app settings.
"""
from app.core.config import settings

# Agent orchestration defaults
AGENT_MAX_ITERATIONS: int = settings.AGENT_MAX_ITERATIONS
AGENT_MAX_TOOL_CALLS: int = settings.AGENT_MAX_TOOL_CALLS
LLM_PROVIDER: str = settings.LLM_PROVIDER
LLM_MODEL: str = settings.LLM_MODEL
LLM_API_KEY: str | None = settings.LLM_API_KEY
