"""
Simulated Cache Invalidation Action
"""
from typing import Any, Dict, List
from app.remediation.base import BaseRemediationAction, RemediationResult
from app.remediation.exceptions import RemediationParameterError


class ClearCacheAction(BaseRemediationAction):
    """
    Simulates clearing an application or distributed caching tier.
    """

    @property
    def action_name(self) -> str:
        return "clear_cache"

    @property
    def default_risk_level(self) -> str:
        return "LOW"

    @property
    def description(self) -> str:
        return "Simulates flushing or invalidating keys in a service cache cluster."

    @property
    def required_parameters(self) -> List[str]:
        return ["service"]

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        if not isinstance(parameters, dict):
            raise RemediationParameterError("Parameters must be a JSON object dictionary.")
        service = parameters.get("service")
        if not service or not isinstance(service, str) or not service.strip():
            raise RemediationParameterError("Missing or empty required parameter: 'service'.")
        cache_type = parameters.get("cache_type", "redis")
        if not isinstance(cache_type, str):
            raise RemediationParameterError("'cache_type' must be a string (e.g., 'redis', 'memcached', 'application').")

    def execute(self, parameters: Dict[str, Any]) -> RemediationResult:
        self.validate_parameters(parameters)
        service = parameters["service"].strip()
        cache_type = str(parameters.get("cache_type", "redis")).strip()

        output = {
            "status": "success",
            "action": "clear_cache",
            "service": service,
            "cache_type": cache_type,
            "keys_evicted": 1250,
            "message": f"Simulated cache clearance completed for '{service}' ({cache_type}).",
        }
        return RemediationResult(
            status="success",
            action=self.action_name,
            output=output,
            message=output["message"],
        )
