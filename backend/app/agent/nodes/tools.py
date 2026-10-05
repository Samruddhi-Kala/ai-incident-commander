"""
Tools Node

Selects, validates, and executes registered diagnostic engineering tools.
Ensures tool execution is audited and persisted to `tool_calls` and `audit_logs`
with the active investigation_id attached.
"""
import uuid
from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.core.config import settings
from app.core.logging import logger
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.services.tool_service import ToolService
from app.tools.registry import tool_registry


def _default_arguments_for_tool(tool_name: str, service_name: str) -> Dict[str, Any]:
    """Provides sensible contextual arguments for diagnostic tools."""
    svc = service_name or "payment-service"
    defaults = {
        "get_error_rate": {"service_name": svc, "minutes": 30},
        "get_latency": {"service_name": svc, "percentile": "p99", "minutes": 30},
        "get_service_health": {"service_name": svc},
        "get_recent_deployments": {"service_name": svc, "limit": 5},
        "get_recent_commits": {"service_name": svc, "limit": 5},
        "get_database_status": {"database_name": "payment-db"},
        "get_pod_status": {"service_name": svc},
        "get_service_dependencies": {"service_name": svc},
        "search_logs": {"service_name": svc, "query": "error", "limit": 20},
        "search_previous_incidents": {"service_name": svc, "limit": 5},
    }
    return defaults.get(tool_name, {"service_name": svc})


def tools_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Tools node:
    1. Determines diagnostic tools to execute from plan or verification feedback.
    2. Validates tools against ToolRegistry (rejects unregistered tools).
    3. Respects hard execution limits (AGENT_MAX_TOOL_CALLS).
    4. Executes tools via ToolService (persisting to tool_calls and audit_logs).
    5. Records the diagnostic step into the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "tools"}

    db = config.get("configurable", {}).get("db") if config else None
    inv_id_str = state.get("investigation_id")
    inv_uuid = uuid.UUID(inv_id_str) if inv_id_str else None

    # Determine candidate tools
    plan = state.get("investigation_plan") or {}
    planned_tools: List[str] = plan.get("required_tools", [])

    # If re-entering from verification with additional tools
    additional_tools = state.get("additional_tools", []) if "additional_tools" in state else []
    candidate_tools = additional_tools if additional_tools else planned_tools

    if not candidate_tools:
        candidate_tools = [
            "get_error_rate",
            "get_latency",
            "search_logs",
            "get_recent_deployments",
            "get_database_status",
        ]

    # Enforce tool limit
    current_calls = state.get("tool_calls_count", 0)
    max_calls = settings.AGENT_MAX_TOOL_CALLS
    remaining_quota = max(0, max_calls - current_calls)

    tools_to_run = candidate_tools[:remaining_quota]
    service_name = state.get("service_name") or "payment-service"

    executed_results = list(state.get("tool_results", []))
    selected_tools_list = list(state.get("selected_tools", []))
    new_calls_count = current_calls
    success_count = 0
    fail_count = 0

    tool_service = ToolService(db) if db is not None else None

    for tool_name in tools_to_run:
        # Validate tool against registry
        if not tool_registry.has_tool(tool_name):
            logger.warning(f"Tools node rejected unknown/unregistered tool: '{tool_name}'")
            executed_results.append({
                "tool_name": tool_name,
                "status": "Rejected",
                "error": f"Tool '{tool_name}' is not registered in ToolRegistry.",
                "data": None,
                "execution_time_ms": 0,
            })
            fail_count += 1
            continue

        args = _default_arguments_for_tool(tool_name, service_name)
        selected_tools_list.append({"tool_name": tool_name, "arguments": args})

        try:
            if tool_service and inv_uuid:
                res, call_entity = tool_service.execute_tool(
                    tool_name=tool_name,
                    arguments=args,
                    investigation_id=inv_uuid,
                )
                executed_results.append({
                    "tool_call_id": str(call_entity.id),
                    "tool_name": tool_name,
                    "arguments": args,
                    "status": res.status,
                    "data": res.result,
                    "execution_time_ms": res.execution_time_ms,
                })
                if res.status == "Success":
                    success_count += 1
                else:
                    fail_count += 1
            else:
                # Standalone mock execution without database session
                mock_res = tool_registry.execute(tool_name=tool_name, arguments=args)
                executed_results.append({
                    "tool_name": tool_name,
                    "arguments": args,
                    "status": mock_res.status,
                    "data": mock_res.result,
                    "execution_time_ms": mock_res.execution_time_ms,
                })
                if mock_res.status == "Success":
                    success_count += 1
                else:
                    fail_count += 1

            new_calls_count += 1

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            executed_results.append({
                "tool_name": tool_name,
                "arguments": args,
                "status": "Error",
                "error": str(e),
                "data": None,
                "execution_time_ms": 0,
            })
            fail_count += 1
            new_calls_count += 1

    # Record investigation step in database
    if db and inv_uuid:
        step_repo = InvestigationStepRepository(db)
        summary = (
            f"Executed {len(tools_to_run)} diagnostic tools ({success_count} succeeded, "
            f"{fail_count} failed/rejected). Total tool calls: {new_calls_count}/{max_calls}."
        )
        step_repo.record_step(
            investigation_id=inv_uuid,
            step_order=4,
            title="Step 4 — Diagnostic Telemetry Collection",
            status="Completed",
            output_summary=summary,
        )

    logger.info(f"Tools node finished. Ran {len(tools_to_run)} tools.")

    return {
        "selected_tools": selected_tools_list,
        "tool_results": executed_results,
        "tool_calls_count": new_calls_count,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "current_step": "tools",
    }
