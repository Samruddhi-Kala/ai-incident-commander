"""
Infrastructure Tool Adapter (Simulated V1)

Provides simulated diagnostic tools for querying service health,
service dependencies, and database status.
Tools: get_service_health, get_service_dependencies, get_database_status
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter


# ---------------------------------------------------------------------------
# Simulated infrastructure state
# ---------------------------------------------------------------------------

_SERVICE_HEALTH = {
    "payment-service": {
        "service_name": "payment-service",
        "status": "degraded",
        "healthy_replicas": 1,
        "total_replicas": 3,
        "cpu_usage_percent": 78.5,
        "memory_usage_percent": 92.3,
        "uptime_seconds": 1500,
        "last_restart": (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat(),
        "restart_count_24h": 4,
        "pods": [
            {
                "name": "payment-service-7d8f9c-abc12",
                "status": "Running",
                "ready": True,
                "restarts": 0,
                "cpu": "250m",
                "memory": "380Mi/512Mi",
            },
            {
                "name": "payment-service-7d8f9c-def34",
                "status": "CrashLoopBackOff",
                "ready": False,
                "restarts": 3,
                "cpu": "50m",
                "memory": "490Mi/512Mi",
            },
            {
                "name": "payment-service-7d8f9c-ghi56",
                "status": "OOMKilled",
                "ready": False,
                "restarts": 1,
                "cpu": "0m",
                "memory": "512Mi/512Mi",
            },
        ],
        "alerts_active": [
            {
                "alert_name": "HighErrorRate",
                "severity": "critical",
                "message": "Error rate exceeds 10% threshold",
                "firing_since": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
            },
            {
                "alert_name": "PodCrashLooping",
                "severity": "warning",
                "message": "Pod payment-service-7d8f9c-def34 is crash looping",
                "firing_since": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
            },
        ],
    },
    "auth-service": {
        "service_name": "auth-service",
        "status": "healthy",
        "healthy_replicas": 3,
        "total_replicas": 3,
        "cpu_usage_percent": 25.0,
        "memory_usage_percent": 45.2,
        "uptime_seconds": 86400,
        "last_restart": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "restart_count_24h": 0,
        "pods": [
            {"name": "auth-service-5a6b7c-xyz11", "status": "Running", "ready": True, "restarts": 0, "cpu": "100m", "memory": "200Mi/512Mi"},
            {"name": "auth-service-5a6b7c-xyz22", "status": "Running", "ready": True, "restarts": 0, "cpu": "95m", "memory": "190Mi/512Mi"},
            {"name": "auth-service-5a6b7c-xyz33", "status": "Running", "ready": True, "restarts": 0, "cpu": "105m", "memory": "210Mi/512Mi"},
        ],
        "alerts_active": [],
    },
    "gateway-service": {
        "service_name": "gateway-service",
        "status": "healthy",
        "healthy_replicas": 2,
        "total_replicas": 2,
        "cpu_usage_percent": 35.0,
        "memory_usage_percent": 50.1,
        "uptime_seconds": 43200,
        "last_restart": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
        "restart_count_24h": 0,
        "pods": [
            {"name": "gateway-service-8x9y0z-aaa11", "status": "Running", "ready": True, "restarts": 0, "cpu": "150m", "memory": "250Mi/512Mi"},
            {"name": "gateway-service-8x9y0z-bbb22", "status": "Running", "ready": True, "restarts": 0, "cpu": "140m", "memory": "245Mi/512Mi"},
        ],
        "alerts_active": [],
    },
    "user-service": {
        "service_name": "user-service",
        "status": "healthy",
        "healthy_replicas": 2,
        "total_replicas": 2,
        "cpu_usage_percent": 15.0,
        "memory_usage_percent": 30.5,
        "uptime_seconds": 172800,
        "last_restart": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "restart_count_24h": 0,
        "pods": [
            {"name": "user-service-4m5n6o-ccc11", "status": "Running", "ready": True, "restarts": 0, "cpu": "80m", "memory": "150Mi/512Mi"},
            {"name": "user-service-4m5n6o-ddd22", "status": "Running", "ready": True, "restarts": 0, "cpu": "75m", "memory": "145Mi/512Mi"},
        ],
        "alerts_active": [],
    },
}


_SERVICE_DEPENDENCIES = {
    "payment-service": {
        "service_name": "payment-service",
        "upstream": [
            {"name": "gateway-service", "protocol": "HTTP/gRPC", "health": "healthy"},
        ],
        "downstream": [
            {"name": "payment-db", "type": "PostgreSQL", "health": "healthy"},
            {"name": "payment-gateway-external", "type": "External API", "health": "degraded"},
            {"name": "redis-cache", "type": "Redis", "health": "healthy"},
            {"name": "auth-service", "type": "Internal Service", "health": "healthy"},
        ],
        "dependency_graph": {
            "gateway-service": ["payment-service"],
            "payment-service": ["payment-db", "payment-gateway-external", "redis-cache", "auth-service"],
        },
    },
    "auth-service": {
        "service_name": "auth-service",
        "upstream": [
            {"name": "gateway-service", "protocol": "HTTP", "health": "healthy"},
            {"name": "payment-service", "protocol": "HTTP", "health": "degraded"},
            {"name": "user-service", "protocol": "HTTP", "health": "healthy"},
        ],
        "downstream": [
            {"name": "auth-db", "type": "PostgreSQL", "health": "healthy"},
            {"name": "redis-sessions", "type": "Redis", "health": "healthy"},
        ],
        "dependency_graph": {
            "gateway-service": ["auth-service"],
            "payment-service": ["auth-service"],
            "user-service": ["auth-service"],
            "auth-service": ["auth-db", "redis-sessions"],
        },
    },
    "gateway-service": {
        "service_name": "gateway-service",
        "upstream": [
            {"name": "load-balancer", "protocol": "HTTP", "health": "healthy"},
        ],
        "downstream": [
            {"name": "payment-service", "type": "Internal Service", "health": "degraded"},
            {"name": "auth-service", "type": "Internal Service", "health": "healthy"},
            {"name": "user-service", "type": "Internal Service", "health": "healthy"},
        ],
        "dependency_graph": {
            "load-balancer": ["gateway-service"],
            "gateway-service": ["payment-service", "auth-service", "user-service"],
        },
    },
}


_DATABASE_STATUS = {
    "payment-db": {
        "database_name": "payment-db",
        "engine": "PostgreSQL 16.2",
        "status": "healthy",
        "connections_active": 48,
        "connections_max": 50,
        "connections_idle": 2,
        "connection_utilization_percent": 96.0,
        "disk_usage_percent": 45.2,
        "replication_lag_ms": 5,
        "slow_queries_last_hour": 12,
        "deadlocks_last_hour": 0,
        "avg_query_time_ms": 85.3,
        "warnings": [
            "Connection pool near capacity (48/50 active connections)",
            "12 slow queries detected in last hour (threshold: >500ms)",
        ],
    },
    "auth-db": {
        "database_name": "auth-db",
        "engine": "PostgreSQL 16.2",
        "status": "healthy",
        "connections_active": 15,
        "connections_max": 50,
        "connections_idle": 35,
        "connection_utilization_percent": 30.0,
        "disk_usage_percent": 22.8,
        "replication_lag_ms": 2,
        "slow_queries_last_hour": 0,
        "deadlocks_last_hour": 0,
        "avg_query_time_ms": 12.5,
        "warnings": [],
    },
    "redis-cache": {
        "database_name": "redis-cache",
        "engine": "Redis 7.2",
        "status": "healthy",
        "connections_active": 20,
        "connections_max": 100,
        "connections_idle": 80,
        "connection_utilization_percent": 20.0,
        "memory_usage_percent": 35.0,
        "hit_rate_percent": 94.5,
        "evictions_last_hour": 0,
        "warnings": [],
    },
}


class InfrastructureAdapter(BaseToolAdapter):
    """
    Simulated Infrastructure adapter providing service health monitoring,
    dependency mapping, and database status queries.
    """

    @property
    def domain(self) -> str:
        return "infrastructure"

    @property
    def tools(self) -> List[str]:
        return ["get_service_health", "get_service_dependencies", "get_database_status"]

    def get_service_health(
        self,
        service_name: str,
    ) -> Dict[str, Any]:
        """
        Get comprehensive health status for a service including pod states,
        resource usage, and active alerts.

        Args:
            service_name: Target service name.

        Returns:
            Dict with health status, replica counts, resource usage,
            pod details, and active alerts.
        """
        health = _SERVICE_HEALTH.get(service_name)
        if health:
            return health

        # Default health for unknown services
        return {
            "service_name": service_name,
            "status": "unknown",
            "healthy_replicas": 0,
            "total_replicas": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "uptime_seconds": 0,
            "last_restart": None,
            "restart_count_24h": 0,
            "pods": [],
            "alerts_active": [],
            "warning": f"Service '{service_name}' not found in infrastructure registry",
        }

    def get_service_dependencies(
        self,
        service_name: str,
    ) -> Dict[str, Any]:
        """
        Get upstream and downstream service dependencies with health status.

        Args:
            service_name: Target service name.

        Returns:
            Dict with upstream/downstream dependencies, health status,
            and dependency graph.
        """
        deps = _SERVICE_DEPENDENCIES.get(service_name)
        if deps:
            return deps

        return {
            "service_name": service_name,
            "upstream": [],
            "downstream": [],
            "dependency_graph": {},
            "warning": f"No dependency information available for '{service_name}'",
        }

    def get_database_status(
        self,
        database_name: str,
    ) -> Dict[str, Any]:
        """
        Get database health, connection pool stats, and performance metrics.

        Args:
            database_name: Target database name.

        Returns:
            Dict with database status, connection stats, performance
            metrics, and any warnings.
        """
        status = _DATABASE_STATUS.get(database_name)
        if status:
            return status

        return {
            "database_name": database_name,
            "status": "unknown",
            "warning": f"Database '{database_name}' not found in infrastructure registry",
        }
