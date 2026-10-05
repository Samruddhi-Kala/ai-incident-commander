"""
Tests for Tool Execution Persistence — Phase 5

Verifies that all tool executions (successful, failed, and batch)
are transactional and persisted into `tool_calls` and `audit_logs` tables,
with execution duration and optional investigation_id context.
"""
import uuid
from fastapi import status
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.tool_call import ToolCall
from app.models.audit_log import AuditLog


def test_tool_execution_persists_to_tool_calls_and_audit_logs(client):
    """
    Verify successful tool execution creates both a tool_calls row
    and an audit_logs row with duration, name, arguments, and result.
    """
    payload = {
        "tool_name": "get_error_rate",
        "arguments": {"service_name": "payment-service", "minutes": 30},
    }
    response = client.post("/api/v1/tools/execute", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Success"
    assert data["tool_name"] == "get_error_rate"
    assert data["tool_call_id"] is not None
    assert data["execution_time_ms"] >= 0

    tool_call_id = uuid.UUID(data["tool_call_id"])

    with SessionLocal() as db:
        # Verify tool_calls row
        tool_call = db.get(ToolCall, tool_call_id)
        assert tool_call is not None
        assert tool_call.tool_name == "get_error_rate"
        assert tool_call.arguments == {"service_name": "payment-service", "minutes": 30}
        assert tool_call.status == "Success"
        assert tool_call.execution_time_ms >= 0
        assert tool_call.result["service_name"] == "payment-service"
        assert tool_call.investigation_id is None

        # Verify audit_logs row
        audit_entry = db.scalars(
            select(AuditLog)
            .where(AuditLog.action_type == "tool.execute")
            .order_by(AuditLog.created_at.desc())
        ).first()
        assert audit_entry is not None
        assert audit_entry.actor_type == "SYSTEM_AGENT"
        assert audit_entry.payload["tool_name"] == "get_error_rate"
        assert audit_entry.payload["tool_call_id"] == str(tool_call_id)
        assert audit_entry.payload["status"] == "Success"
        assert audit_entry.payload["execution_time_ms"] >= 0


def test_failed_tool_execution_persists_to_tool_calls_and_audit_logs(client):
    """
    Verify failed tool execution creates both a tool_calls row
    and an audit_logs row with Error status and error details.
    """
    payload = {
        "tool_name": "non_existent_diagnostic_tool",
        "arguments": {"foo": "bar"},
    }
    response = client.post("/api/v1/tools/execute", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Error"
    assert "error" in data["result"]
    assert data["tool_call_id"] is not None

    tool_call_id = uuid.UUID(data["tool_call_id"])

    with SessionLocal() as db:
        # Verify tool_calls row has Error status
        tool_call = db.get(ToolCall, tool_call_id)
        assert tool_call is not None
        assert tool_call.tool_name == "non_existent_diagnostic_tool"
        assert tool_call.status == "Error"
        assert "error" in tool_call.result

        # Verify audit_logs row captures the failure
        audit_entry = db.scalars(
            select(AuditLog)
            .where(AuditLog.action_type == "tool.execute")
            .order_by(AuditLog.created_at.desc())
        ).first()
        assert audit_entry is not None
        assert audit_entry.payload["status"] == "Error"
        assert "error" in audit_entry.payload


def test_tool_execution_with_investigation_id(client):
    """
    Verify that an optional investigation_id is linked to the tool_calls
    record and the parent incident is populated in the audit_logs entry.
    """
    with SessionLocal() as db:
        # Create service, incident, and investigation
        svc = Service(name=f"svc-{uuid.uuid4().hex[:6]}", owner_team="Core")
        db.add(svc)
        db.commit()

        inc = Incident(
            title="Latency Alert",
            description="High latency on service",
            service_id=svc.id,
            severity="SEV-2",
        )
        db.add(inc)
        db.commit()

        inv = Investigation(
            incident_id=inc.id,
            investigation_number=f"INV-{uuid.uuid4().hex[:4].upper()}",
            status="Active",
        )
        db.add(inv)
        db.commit()

        inv_id = inv.id
        inc_id = inc.id

    payload = {
        "tool_name": "get_latency",
        "arguments": {"service_name": "payment-service", "percentile": "p99"},
        "investigation_id": str(inv_id),
    }
    response = client.post("/api/v1/tools/execute", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Success"
    assert data["investigation_id"] == str(inv_id)

    tool_call_id = uuid.UUID(data["tool_call_id"])

    with SessionLocal() as db:
        tool_call = db.get(ToolCall, tool_call_id)
        assert tool_call is not None
        assert tool_call.investigation_id == inv_id

        # Verify audit log has incident_id linked from investigation
        audit_entry = db.scalars(
            select(AuditLog)
            .where(AuditLog.action_type == "tool.execute")
            .order_by(AuditLog.created_at.desc())
        ).first()
        assert audit_entry is not None
        assert audit_entry.incident_id == inc_id
        assert audit_entry.payload["investigation_id"] == str(inv_id)


def test_batch_execution_persists_individual_records(client):
    """
    Verify batch execution creates individual tool_calls and audit_logs
    rows for each tool call in the batch.
    """
    payload = {
        "tools": [
            {"tool_name": "get_error_rate", "arguments": {"service_name": "payment-service"}},
            {"tool_name": "get_latency", "arguments": {"service_name": "payment-service"}},
            {"tool_name": "get_service_health", "arguments": {"service_name": "payment-service"}},
        ]
    }
    response = client.post("/api/v1/tools/execute/batch", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_tools"] == 3
    assert len(data["results"]) == 3

    tool_call_ids = [uuid.UUID(r["tool_call_id"]) for r in data["results"]]

    with SessionLocal() as db:
        for t_id in tool_call_ids:
            tool_call = db.get(ToolCall, t_id)
            assert tool_call is not None
            assert tool_call.status == "Success"
            assert tool_call.execution_time_ms >= 0


def test_backward_compatibility_without_investigation_id(client):
    """
    Verify requests without investigation_id continue to work identically.
    """
    payload = {
        "tool_name": "search_logs",
        "arguments": {"service_name": "payment-service", "limit": 5},
    }
    response = client.post("/api/v1/tools/execute", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Success"
    assert data["investigation_id"] is None
    assert data["tool_call_id"] is not None
