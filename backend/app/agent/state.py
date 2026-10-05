"""
Agent State Definition

Defines the typed, serializable LangGraph state dictionary that flows
through all nodes of the incident investigation workflow.
"""
from typing import Any, Dict, List, Optional, TypedDict


class InvestigationState(TypedDict):
    """
    Complete state dictionary for an incident investigation workflow session.
    All data is serializable for LangGraph checkpoints and state inspection.
    """
    # Incident & Service Context
    incident_id: str
    investigation_id: str
    investigation_number: str
    title: str
    description: str
    severity: str
    status: str
    service_name: Optional[str]
    service_tier: Optional[str]
    service_dependencies: List[str]

    # Investigation Planning
    investigation_plan: Optional[Dict[str, Any]]

    # Knowledge Retrieval (RAG)
    retrieved_context: Optional[str]
    retrieved_sources: List[Dict[str, Any]]

    # Tool Execution & Observability
    selected_tools: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tool_calls_count: int
    iteration_count: int
    max_iterations: int
    need_more_evidence: bool

    # Empirical Findings & Deductive Reasoning
    evidence: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]

    # Root Cause Determination
    probable_root_cause: Optional[str]
    confidence: Optional[float]
    recommended_remediation: List[str]
    analysis_reasoning: Optional[str]

    # Workflow Operational Tracking
    current_step: str
    status_outcome: str  # "completed", "failed", "inconclusive"
    errors: List[str]


def create_initial_state(
    incident_id: str,
    max_iterations: int = 5,
) -> InvestigationState:
    """
    Constructs an initialized empty investigation state for starting a graph execution.
    """
    return {
        "incident_id": incident_id,
        "investigation_id": "",
        "investigation_number": "",
        "title": "",
        "description": "",
        "severity": "",
        "status": "Triggered",
        "service_name": None,
        "service_tier": None,
        "service_dependencies": [],
        "investigation_plan": None,
        "retrieved_context": None,
        "retrieved_sources": [],
        "selected_tools": [],
        "tool_results": [],
        "tool_calls_count": 0,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "need_more_evidence": False,
        "evidence": [],
        "hypotheses": [],
        "verification_results": [],
        "probable_root_cause": None,
        "confidence": None,
        "recommended_remediation": [],
        "analysis_reasoning": None,
        "current_step": "init",
        "status_outcome": "in_progress",
        "errors": [],
    }
