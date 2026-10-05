"""
Intake Node

Loads the incident and service context from the database, initializes or
retrieves the active investigation session, and normalizes state for the planner.
"""
import uuid
from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.models.incident import Incident
from app.models.service import Service
from app.repositories.incident_repo import IncidentRepository
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.services.investigation_service import InvestigationService
from app.core.logging import logger


def intake_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Intake node:
    1. Loads the incident record.
    2. Retrieves service metadata.
    3. Initializes or attaches the active investigation.
    4. Records the diagnostic step into the database.
    """
    incident_id_str = state.get("incident_id")
    if not incident_id_str:
        return {
            "current_step": "intake",
            "status_outcome": "failed",
            "errors": ["Missing incident_id in state."],
        }

    db = config.get("configurable", {}).get("db") if config else None
    if db is None:
        # Standalone mock execution
        return {
            "current_step": "intake",
            "status_outcome": "in_progress",
            "title": state.get("title") or "Mock Incident",
            "service_name": state.get("service_name") or "payment-service",
        }

    try:
        inc_uuid = uuid.UUID(incident_id_str)
    except ValueError:
        return {
            "current_step": "intake",
            "status_outcome": "failed",
            "errors": [f"Invalid incident_id UUID: {incident_id_str}"],
        }

    incident_repo = IncidentRepository(db)
    incident = incident_repo.get_by_id(inc_uuid)
    if not incident:
        logger.error(f"Intake failed: Incident {inc_uuid} not found.")
        return {
            "current_step": "intake",
            "status_outcome": "failed",
            "errors": [f"Incident '{inc_uuid}' does not exist."],
        }

    # Retrieve or initialize investigation
    inv_service = InvestigationService(db)
    investigation = inv_service.initialize_investigation(incident.id)

    # Retrieve service context
    service_name = None
    service_tier = None
    service_deps = []
    if incident.service_id:
        svc = db.get(Service, incident.service_id)
        if svc:
            service_name = svc.name
            service_tier = svc.tier
            service_deps = svc.dependencies or []

    # Record intake step in database
    step_repo = InvestigationStepRepository(db)
    summary = (
        f"Ingested incident '{incident.title}' ({incident.severity}) on service '{service_name or 'unassigned'}'. "
        f"Initialized investigation session {investigation.investigation_number}."
    )
    step_repo.record_step(
        investigation_id=investigation.id,
        step_order=1,
        title="Step 1 — Incident Intake & Context Normalization",
        status="Completed",
        output_summary=summary,
    )

    logger.info(f"Intake node completed for investigation {investigation.investigation_number}")

    return {
        "incident_id": str(incident.id),
        "investigation_id": str(investigation.id),
        "investigation_number": investigation.investigation_number,
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity,
        "status": incident.status,
        "service_name": service_name,
        "service_tier": service_tier,
        "service_dependencies": service_deps,
        "current_step": "intake",
        "status_outcome": "in_progress",
    }
