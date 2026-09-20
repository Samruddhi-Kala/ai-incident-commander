from fastapi import status


def test_root_endpoint(client):
    """
    Test root endpoint response.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "online"
    assert "health_check" in data


def test_app_health_endpoint(client):
    """
    Test application health check.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "environment" in data


def test_db_health_endpoint_format(client):
    """
    Test DB health check endpoint returns appropriate HTTP status and structure.
    """
    response = client.get("/health/db")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_redis_health_endpoint_format(client):
    """
    Test Redis health check endpoint returns appropriate HTTP status and structure.
    """
    response = client.get("/health/redis")
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
    data = response.json()
    assert "status" in data
    assert "redis" in data
