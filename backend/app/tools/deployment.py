"""
Deployment Tool Adapter (Simulated V1)

Provides simulated diagnostic tools for querying deployment history,
deployment details, and comparing deployments.
Tools: get_recent_deployments, get_deployment_details, compare_deployments
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter


# ---------------------------------------------------------------------------
# Simulated deployment data — deterministic per service_name
# ---------------------------------------------------------------------------

_DEPLOYMENTS = {
    "payment-service": [
        {
            "deployment_id": "deploy-pay-005",
            "service_name": "payment-service",
            "version": "v2.5.1",
            "previous_version": "v2.5.0",
            "status": "completed",
            "deployer": "ci-bot",
            "environment": "production",
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
            "commit_sha": "a1b2c3d4e5f6",
            "changelog": "feat: add new payment processor integration; fix: connection pool sizing",
            "rollback_available": True,
        },
        {
            "deployment_id": "deploy-pay-004",
            "service_name": "payment-service",
            "version": "v2.5.0",
            "previous_version": "v2.4.9",
            "status": "completed",
            "deployer": "engineer-alice",
            "environment": "production",
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(hours=8) + timedelta(minutes=5)).isoformat(),
            "commit_sha": "f6e5d4c3b2a1",
            "changelog": "fix: retry logic for timeout errors",
            "rollback_available": True,
        },
        {
            "deployment_id": "deploy-pay-003",
            "service_name": "payment-service",
            "version": "v2.4.9",
            "previous_version": "v2.4.8",
            "status": "completed",
            "deployer": "engineer-bob",
            "environment": "production",
            "started_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(days=2) + timedelta(minutes=4)).isoformat(),
            "commit_sha": "1a2b3c4d5e6f",
            "changelog": "chore: dependency update for payment-sdk",
            "rollback_available": True,
        },
    ],
    "auth-service": [
        {
            "deployment_id": "deploy-auth-012",
            "service_name": "auth-service",
            "version": "v3.1.0",
            "previous_version": "v3.0.9",
            "status": "completed",
            "deployer": "ci-bot",
            "environment": "production",
            "started_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(days=1) + timedelta(minutes=3)).isoformat(),
            "commit_sha": "abc123def456",
            "changelog": "feat: add OAuth2 PKCE support",
            "rollback_available": True,
        },
    ],
    "gateway-service": [
        {
            "deployment_id": "deploy-gw-008",
            "service_name": "gateway-service",
            "version": "v1.12.0",
            "previous_version": "v1.11.9",
            "status": "completed",
            "deployer": "engineer-carol",
            "environment": "production",
            "started_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(hours=4) + timedelta(minutes=2)).isoformat(),
            "commit_sha": "789abc012def",
            "changelog": "fix: rate limiting configuration update",
            "rollback_available": True,
        },
    ],
}


def _get_default_deployments(service_name: str) -> List[Dict[str, Any]]:
    """Return default empty deployment list for unknown services."""
    return [{
        "deployment_id": f"deploy-{service_name[:4]}-001",
        "service_name": service_name,
        "version": "v1.0.0",
        "previous_version": "v0.9.9",
        "status": "completed",
        "deployer": "ci-bot",
        "environment": "production",
        "started_at": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
        "completed_at": (datetime.now(timezone.utc) - timedelta(days=7) + timedelta(minutes=3)).isoformat(),
        "commit_sha": "000aaa111bbb",
        "changelog": "initial deployment",
        "rollback_available": False,
    }]


class DeploymentAdapter(BaseToolAdapter):
    """
    Simulated Deployment adapter providing deployment history queries,
    deployment details lookup, and deployment comparison.
    """

    @property
    def domain(self) -> str:
        return "deployment"

    @property
    def tools(self) -> List[str]:
        return ["get_recent_deployments", "get_deployment_details", "compare_deployments"]

    def get_recent_deployments(
        self,
        service_name: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        List recent deployments for a service.

        Args:
            service_name: Target service name.
            limit: Maximum number of deployments to return.

        Returns:
            Dict with deployment records and count.
        """
        deployments = _DEPLOYMENTS.get(service_name, _get_default_deployments(service_name))
        results = deployments[:limit]
        return {
            "service_name": service_name,
            "total_deployments": len(results),
            "deployments": results,
        }

    def get_deployment_details(
        self,
        deployment_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific deployment.

        Args:
            deployment_id: The deployment identifier.

        Returns:
            Dict with full deployment details or error if not found.
        """
        # Search across all services
        for service_deploys in _DEPLOYMENTS.values():
            for deploy in service_deploys:
                if deploy["deployment_id"] == deployment_id:
                    return {
                        **deploy,
                        "health_check_status": "passing",
                        "replicas_updated": 3,
                        "replicas_total": 3,
                        "canary_passed": True,
                    }

        return {
            "error": f"Deployment '{deployment_id}' not found",
            "deployment_id": deployment_id,
        }

    def compare_deployments(
        self,
        service_name: str,
        version_a: str,
        version_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two deployment versions of a service showing config
        and dependency changes.

        Args:
            service_name: Target service name.
            version_a: First version for comparison (older).
            version_b: Second version for comparison (newer).

        Returns:
            Dict with deployment diff summary.
        """
        deployments = _DEPLOYMENTS.get(service_name, [])
        deploy_a = next((d for d in deployments if d["version"] == version_a), None)
        deploy_b = next((d for d in deployments if d["version"] == version_b), None)

        # Simulate meaningful diffs for payment-service v2.5.0 -> v2.5.1
        if service_name == "payment-service" and version_a == "v2.5.0" and version_b == "v2.5.1":
            return {
                "service_name": service_name,
                "version_a": version_a,
                "version_b": version_b,
                "files_changed": 8,
                "lines_added": 142,
                "lines_removed": 37,
                "config_changes": [
                    {
                        "file": "config/database.yml",
                        "change": "connection_pool_size: 20 -> 50",
                        "risk": "MEDIUM",
                    },
                    {
                        "file": "config/payment-gateway.yml",
                        "change": "Added new payment processor endpoint",
                        "risk": "HIGH",
                    },
                ],
                "dependency_changes": [
                    {
                        "package": "payment-sdk",
                        "from_version": "3.2.0",
                        "to_version": "4.0.0",
                        "breaking_change": True,
                    },
                ],
                "environment_variable_changes": [
                    "PAYMENT_PROCESSOR_URL (added)",
                    "CONNECTION_POOL_MAX_SIZE (modified)",
                ],
            }

        return {
            "service_name": service_name,
            "version_a": version_a,
            "version_b": version_b,
            "deploy_a_found": deploy_a is not None,
            "deploy_b_found": deploy_b is not None,
            "files_changed": 3,
            "lines_added": 25,
            "lines_removed": 10,
            "config_changes": [],
            "dependency_changes": [],
            "environment_variable_changes": [],
        }
