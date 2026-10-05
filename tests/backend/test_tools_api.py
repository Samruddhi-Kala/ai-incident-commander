"""
Tests for Engineering Tools API Endpoints — Phase 5

Covers:
- GET /api/v1/tools/ — list all tools
- GET /api/v1/tools/schemas — get tool schemas for LLM function calling
- POST /api/v1/tools/execute — execute a single tool
- POST /api/v1/tools/execute/batch — execute multiple tools
"""
import pytest
from fastapi.testclient import TestClient


class TestToolsAPI:
    """Tests for the Engineering Tools API endpoints."""

    def test_list_tools(self, client: TestClient):
        """GET /api/v1/tools/ should return all 14 registered tools."""
        response = client.get("/api/v1/tools/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] == 14
        assert len(data["domains"]) == 5
        assert len(data["tools"]) == 14

        # Verify all expected domains are present
        domain_set = set(data["domains"])
        assert "observability" in domain_set
        assert "deployment" in domain_set
        assert "git" in domain_set
        assert "incident_history" in domain_set
        assert "infrastructure" in domain_set

    def test_get_tool_schemas(self, client: TestClient):
        """GET /api/v1/tools/schemas should return LLM-ready schemas."""
        response = client.get("/api/v1/tools/schemas")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] == 14
        assert len(data["schemas"]) == 14

        # Verify schema structure
        for schema in data["schemas"]:
            assert "name" in schema
            assert "domain" in schema
            assert "description" in schema
            assert "parameters" in schema

    def test_execute_get_metrics(self, client: TestClient):
        """POST /api/v1/tools/execute — execute get_metrics tool."""
        response = client.post("/api/v1/tools/execute", json={
            "tool_name": "get_metrics",
            "arguments": {
                "service_name": "payment-service",
                "metric_name": "error_rate",
                "minutes": 5,
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["tool_name"] == "get_metrics"
        assert data["domain"] == "observability"
        assert data["status"] == "Success"
        assert data["result"]["service_name"] == "payment-service"
        assert len(data["result"]["data_points"]) == 5
        assert data["execution_time_ms"] >= 0

    def test_execute_search_logs(self, client: TestClient):
        """POST /api/v1/tools/execute — execute search_logs tool."""
        response = client.post("/api/v1/tools/execute", json={
            "tool_name": "search_logs",
            "arguments": {
                "service_name": "payment-service",
                "level": "ERROR",
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Success"
        assert data["result"]["total_results"] > 0

    def test_execute_get_service_health(self, client: TestClient):
        """POST /api/v1/tools/execute — execute get_service_health tool."""
        response = client.post("/api/v1/tools/execute", json={
            "tool_name": "get_service_health",
            "arguments": {"service_name": "payment-service"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Success"
        assert data["domain"] == "infrastructure"
        assert data["result"]["status"] == "degraded"

    def test_execute_unknown_tool(self, client: TestClient):
        """POST /api/v1/tools/execute — unknown tool returns Error status."""
        response = client.post("/api/v1/tools/execute", json={
            "tool_name": "nonexistent_tool",
            "arguments": {},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Error"
        assert "not registered" in data["result"]["error"]

    def test_execute_batch(self, client: TestClient):
        """POST /api/v1/tools/execute/batch — execute multiple tools."""
        response = client.post("/api/v1/tools/execute/batch", json={
            "tools": [
                {
                    "tool_name": "get_error_rate",
                    "arguments": {"service_name": "payment-service"},
                },
                {
                    "tool_name": "search_logs",
                    "arguments": {"service_name": "payment-service", "level": "ERROR"},
                },
                {
                    "tool_name": "get_service_health",
                    "arguments": {"service_name": "payment-service"},
                },
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_tools"] == 3
        assert len(data["results"]) == 3
        assert data["total_execution_time_ms"] >= 0

        # All results should be Success
        for result in data["results"]:
            assert result["status"] == "Success"

    def test_execute_missing_tool_name(self, client: TestClient):
        """POST /api/v1/tools/execute — missing tool_name returns 422."""
        response = client.post("/api/v1/tools/execute", json={
            "arguments": {"service_name": "payment-service"},
        })
        assert response.status_code == 422

    def test_execute_batch_empty_tools(self, client: TestClient):
        """POST /api/v1/tools/execute/batch — empty tools list returns 422."""
        response = client.post("/api/v1/tools/execute/batch", json={
            "tools": [],
        })
        assert response.status_code == 422
