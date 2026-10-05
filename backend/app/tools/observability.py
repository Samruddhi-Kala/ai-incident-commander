"""
Observability Tool Adapter (Simulated V1)

Provides simulated diagnostic tools for metrics, logs, error rates, and latency.
Returns deterministic mock data keyed by service_name for reproducible testing.
Tools: get_metrics, search_logs, get_error_rate, get_latency
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from app.tools.base import BaseToolAdapter


# ---------------------------------------------------------------------------
# Simulated data generators — deterministic per service_name
# ---------------------------------------------------------------------------

def _sim_metrics(service_name: str, metric_name: str, minutes: int = 30) -> Dict[str, Any]:
    """Generate simulated time-series metric data points."""
    base = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    data_points = []
    for i in range(minutes):
        ts = base + timedelta(minutes=i)
        # Simulate a spike at the 20-minute mark for payment-service
        if service_name == "payment-service" and metric_name == "error_rate" and 18 <= i <= 25:
            value = 12.5 + (i - 18) * 3.2
        elif service_name == "payment-service" and metric_name == "latency_p99" and 18 <= i <= 25:
            value = 850 + (i - 18) * 200
        else:
            value = round(0.5 + (hash(f"{service_name}{metric_name}{i}") % 100) / 100.0, 2)
        data_points.append({
            "timestamp": ts.isoformat(),
            "value": round(value, 2),
        })
    return {
        "service_name": service_name,
        "metric_name": metric_name,
        "unit": _metric_unit(metric_name),
        "data_points": data_points,
        "aggregation": "1m",
    }


def _metric_unit(metric_name: str) -> str:
    units = {
        "error_rate": "percent",
        "latency_p99": "ms",
        "latency_p50": "ms",
        "cpu_usage": "percent",
        "memory_usage": "percent",
        "request_rate": "req/s",
        "throughput": "req/s",
    }
    return units.get(metric_name, "units")


def _sim_logs(
    service_name: str,
    level: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Generate simulated structured log entries."""
    base_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    all_logs = [
        {
            "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": f"Connection timeout to downstream database after 30s",
            "trace_id": "trace-abc-001",
            "span_id": "span-def-001",
        },
        {
            "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": f"HTTP 503 from gateway-service: upstream connect error",
            "trace_id": "trace-abc-002",
            "span_id": "span-def-002",
        },
        {
            "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
            "level": "WARN",
            "service": service_name,
            "message": "Connection pool exhausted — waiting for available connection",
            "trace_id": "trace-abc-003",
            "span_id": "span-def-003",
        },
        {
            "timestamp": (base_time + timedelta(minutes=7)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": f"Failed to process payment: timeout after 30000ms",
            "trace_id": "trace-abc-004",
            "span_id": "span-def-004",
        },
        {
            "timestamp": (base_time + timedelta(minutes=8)).isoformat(),
            "level": "INFO",
            "service": service_name,
            "message": "Health check passed — pod is ready",
            "trace_id": "trace-abc-005",
            "span_id": "span-def-005",
        },
        {
            "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": "CircuitBreaker tripped for payment-gateway downstream call",
            "trace_id": "trace-abc-006",
            "span_id": "span-def-006",
        },
        {
            "timestamp": (base_time + timedelta(minutes=12)).isoformat(),
            "level": "WARN",
            "service": service_name,
            "message": "Retrying failed request (attempt 3/3) to payment-processor",
            "trace_id": "trace-abc-007",
            "span_id": "span-def-007",
        },
        {
            "timestamp": (base_time + timedelta(minutes=15)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": "NullPointerException in PaymentHandler.processTransaction line 142",
            "trace_id": "trace-abc-008",
            "span_id": "span-def-008",
        },
        {
            "timestamp": (base_time + timedelta(minutes=18)).isoformat(),
            "level": "INFO",
            "service": service_name,
            "message": "Deployment v2.5.1 started rolling out",
            "trace_id": "trace-abc-009",
            "span_id": "span-def-009",
        },
        {
            "timestamp": (base_time + timedelta(minutes=20)).isoformat(),
            "level": "ERROR",
            "service": service_name,
            "message": "OOM killed: container exceeded memory limit of 512Mi",
            "trace_id": "trace-abc-010",
            "span_id": "span-def-010",
        },
    ]

    filtered = all_logs
    if level:
        filtered = [log for log in filtered if log["level"] == level.upper()]
    if query:
        filtered = [log for log in filtered if query.lower() in log["message"].lower()]

    return filtered[:limit]


class ObservabilityAdapter(BaseToolAdapter):
    """
    Simulated Observability adapter providing metrics, logs, error rates,
    and latency queries. Returns deterministic mock telemetry data.
    """

    @property
    def domain(self) -> str:
        return "observability"

    @property
    def tools(self) -> List[str]:
        return ["get_metrics", "search_logs", "get_error_rate", "get_latency"]

    def get_metrics(
        self,
        service_name: str,
        metric_name: str = "error_rate",
        minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Retrieve time-series metrics for a service.

        Args:
            service_name: Target service name.
            metric_name: Metric to query (error_rate, latency_p99, cpu_usage, etc.).
            minutes: Lookback window in minutes.

        Returns:
            Dict with metric data points, unit, and aggregation interval.
        """
        return _sim_metrics(service_name, metric_name, minutes)

    def search_logs(
        self,
        service_name: str,
        level: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search structured log entries for a service.

        Args:
            service_name: Target service name.
            level: Filter by log level (ERROR, WARN, INFO, DEBUG).
            query: Free-text search within log messages.
            limit: Maximum number of log entries to return.

        Returns:
            Dict with matching log entries and count.
        """
        logs = _sim_logs(service_name, level, query, limit)
        return {
            "service_name": service_name,
            "total_results": len(logs),
            "filters": {"level": level, "query": query},
            "logs": logs,
        }

    def get_error_rate(
        self,
        service_name: str,
        minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Get the current and recent error rate for a service.

        Args:
            service_name: Target service name.
            minutes: Lookback window in minutes.

        Returns:
            Dict with current error rate, average, peak, and trend.
        """
        # Simulated error rates per service
        simulated = {
            "payment-service": {"current": 15.3, "average": 2.1, "peak": 28.7, "trend": "increasing"},
            "auth-service": {"current": 0.5, "average": 0.3, "peak": 1.2, "trend": "stable"},
            "gateway-service": {"current": 3.2, "average": 1.0, "peak": 5.8, "trend": "increasing"},
            "user-service": {"current": 0.1, "average": 0.1, "peak": 0.3, "trend": "stable"},
        }
        data = simulated.get(service_name, {
            "current": 0.5,
            "average": 0.3,
            "peak": 1.0,
            "trend": "stable",
        })
        return {
            "service_name": service_name,
            "window_minutes": minutes,
            "error_rate_percent": data["current"],
            "average_error_rate_percent": data["average"],
            "peak_error_rate_percent": data["peak"],
            "trend": data["trend"],
            "unit": "percent",
        }

    def get_latency(
        self,
        service_name: str,
        percentile: str = "p99",
        minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Get latency percentile metrics for a service.

        Args:
            service_name: Target service name.
            percentile: Latency percentile (p50, p90, p95, p99).
            minutes: Lookback window in minutes.

        Returns:
            Dict with current latency, baseline, and assessment.
        """
        baselines = {
            "payment-service": {"p50": 45, "p90": 120, "p95": 200, "p99": 350},
            "auth-service": {"p50": 15, "p90": 40, "p95": 60, "p99": 100},
            "gateway-service": {"p50": 10, "p90": 25, "p95": 40, "p99": 70},
            "user-service": {"p50": 20, "p90": 50, "p95": 80, "p99": 130},
        }
        base = baselines.get(service_name, {"p50": 20, "p90": 50, "p95": 80, "p99": 130})
        baseline_val = base.get(percentile, base["p99"])

        # Simulate elevated latency for payment-service
        if service_name == "payment-service":
            current_val = baseline_val * 3.5
        else:
            current_val = baseline_val * 1.1

        return {
            "service_name": service_name,
            "percentile": percentile,
            "window_minutes": minutes,
            "current_ms": round(current_val, 1),
            "baseline_ms": baseline_val,
            "deviation_factor": round(current_val / baseline_val, 2),
            "assessment": "degraded" if current_val > baseline_val * 2 else "normal",
            "unit": "ms",
        }
