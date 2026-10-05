"""
Planner Node

Formulates a structured diagnostic plan including core investigation questions,
required diagnostic tools, and knowledge retrieval queries.
"""
import uuid
from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.agent.llm import LLMService
from app.tools.registry import tool_registry
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.core.logging import logger


def planner_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Planner node:
    1. Evaluates normalized incident and service context.
    2. Identifies questions and selects registered diagnostic tools.
    3. Produces a structured InvestigationPlan.
    4. Persists the planning step to the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "planner"}

    db = config.get("configurable", {}).get("db") if config else None
    llm = config.get("configurable", {}).get("llm") if config else None
    if llm is None:
        llm = LLMService()

    available_tool_names = [t["tool_name"] for t in tool_registry.list_tools()]

    plan = llm.generate_plan(
        title=state.get("title", ""),
        description=state.get("description", ""),
        severity=state.get("severity", ""),
        service_name=state.get("service_name"),
        service_tier=state.get("service_tier"),
        dependencies=state.get("service_dependencies", []),
        available_tools=available_tool_names,
    )

    # Persist planning step if db session exists
    inv_id_str = state.get("investigation_id")
    if db and inv_id_str:
        step_repo = InvestigationStepRepository(db)
        summary = (
            f"Formulated investigation plan with {len(plan.questions)} questions and "
            f"{len(plan.required_tools)} target tools: {', '.join(plan.required_tools)}. "
            f"Requires RAG: {plan.requires_rag}."
        )
        step_repo.record_step(
            investigation_id=uuid.UUID(inv_id_str),
            step_order=2,
            title="Step 2 — Diagnostic Planning",
            status="Completed",
            output_summary=summary,
        )

    logger.info(f"Planner node completed: {len(plan.required_tools)} tools selected.")

    return {
        "investigation_plan": plan.model_dump(),
        "current_step": "planner",
    }
