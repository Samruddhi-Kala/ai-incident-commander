import uuid
from fastapi import status


def _create_helper_service(client) -> str:
    svc_name = f"inc-svc-{uuid.uuid4().hex[:6]}"
    resp = client.post("/api/v1/services", json={
        "name": svc_name,
        "owner_team": "Core Infra",
        "tier": "Tier-0",
    })
    return resp.json()["id"], svc_name


def test_create_incident_success(client):
    """
    Test POST /api/v1/incidents creates an incident and initializes investigation.
    """
    svc_id, svc_name = _create_helper_service(client)
    payload = {
        "title": "Database connection pool exhaustion",
        "description": "High connection latency causing HTTP 500 errors",
        "severity": "SEV-1",
        "status": "Triggered",
        "service_id": svc_id,
    }
    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Database connection pool exhaustion"
    assert data["severity"] == "SEV-1"
    assert data["status"] == "Triggered"
    assert data["service_id"] == svc_id
    assert "investigation" in data
    assert data["investigation"] is not None
    assert data["investigation"]["status"] == "Active"
    assert data["investigation"]["investigation_number"].startswith("INV-")


def test_create_incident_missing_service_404(client):
    """
    Test POST /api/v1/incidents with non-existent service_id returns 404 Not Found.
    """
    fake_service_id = str(uuid.uuid4())
    payload = {
        "title": "Orphan incident alert",
        "description": "Alert triggered for non-existent service",
        "severity": "SEV-2",
        "status": "Triggered",
        "service_id": fake_service_id,
    }
    response = client.post("/api/v1/incidents", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_ingest_incident_success(client):
    """
    Test POST /api/v1/incidents/ingest creates an incident from monitoring trigger.
    """
    svc_id, svc_name = _create_helper_service(client)
    payload = {
        "title": "Datadog Alert: Latency > 2000ms",
        "description": "p99 latency threshold breached",
        "severity": "SEV-2",
        "service_name": svc_name,
        "source": "datadog",
    }
    response = client.post("/api/v1/incidents/ingest", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Datadog Alert: Latency > 2000ms"
    assert data["status"] == "Triggered"
    assert "[DATADOG ALERT]" in data["description"]
    assert data["investigation"] is not None


def test_ingest_incident_unknown_service_404(client):
    """
    Test POST /api/v1/incidents/ingest for unknown service_name returns 404 Not Found.
    """
    payload = {
        "title": "Alert for ghost service",
        "description": "High CPU usage",
        "severity": "SEV-3",
        "service_name": "ghost-service-nonexistent-12345",
        "source": "cloudwatch",
    }
    response = client.post("/api/v1/incidents/ingest", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["message"]


def test_get_incident_by_id_success(client):
    """
    Test GET /api/v1/incidents/{incident_id} retrieves incident details.
    """
    svc_id, _ = _create_helper_service(client)
    create_resp = client.post("/api/v1/incidents", json={
        "title": "Memory Leak Alert",
        "description": "Heap space exhausted",
        "severity": "SEV-2",
        "service_id": svc_id,
    })
    inc_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/incidents/{inc_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == inc_id
    assert data["title"] == "Memory Leak Alert"
    assert "service" in data
    assert data["service"]["id"] == svc_id


def test_get_incident_not_found(client):
    """
    Test GET /api/v1/incidents/{fake_id} returns 404 Not Found.
    """
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/incidents/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_incidents_with_filters_and_pagination(client):
    """
    Test GET /api/v1/incidents supports filtering and pagination.
    """
    svc_id, _ = _create_helper_service(client)
    client.post("/api/v1/incidents", json={
        "title": "Filter Test Inc 1",
        "description": "Test inc 1",
        "severity": "SEV-1",
        "status": "Triggered",
        "service_id": svc_id,
    })

    response = client.get(f"/api/v1/incidents?severity=SEV-1&status=Triggered&page=1&page_size=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert len(data["items"]) >= 1
    for item in data["items"]:
        assert item["severity"] == "SEV-1"
        assert item["status"] == "Triggered"


def test_update_incident_status_and_resolved_at(client):
    """
    Test PATCH /api/v1/incidents/{id} updates status and sets resolved_at timestamp when Resolved.
    """
    svc_id, _ = _create_helper_service(client)
    create_resp = client.post("/api/v1/incidents", json={
        "title": "Transient Network Flap",
        "description": "Packet loss detected",
        "severity": "SEV-3",
        "status": "Investigating",
        "service_id": svc_id,
    })
    inc_id = create_resp.json()["id"]

    response = client.patch(f"/api/v1/incidents/{inc_id}", json={
        "status": "Resolved",
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "Resolved"
    assert data["resolved_at"] is not None


def test_create_incident_invalid_state_400(client):
    """
    Test POST /api/v1/incidents with invalid severity returns 400 Bad Request.
    """
    svc_id, _ = _create_helper_service(client)
    response = client.post("/api/v1/incidents", json={
        "title": "Bad Severity Incident",
        "description": "Invalid severity",
        "severity": "INVALID_SEVERITY_CODE",
        "service_id": svc_id,
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
