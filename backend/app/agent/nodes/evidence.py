"""
Evidence Node

Extracts empirical findings from diagnostic tool executions and knowledge retrieval,
correlating observations into structured Evidence entities persisted in the database.
"""
import uuid
from typing import Any, Dict, List, Tuple
from langchain_core.runnables import RunnableConfig
from app.agent.state import InvestigationState
from app.models.evidence import Evidence
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.investigation_step_repo import InvestigationStepRepository
from app.core.logging import logger


def _summarize_tool_result(tool_name: str, data: Any, status: str) -> Tuple[str, float]:
    """Extracts human-readable observation and relevance score from tool output."""
    if status != "Success" or not isinstance(data, dict):
        return f"Tool {tool_name} returned status '{status}'.", 0.3

    if tool_name == "get_error_rate":
        rate = data.get("error_rate_percent", 0.0)
        baseline = data.get("baseline_percent", 1.0)
        return (
            f"Error rate currently observed at {rate:.1f}% (baseline: {baseline:.1f}%).",
            0.9 if rate > baseline else 0.5,
        )

    if tool_name == "get_latency":
        p99 = data.get("p99_ms", 0.0)
        p50 = data.get("p50_ms", 0.0)
        return (
            f"Latency metrics indicate P99 of {p99:.0f}ms and P50 of {p50:.0f}ms.",
            0.85 if p99 > 500 else 0.5,
        )

    if tool_name == "search_logs":
        total = data.get("total_results", data.get("total_matches", 0))
        samples = data.get("logs", data.get("samples", []))
        sample_msg = samples[0].get("message") if samples else "No logs matched query"
        return (
            f"Found {total} log entries matching error query. Sample: '{sample_msg}'.",
            0.9 if total > 0 else 0.4,
        )

    if tool_name == "get_recent_deployments":
        deployments = data.get("deployments", [])
        if deployments:
            d = deployments[0]
            ver = d.get("version", "unknown")
            time_ago = d.get("deployed_at", "recently")
            env = d.get("environment", "prod")
            return (
                f"Recent deployment '{ver}' deployed to {env} at {time_ago}.",
                0.9,
            )
        return "No recent deployments found within lookback window.", 0.4

    if tool_name == "get_recent_commits":
        commits = data.get("commits", [])
        if commits:
            c = commits[0]
            msg = c.get("message", "")
            sha = c.get("sha", "")[:7]
            return f"Recent commit {sha}: '{msg}'.", 0.8
        return "No recent git commits found.", 0.3

    if tool_name == "get_database_status":
        active = data.get("connections_active", data.get("connection_pool", {}).get("active_connections", 0))
        max_conn = data.get("connections_max", data.get("connection_pool", {}).get("max_connections", 50))
        return (
            f"Database status: {active}/{max_conn} active connections in pool.",
            0.85 if active >= max_conn * 0.8 else 0.5,
        )

    if tool_name == "get_service_health":
        health = data.get("status", "unknown")
        restarts = data.get("restart_count", 0)
        return (
            f"Service health check reports status='{health}' with {restarts} pod restarts.",
            0.9 if health != "healthy" or restarts > 0 else 0.4,
        )

    return f"Observation from {tool_name}: {str(data)[:120]}...", 0.6


def evidence_node(state: InvestigationState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Evidence node:
    1. Transforms diagnostic tool results into structured Evidence items.
    2. Persists items into the database associated with the active investigation.
    3. Records the diagnostic step into the database.
    """
    if state.get("status_outcome") == "failed":
        return {"current_step": "evidence"}

    db = config.get("configurable", {}).get("db") if config else None
    inv_id_str = state.get("investigation_id")
    inv_uuid = uuid.UUID(inv_id_str) if inv_id_str else None

    existing_evidence = list(state.get("evidence", []))
    existing_tools_seen = {e.get("source_tool") for e in existing_evidence}

    new_evidence: List[Dict[str, Any]] = []

    for tr in state.get("tool_results", []):
        t_name = tr.get("tool_name", "unknown")
        status = tr.get("status", "unknown")
        data = tr.get("data")

        # Skip duplicate processing for tools already converted
        if t_name in existing_tools_seen:
            continue

        summary, score = _summarize_tool_result(t_name, data, status)
        evidence_entry = {
            "id": str(uuid.uuid4()),
            "source_tool": t_name,
            "summary": summary,
            "raw_payload": data or {"status": status, "error": tr.get("error")},
            "relevance_score": score,
        }

        # Persist to DB if session available
        if db and inv_uuid:
            ev_record = Evidence(
                id=uuid.UUID(evidence_entry["id"]),
                investigation_id=inv_uuid,
                source_tool=t_name,
                summary=summary,
                raw_payload=evidence_entry["raw_payload"],
                relevance_score=score,
            )
            db.add(ev_record)
            db.flush()

        new_evidence.append(evidence_entry)
        existing_tools_seen.add(t_name)

    if db:
        db.commit()

    all_evidence = existing_evidence + new_evidence

    # Record investigation step in database
    if db and inv_uuid:
        step_repo = InvestigationStepRepository(db)
        summary = (
            f"Collected and correlated {len(all_evidence)} empirical telemetry evidence items "
            f"({len(new_evidence)} new in current cycle)."
        )
        step_repo.record_step(
            investigation_id=inv_uuid,
            step_order=5,
            title="Step 5 — Evidence Extraction & Correlation",
            status="Completed",
            output_summary=summary,
        )

    logger.info(f"Evidence node completed with {len(all_evidence)} total evidence items.")

    return {
        "evidence": all_evidence,
        "current_step": "evidence",
    }
