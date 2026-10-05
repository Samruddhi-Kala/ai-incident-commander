"""
Incident History Tool Adapter (Simulated V1)

Provides simulated diagnostic tools for searching historical incidents
to identify recurring failure patterns and past resolutions.
Tools: search_previous_incidents
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter


# ---------------------------------------------------------------------------
# Simulated historical incidents
# ---------------------------------------------------------------------------

_HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-2025-08-01",
        "title": "Payment Service Timeout During Peak Traffic",
        "service_name": "payment-service",
        "severity": "SEV-1",
        "status": "Resolved",
        "root_cause": "Database connection pool exhaustion during peak traffic. Pool size was set to 10 and could not handle concurrent requests.",
        "resolution": "Increased connection pool size from 10 to 30 and added connection pool monitoring alerts.",
        "duration_minutes": 47,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
        "resolved_at": (datetime.now(timezone.utc) - timedelta(days=60) + timedelta(minutes=47)).isoformat(),
        "tags": ["timeout", "database", "connection-pool", "payment"],
        "postmortem_url": "/postmortems/INC-2025-08-01",
    },
    {
        "incident_id": "INC-2025-07-15",
        "title": "Payment Gateway Integration Failure After SDK Upgrade",
        "service_name": "payment-service",
        "severity": "SEV-2",
        "status": "Resolved",
        "root_cause": "Breaking API change in payment-sdk v3.0.0 caused null responses from payment processor.",
        "resolution": "Rolled back payment-sdk to v2.8.0, added null response handling, then re-upgraded with compatibility fixes.",
        "duration_minutes": 92,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=75)).isoformat(),
        "resolved_at": (datetime.now(timezone.utc) - timedelta(days=75) + timedelta(minutes=92)).isoformat(),
        "tags": ["payment", "sdk-upgrade", "null-response", "breaking-change"],
        "postmortem_url": "/postmortems/INC-2025-07-15",
    },
    {
        "incident_id": "INC-2025-06-20",
        "title": "Auth Service Token Validation Timeout",
        "service_name": "auth-service",
        "severity": "SEV-2",
        "status": "Resolved",
        "root_cause": "JWT token validation was making synchronous calls to expired certificate endpoint, causing cascading timeouts.",
        "resolution": "Implemented certificate caching with 1-hour TTL and async validation fallback.",
        "duration_minutes": 35,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=105)).isoformat(),
        "resolved_at": (datetime.now(timezone.utc) - timedelta(days=105) + timedelta(minutes=35)).isoformat(),
        "tags": ["auth", "timeout", "jwt", "certificate"],
        "postmortem_url": "/postmortems/INC-2025-06-20",
    },
    {
        "incident_id": "INC-2025-05-10",
        "title": "Gateway Service Rate Limiter Misconfiguration",
        "service_name": "gateway-service",
        "severity": "SEV-3",
        "status": "Resolved",
        "root_cause": "Rate limiter was configured with per-IP limits instead of per-user limits, blocking legitimate API consumers behind shared NAT.",
        "resolution": "Updated rate limiter to use API key-based bucketing instead of IP-based.",
        "duration_minutes": 120,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=140)).isoformat(),
        "resolved_at": (datetime.now(timezone.utc) - timedelta(days=140) + timedelta(minutes=120)).isoformat(),
        "tags": ["gateway", "rate-limiting", "configuration"],
        "postmortem_url": "/postmortems/INC-2025-05-10",
    },
    {
        "incident_id": "INC-2025-04-22",
        "title": "Database Failover Cascading Failure",
        "service_name": "payment-service",
        "severity": "SEV-1",
        "status": "Resolved",
        "root_cause": "Primary database failover triggered connection pool reset across all services. Services without connection retry logic experienced extended outages.",
        "resolution": "Added connection retry with exponential backoff to all database clients. Implemented circuit breaker for database connections.",
        "duration_minutes": 65,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=160)).isoformat(),
        "resolved_at": (datetime.now(timezone.utc) - timedelta(days=160) + timedelta(minutes=65)).isoformat(),
        "tags": ["database", "failover", "connection-pool", "circuit-breaker", "payment"],
        "postmortem_url": "/postmortems/INC-2025-04-22",
    },
]


class IncidentHistoryAdapter(BaseToolAdapter):
    """
    Simulated Incident History adapter for searching past incidents
    to find recurring patterns and proven resolutions.
    """

    @property
    def domain(self) -> str:
        return "incident_history"

    @property
    def tools(self) -> List[str]:
        return ["search_previous_incidents"]

    def search_previous_incidents(
        self,
        query: Optional[str] = None,
        service_name: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search historical incidents for pattern matching and lessons learned.

        Args:
            query: Free-text search across incident titles, root causes, and tags.
            service_name: Filter by affected service name.
            severity: Filter by severity level (SEV-1, SEV-2, SEV-3, SEV-4).
            limit: Maximum number of results.

        Returns:
            Dict with matching historical incidents, relevance scoring,
            and pattern analysis.
        """
        results = _HISTORICAL_INCIDENTS.copy()

        # Apply filters
        if service_name:
            results = [inc for inc in results if inc["service_name"] == service_name]

        if severity:
            results = [inc for inc in results if inc["severity"] == severity]

        if query:
            query_lower = query.lower()
            scored_results = []
            for inc in results:
                score = 0.0
                # Check title
                if query_lower in inc["title"].lower():
                    score += 0.4
                # Check root cause
                if query_lower in inc["root_cause"].lower():
                    score += 0.3
                # Check tags
                for tag in inc["tags"]:
                    if query_lower in tag.lower():
                        score += 0.15
                # Check resolution
                if query_lower in inc["resolution"].lower():
                    score += 0.15

                if score > 0:
                    scored_results.append({
                        **inc,
                        "relevance_score": round(min(score, 1.0), 2),
                    })

            # Sort by relevance
            scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            results = scored_results
        else:
            # No query — return all with default score
            results = [{**inc, "relevance_score": 0.5} for inc in results]

        truncated = results[:limit]

        # Pattern analysis summary
        patterns = []
        if service_name:
            service_incidents = [i for i in _HISTORICAL_INCIDENTS if i["service_name"] == service_name]
            if len(service_incidents) >= 2:
                # Collect all tags across historical incidents
                all_tags = []
                for inc in service_incidents:
                    all_tags.extend(inc["tags"])
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                recurring_tags = [tag for tag, count in tag_counts.items() if count >= 2]
                if recurring_tags:
                    patterns.append({
                        "pattern": "recurring_failure_tags",
                        "tags": recurring_tags,
                        "message": f"Service '{service_name}' has recurring incidents with tags: {', '.join(recurring_tags)}",
                    })

        return {
            "query": query,
            "filters": {
                "service_name": service_name,
                "severity": severity,
            },
            "total_results": len(truncated),
            "incidents": truncated,
            "patterns": patterns,
        }
