"""
LangGraph Investigation Workflow Orchestrator

Defines and compiles the stateful investigation graph for automated incident analysis:
INTAKE -> PLANNER -> (RAG) -> TOOLS -> EVIDENCE -> HYPOTHESES -> VERIFICATION -> (LOOP/ROOT_CAUSE) -> ROOT_CAUSE -> END
"""
from typing import Literal, Optional
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, START, END

from app.agent.state import InvestigationState, create_initial_state
from app.agent.llm import LLMService
from app.core.config import settings
from app.core.logging import logger
from app.agent.nodes import (
    intake_node,
    planner_node,
    rag_node,
    tools_node,
    evidence_node,
    hypotheses_node,
    verification_node,
    root_cause_node,
)


def _route_after_intake(state: InvestigationState) -> Literal["planner", "__end__"]:
    """Conditional routing following incident intake."""
    if state.get("status_outcome") == "failed":
        return END
    return "planner"


def _route_after_planner(state: InvestigationState) -> Literal["rag", "tools", "__end__"]:
    """Conditional routing based on whether organizational runbooks are required."""
    if state.get("status_outcome") == "failed":
        return END
    plan = state.get("investigation_plan") or {}
    if plan.get("requires_rag", True):
        return "rag"
    return "tools"


def _route_after_verification(state: InvestigationState) -> Literal["tools", "root_cause", "__end__"]:
    """Conditional loop evaluation: decides between collecting more evidence or concluding root cause."""
    if state.get("status_outcome") == "failed":
        return END

    need_more = state.get("need_more_evidence", False)
    current_iter = state.get("iteration_count", 1)
    max_iter = state.get("max_iterations") or settings.AGENT_MAX_ITERATIONS
    tool_calls = state.get("tool_calls_count", 0)
    max_calls = settings.AGENT_MAX_TOOL_CALLS

    if need_more and current_iter < max_iter and tool_calls < max_calls:
        logger.info(
            f"Investigation loop cycle: iteration {current_iter}/{max_iter}, "
            f"tool calls {tool_calls}/{max_calls}. Returning to tools node for additional evidence."
        )
        return "tools"

    return "root_cause"


def build_investigation_graph():
    """
    Constructs and compiles the stateful LangGraph Investigation StateGraph.
    """
    builder = StateGraph(InvestigationState)

    # Register Nodes
    builder.add_node("intake", intake_node)
    builder.add_node("planner", planner_node)
    builder.add_node("rag", rag_node)
    builder.add_node("tools", tools_node)
    builder.add_node("evidence", evidence_node)
    builder.add_node("hypotheses", hypotheses_node)
    builder.add_node("verification", verification_node)
    builder.add_node("root_cause", root_cause_node)

    # Edge: START -> intake
    builder.add_edge(START, "intake")

    # Edge: intake -> planner (or END if intake failed)
    builder.add_conditional_edges("intake", _route_after_intake)

    # Edge: planner -> rag or tools
    builder.add_conditional_edges("planner", _route_after_planner)

    # Edge: rag -> tools
    builder.add_edge("rag", "tools")

    # Edge: tools -> evidence
    builder.add_edge("tools", "evidence")

    # Edge: evidence -> hypotheses
    builder.add_edge("evidence", "hypotheses")

    # Edge: hypotheses -> verification
    builder.add_edge("hypotheses", "verification")

    # Edge: verification -> tools (loop) or root_cause
    builder.add_conditional_edges("verification", _route_after_verification)

    # Edge: root_cause -> END
    builder.add_edge("root_cause", END)

    return builder.compile()


# Singleton compiled graph instance
investigation_graph = build_investigation_graph()


def run_investigation_workflow(
    incident_id: str,
    max_iterations: int = 5,
    db: Optional[Session] = None,
    llm: Optional[LLMService] = None,
) -> InvestigationState:
    """
    Synchronous orchestrator entry point that executes the full LangGraph investigation workflow.

    Args:
        incident_id: String UUID of the incident to investigate.
        max_iterations: Maximum evidence gathering feedback loops allowed.
        db: SQLAlchemy database session.
        llm: LLMService instance (defaults to configured provider or fake).

    Returns:
        The final InvestigationState containing all diagnostic findings and root cause.
    """
    initial_state = create_initial_state(
        incident_id=incident_id,
        max_iterations=max_iterations,
    )

    config = {
        "configurable": {
            "db": db,
            "llm": llm or LLMService(),
        }
    }

    logger.info(f"Initiating LangGraph investigation workflow for incident {incident_id}...")
    final_state = investigation_graph.invoke(initial_state, config=config)
    logger.info(
        f"Completed LangGraph investigation workflow for incident {incident_id}. "
        f"Status: {final_state.get('status_outcome')}, Step: {final_state.get('current_step')}."
    )
    return final_state
