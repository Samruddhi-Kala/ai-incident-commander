"""
Hypotheses Node

Formulates competing diagnostic hypotheses regarding failure mechanisms,
drawing upon empirical telemetry evidence, service topologies, and runbooks.
Persists generated hypotheses to the `hypotheses` table.
"""
import uuid
from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.agent.llm import LLMService
from app.models.hypothesis import Hypothesis
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.core.logging import logger


def hypotheses_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Hypotheses node:
    1. Evaluates accumulated evidence against incident context and knowledge.
    2. Uses LLM to generate multiple competing failure hypotheses.
    3. Persists hypotheses into the database.
    4. Records the diagnostic step into the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "hypotheses"}

    db = config.get("configurable", {}).get("db") if config else None
    llm = config.get("configurable", {}).get("llm") if config else None
    if llm is None:
        llm = LLMService()

    inv_id_str = state.get("investigation_id")
    inv_uuid = uuid.UUID(inv_id_str) if inv_id_str else None

    # Call LLM to generate hypotheses
    payload = llm.generate_hypotheses(
        title=state.get("title", ""),
        description=state.get("description", ""),
        service_name=state.get("service_name"),
        retrieved_context=state.get("retrieved_context"),
        evidence_list=state.get("evidence", []),
    )

    persisted_hypotheses: List[Dict[str, Any]] = []

    # Map evidence IDs if available
    evidence_items = state.get("evidence", [])
    evidence_id_map = {e.get("summary"): e.get("id") for e in evidence_items if "id" in e}

    for item in payload.hypotheses:
        hypo_id = str(uuid.uuid4())
        supp_ids = []
        for s in item.supporting_evidence:
            matched_id = evidence_id_map.get(s)
            if matched_id:
                supp_ids.append(uuid.UUID(matched_id))

        hypo_dict = {
            "id": hypo_id,
            "title": item.title,
            "description": item.description,
            "confidence": item.confidence,
            "status": "Proposed",
            "supporting_evidence": item.supporting_evidence,
            "contradicting_evidence": item.contradicting_evidence,
        }

        if db and inv_uuid:
            record = Hypothesis(
                id=uuid.UUID(hypo_id),
                investigation_id=inv_uuid,
                hypothesis_text=f"{item.title}: {item.description}",
                status="Proposed",
                confidence_score=item.confidence,
                supporting_evidence_ids=supp_ids,
                opposing_evidence_ids=[],
            )
            db.add(record)
            db.flush()

        persisted_hypotheses.append(hypo_dict)

    if db:
        db.commit()

    # Record investigation step in database
    if db and inv_uuid:
        step_repo = InvestigationStepRepository(db)
        summary = (
            f"Generated {len(persisted_hypotheses)} competing diagnostic hypotheses: "
            + "; ".join(f"[{h['title']} (conf: {h['confidence']:.2f})]" for h in persisted_hypotheses)
        )
        step_repo.record_step(
            investigation_id=inv_uuid,
            step_order=6,
            title="Step 6 — Competing Hypotheses Formulation",
            status="Completed",
            output_summary=summary,
        )

    logger.info(f"Hypotheses node completed with {len(persisted_hypotheses)} hypotheses.")

    return {
        "hypotheses": persisted_hypotheses,
        "current_step": "hypotheses",
    }
