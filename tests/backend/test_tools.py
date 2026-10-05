"""
Tests for Engineering Tool Adapters — Phase 5

Covers:
- BaseToolAdapter dispatch, latency tracking, and error handling
- All 5 domain adapters (Observability, Deployment, Git, Incident History, Infrastructure)
- ToolRegistry discovery, execution routing, and schema generation
- Tool execution validation for every tool method
"""
import pytest
from app.tools.base import BaseToolAdapter, ToolResult
from app.tools.observability import ObservabilityAdapter
from app.tools.deployment import DeploymentAdapter
from app.tools.git import GitAdapter
from app.tools.incident_history import IncidentHistoryAdapter
from app.tools.infrastructure import InfrastructureAdapter
from app.tools.registry import ToolRegistry


# ================================================================
# BaseToolAdapter & ToolResult Tests
# ================================================================

class TestToolResult:
    """Tests for the ToolResult Pydantic model."""

    def test_tool_result_defaults(self):
        result = ToolResult(tool_name="test_tool")
        assert result.tool_name == "test_tool"
        assert result.status == "Success"
        assert result.execution_time_ms == 0
        assert result.arguments == {}
        assert result.result == {}
        assert result.timestamp is not None

    def test_tool_result_with_data(self):
        result = ToolResult(
            tool_name="get_metrics",
            arguments={"service_name": "payment-service"},
            result={"data": "test"},
            status="Success",
            execution_time_ms=42,
        )
        assert result.tool_name == "get_metrics"
        assert result.arguments["service_name"] == "payment-service"
        assert result.execution_time_ms == 42


# ================================================================
# Observability Adapter Tests
# ================================================================

class TestObservabilityAdapter:
    """Tests for the simulated Observability adapter."""

    def setup_method(self):
        self.adapter = ObservabilityAdapter()

    def test_domain_and_tools(self):
        assert self.adapter.domain == "observability"
        assert "get_metrics" in self.adapter.tools
        assert "search_logs" in self.adapter.tools
        assert "get_error_rate" in self.adapter.tools
        assert "get_latency" in self.adapter.tools
        assert len(self.adapter.tools) == 4

    def test_get_metrics(self):
        result = self.adapter.execute("get_metrics", {
            "service_name": "payment-service",
            "metric_name": "error_rate",
            "minutes": 10,
        })
        assert result.status == "Success"
        assert result.result["service_name"] == "payment-service"
        assert result.result["metric_name"] == "error_rate"
        assert len(result.result["data_points"]) == 10
        assert result.execution_time_ms >= 0

    def test_search_logs_all(self):
        result = self.adapter.execute("search_logs", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["total_results"] > 0
        assert len(result.result["logs"]) > 0

    def test_search_logs_filtered_by_level(self):
        result = self.adapter.execute("search_logs", {
            "service_name": "payment-service",
            "level": "ERROR",
        })
        assert result.status == "Success"
        for log in result.result["logs"]:
            assert log["level"] == "ERROR"

    def test_search_logs_filtered_by_query(self):
        result = self.adapter.execute("search_logs", {
            "service_name": "payment-service",
            "query": "timeout",
        })
        assert result.status == "Success"
        for log in result.result["logs"]:
            assert "timeout" in log["message"].lower()

    def test_get_error_rate_known_service(self):
        result = self.adapter.execute("get_error_rate", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["error_rate_percent"] > 0
        assert result.result["trend"] == "increasing"

    def test_get_error_rate_unknown_service(self):
        result = self.adapter.execute("get_error_rate", {
            "service_name": "unknown-service",
        })
        assert result.status == "Success"
        assert result.result["trend"] == "stable"

    def test_get_latency(self):
        result = self.adapter.execute("get_latency", {
            "service_name": "payment-service",
            "percentile": "p99",
        })
        assert result.status == "Success"
        assert result.result["assessment"] == "degraded"
        assert result.result["deviation_factor"] > 2

    def test_get_latency_healthy_service(self):
        result = self.adapter.execute("get_latency", {
            "service_name": "auth-service",
        })
        assert result.status == "Success"
        assert result.result["assessment"] == "normal"

    def test_execute_unknown_tool(self):
        result = self.adapter.execute("nonexistent_tool", {})
        assert result.status == "Error"
        assert "not available" in result.result["error"]


# ================================================================
# Deployment Adapter Tests
# ================================================================

class TestDeploymentAdapter:
    """Tests for the simulated Deployment adapter."""

    def setup_method(self):
        self.adapter = DeploymentAdapter()

    def test_domain_and_tools(self):
        assert self.adapter.domain == "deployment"
        assert "get_recent_deployments" in self.adapter.tools
        assert "get_deployment_details" in self.adapter.tools
        assert "compare_deployments" in self.adapter.tools
        assert len(self.adapter.tools) == 3

    def test_get_recent_deployments(self):
        result = self.adapter.execute("get_recent_deployments", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["total_deployments"] > 0
        assert result.result["deployments"][0]["service_name"] == "payment-service"

    def test_get_recent_deployments_with_limit(self):
        result = self.adapter.execute("get_recent_deployments", {
            "service_name": "payment-service",
            "limit": 1,
        })
        assert result.status == "Success"
        assert len(result.result["deployments"]) == 1

    def test_get_recent_deployments_unknown_service(self):
        result = self.adapter.execute("get_recent_deployments", {
            "service_name": "unknown-service",
        })
        assert result.status == "Success"
        assert result.result["total_deployments"] >= 1

    def test_get_deployment_details_found(self):
        result = self.adapter.execute("get_deployment_details", {
            "deployment_id": "deploy-pay-005",
        })
        assert result.status == "Success"
        assert result.result["version"] == "v2.5.1"
        assert result.result["health_check_status"] == "passing"

    def test_get_deployment_details_not_found(self):
        result = self.adapter.execute("get_deployment_details", {
            "deployment_id": "deploy-nonexistent",
        })
        assert result.status == "Success"
        assert "error" in result.result

    def test_compare_deployments(self):
        result = self.adapter.execute("compare_deployments", {
            "service_name": "payment-service",
            "version_a": "v2.5.0",
            "version_b": "v2.5.1",
        })
        assert result.status == "Success"
        assert result.result["files_changed"] == 8
        assert len(result.result["config_changes"]) > 0
        assert len(result.result["dependency_changes"]) > 0
        # Verify the breaking change flag
        assert result.result["dependency_changes"][0]["breaking_change"] is True


# ================================================================
# Git Adapter Tests
# ================================================================

class TestGitAdapter:
    """Tests for the simulated Git adapter."""

    def setup_method(self):
        self.adapter = GitAdapter()

    def test_domain_and_tools(self):
        assert self.adapter.domain == "git"
        assert "get_recent_commits" in self.adapter.tools
        assert "get_commit_details" in self.adapter.tools
        assert "search_code_changes" in self.adapter.tools
        assert len(self.adapter.tools) == 3

    def test_get_recent_commits(self):
        result = self.adapter.execute("get_recent_commits", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["total_commits"] > 0
        assert result.result["branch"] == "main"

    def test_get_recent_commits_with_limit(self):
        result = self.adapter.execute("get_recent_commits", {
            "service_name": "payment-service",
            "limit": 2,
        })
        assert result.status == "Success"
        assert result.result["total_commits"] <= 2

    def test_get_commit_details_with_diff(self):
        result = self.adapter.execute("get_commit_details", {
            "sha": "a1b2c3d4e5f6",
        })
        assert result.status == "Success"
        assert result.result["author_name"] == "Alice Chen"
        assert result.result["diff_available"] is True
        assert "src/handlers/payment_handler.py" in result.result["diff"]

    def test_get_commit_details_short_sha(self):
        result = self.adapter.execute("get_commit_details", {
            "sha": "a1b2c3d",
        })
        assert result.status == "Success"
        assert result.result["sha"] == "a1b2c3d4e5f6"

    def test_get_commit_details_not_found(self):
        result = self.adapter.execute("get_commit_details", {
            "sha": "nonexistent",
        })
        assert result.status == "Success"
        assert "error" in result.result

    def test_search_code_changes_by_message(self):
        result = self.adapter.execute("search_code_changes", {
            "service_name": "payment-service",
            "query": "payment processor",
        })
        assert result.status == "Success"
        assert result.result["total_results"] > 0

    def test_search_code_changes_by_file(self):
        result = self.adapter.execute("search_code_changes", {
            "service_name": "payment-service",
            "query": "database.yml",
        })
        assert result.status == "Success"
        assert result.result["total_results"] > 0

    def test_search_code_changes_no_match(self):
        result = self.adapter.execute("search_code_changes", {
            "service_name": "payment-service",
            "query": "nonexistent-file-xyz",
        })
        assert result.status == "Success"
        assert result.result["total_results"] == 0


# ================================================================
# Incident History Adapter Tests
# ================================================================

class TestIncidentHistoryAdapter:
    """Tests for the simulated Incident History adapter."""

    def setup_method(self):
        self.adapter = IncidentHistoryAdapter()

    def test_domain_and_tools(self):
        assert self.adapter.domain == "incident_history"
        assert "search_previous_incidents" in self.adapter.tools
        assert len(self.adapter.tools) == 1

    def test_search_no_filters(self):
        result = self.adapter.execute("search_previous_incidents", {})
        assert result.status == "Success"
        assert result.result["total_results"] > 0

    def test_search_by_service_name(self):
        result = self.adapter.execute("search_previous_incidents", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        for inc in result.result["incidents"]:
            assert inc["service_name"] == "payment-service"

    def test_search_by_severity(self):
        result = self.adapter.execute("search_previous_incidents", {
            "severity": "SEV-1",
        })
        assert result.status == "Success"
        for inc in result.result["incidents"]:
            assert inc["severity"] == "SEV-1"

    def test_search_by_query(self):
        result = self.adapter.execute("search_previous_incidents", {
            "query": "timeout",
        })
        assert result.status == "Success"
        assert result.result["total_results"] > 0
        # Results should have relevance scores
        for inc in result.result["incidents"]:
            assert "relevance_score" in inc
            assert inc["relevance_score"] > 0

    def test_search_patterns_detected(self):
        result = self.adapter.execute("search_previous_incidents", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        # Payment-service has recurring incidents — patterns should be found
        assert len(result.result["patterns"]) > 0


# ================================================================
# Infrastructure Adapter Tests
# ================================================================

class TestInfrastructureAdapter:
    """Tests for the simulated Infrastructure adapter."""

    def setup_method(self):
        self.adapter = InfrastructureAdapter()

    def test_domain_and_tools(self):
        assert self.adapter.domain == "infrastructure"
        assert "get_service_health" in self.adapter.tools
        assert "get_service_dependencies" in self.adapter.tools
        assert "get_database_status" in self.adapter.tools
        assert len(self.adapter.tools) == 3

    def test_get_service_health_degraded(self):
        result = self.adapter.execute("get_service_health", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["status"] == "degraded"
        assert result.result["healthy_replicas"] < result.result["total_replicas"]
        assert len(result.result["alerts_active"]) > 0

    def test_get_service_health_healthy(self):
        result = self.adapter.execute("get_service_health", {
            "service_name": "auth-service",
        })
        assert result.status == "Success"
        assert result.result["status"] == "healthy"
        assert result.result["healthy_replicas"] == result.result["total_replicas"]

    def test_get_service_health_unknown(self):
        result = self.adapter.execute("get_service_health", {
            "service_name": "unknown-service",
        })
        assert result.status == "Success"
        assert result.result["status"] == "unknown"

    def test_get_service_dependencies(self):
        result = self.adapter.execute("get_service_dependencies", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert len(result.result["downstream"]) > 0
        assert len(result.result["upstream"]) > 0
        # Check that dependency graph is present
        assert "dependency_graph" in result.result

    def test_get_service_dependencies_unknown(self):
        result = self.adapter.execute("get_service_dependencies", {
            "service_name": "unknown-service",
        })
        assert result.status == "Success"
        assert "warning" in result.result

    def test_get_database_status(self):
        result = self.adapter.execute("get_database_status", {
            "database_name": "payment-db",
        })
        assert result.status == "Success"
        assert result.result["status"] == "healthy"
        assert result.result["connection_utilization_percent"] > 90
        assert len(result.result["warnings"]) > 0

    def test_get_database_status_unknown(self):
        result = self.adapter.execute("get_database_status", {
            "database_name": "unknown-db",
        })
        assert result.status == "Success"
        assert result.result["status"] == "unknown"


# ================================================================
# Tool Registry Tests
# ================================================================

class TestToolRegistry:
    """Tests for the ToolRegistry central management layer."""

    def setup_method(self):
        self.registry = ToolRegistry()

    def test_all_domains_registered(self):
        domains = self.registry.list_domains()
        assert "observability" in domains
        assert "deployment" in domains
        assert "git" in domains
        assert "incident_history" in domains
        assert "infrastructure" in domains
        assert len(domains) == 5

    def test_all_tools_listed(self):
        tools = self.registry.list_tools()
        tool_names = [t["tool_name"] for t in tools]
        expected = [
            "get_metrics", "search_logs", "get_error_rate", "get_latency",
            "get_recent_deployments", "get_deployment_details", "compare_deployments",
            "get_recent_commits", "get_commit_details", "search_code_changes",
            "search_previous_incidents",
            "get_service_health", "get_service_dependencies", "get_database_status",
        ]
        for name in expected:
            assert name in tool_names, f"Tool '{name}' not found in registry"
        assert len(tools) == 14

    def test_execute_routes_correctly(self):
        result = self.registry.execute("get_metrics", {
            "service_name": "payment-service",
        })
        assert result.status == "Success"
        assert result.result["service_name"] == "payment-service"

    def test_execute_unknown_tool(self):
        result = self.registry.execute("nonexistent_tool", {})
        assert result.status == "Error"
        assert "not registered" in result.result["error"]

    def test_has_tool(self):
        assert self.registry.has_tool("get_metrics") is True
        assert self.registry.has_tool("nonexistent") is False

    def test_get_tool_domain(self):
        assert self.registry.get_tool_domain("get_metrics") == "observability"
        assert self.registry.get_tool_domain("get_recent_commits") == "git"
        assert self.registry.get_tool_domain("search_previous_incidents") == "incident_history"
        assert self.registry.get_tool_domain("nonexistent") is None

    def test_get_tools_by_domain(self):
        obs_tools = self.registry.get_tools_by_domain("observability")
        assert len(obs_tools) == 4
        assert "get_metrics" in obs_tools

    def test_get_tools_by_unknown_domain(self):
        tools = self.registry.get_tools_by_domain("nonexistent")
        assert tools == []

    def test_tool_schemas_generated(self):
        schemas = self.registry.get_tool_schemas()
        assert len(schemas) == 14
        for schema in schemas:
            assert "name" in schema
            assert "domain" in schema
            assert "description" in schema
            assert "parameters" in schema

    def test_tool_schema_has_required_params(self):
        schemas = self.registry.get_tool_schemas()
        metrics_schema = next(s for s in schemas if s["name"] == "get_metrics")
        assert "service_name" in metrics_schema["parameters"]
        assert metrics_schema["parameters"]["service_name"]["required"] is True


# ================================================================
# Integration: Cross-Adapter Execution Tests
# ================================================================

class TestCrossAdapterIntegration:
    """
    Integration tests verifying that the tool registry correctly
    routes calls across different domain adapters.
    """

    def setup_method(self):
        self.registry = ToolRegistry()

    def test_payment_service_investigation_flow(self):
        """
        Simulate a realistic investigation flow: check metrics, then logs,
        then deployments, then infrastructure health.
        """
        # Step 1: Check error rate
        err = self.registry.execute("get_error_rate", {"service_name": "payment-service"})
        assert err.status == "Success"
        assert err.result["error_rate_percent"] > 10

        # Step 2: Search error logs
        logs = self.registry.execute("search_logs", {
            "service_name": "payment-service",
            "level": "ERROR",
        })
        assert logs.status == "Success"
        assert logs.result["total_results"] > 0

        # Step 3: Check recent deployments
        deploys = self.registry.execute("get_recent_deployments", {
            "service_name": "payment-service",
        })
        assert deploys.status == "Success"
        assert deploys.result["total_deployments"] > 0

        # Step 4: Check service health
        health = self.registry.execute("get_service_health", {
            "service_name": "payment-service",
        })
        assert health.status == "Success"
        assert health.result["status"] == "degraded"

        # Step 5: Check database status
        db = self.registry.execute("get_database_status", {"database_name": "payment-db"})
        assert db.status == "Success"
        assert db.result["connection_utilization_percent"] > 90

        # Step 6: Search previous incidents
        prev = self.registry.execute("search_previous_incidents", {
            "service_name": "payment-service",
            "query": "timeout",
        })
        assert prev.status == "Success"
        assert prev.result["total_results"] > 0

    def test_all_14_tools_execute_successfully(self):
        """Verify every registered tool can execute without errors."""
        tool_args = {
            "get_metrics": {"service_name": "payment-service"},
            "search_logs": {"service_name": "payment-service"},
            "get_error_rate": {"service_name": "payment-service"},
            "get_latency": {"service_name": "payment-service"},
            "get_recent_deployments": {"service_name": "payment-service"},
            "get_deployment_details": {"deployment_id": "deploy-pay-005"},
            "compare_deployments": {
                "service_name": "payment-service",
                "version_a": "v2.5.0",
                "version_b": "v2.5.1",
            },
            "get_recent_commits": {"service_name": "payment-service"},
            "get_commit_details": {"sha": "a1b2c3d4e5f6"},
            "search_code_changes": {"service_name": "payment-service", "query": "payment"},
            "search_previous_incidents": {"service_name": "payment-service"},
            "get_service_health": {"service_name": "payment-service"},
            "get_service_dependencies": {"service_name": "payment-service"},
            "get_database_status": {"database_name": "payment-db"},
        }
        for tool_name, args in tool_args.items():
            result = self.registry.execute(tool_name, args)
            assert result.status == "Success", f"Tool '{tool_name}' failed: {result.result}"
            assert result.execution_time_ms >= 0
