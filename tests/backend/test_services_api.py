import uuid
from fastapi import status


def test_create_service_success(client):
    """
    Test POST /api/v1/services creates a new service.
    """
    svc_name = f"billing-svc-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": svc_name,
        "description": "Processes billing transactions",
        "owner_team": "FinTech Team",
        "tier": "Tier-1",
        "repository_url": "https://github.com/org/billing-svc",
        "dependencies": ["auth-service", "database-cluster"],
    }
    response = client.post("/api/v1/services", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == svc_name
    assert data["owner_team"] == "FinTech Team"
    assert "id" in data


def test_create_duplicate_service_conflict(client):
    """
    Test POST /api/v1/services with duplicate name returns 409 Conflict.
    """
    svc_name = f"dup-svc-{uuid.uuid4().hex[:6]}"
    payload = {
        "name": svc_name,
        "owner_team": "Team A",
    }
    resp1 = client.post("/api/v1/services", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post("/api/v1/services", json=payload)
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in resp2.json()["message"]


def test_get_service_by_id_success(client):
    """
    Test GET /api/v1/services/{service_id} returns service details.
    """
    svc_name = f"search-svc-{uuid.uuid4().hex[:6]}"
    create_resp = client.post("/api/v1/services", json={
        "name": svc_name,
        "owner_team": "Search Team",
    })
    svc_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/services/{svc_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == svc_id
    assert response.json()["name"] == svc_name


def test_get_service_not_found(client):
    """
    Test GET /api/v1/services/{fake_id} returns 404 Not Found.
    """
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/services/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_services_pagination(client):
    """
    Test GET /api/v1/services supports pagination parameters.
    """
    response = client.get("/api/v1/services?page=1&page_size=5")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert "total" in data
    assert "total_pages" in data


def test_update_service_success(client):
    """
    Test PATCH /api/v1/services/{service_id} updates mutable fields.
    """
    svc_name = f"update-svc-{uuid.uuid4().hex[:6]}"
    create_resp = client.post("/api/v1/services", json={
        "name": svc_name,
        "owner_team": "Old Team",
        "tier": "Tier-2",
    })
    svc_id = create_resp.json()["id"]

    patch_payload = {
        "owner_team": "New Ownership Team",
        "tier": "Tier-0",
    }
    response = client.patch(f"/api/v1/services/{svc_id}", json=patch_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["owner_team"] == "New Ownership Team"
    assert data["tier"] == "Tier-0"


def test_create_service_validation_error(client):
    """
    Test POST /api/v1/services with invalid payload returns 422 Unprocessable Entity.
    """
    response = client.post("/api/v1/services", json={"name": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
