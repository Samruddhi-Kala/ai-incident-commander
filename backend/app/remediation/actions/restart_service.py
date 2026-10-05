"""
Simulated Service Restart Action
"""
from typing import Any, Dict, List
from app.remediation.base import BaseRemediationAction, RemediationResult
from app.remediation.exceptions import RemediationParameterError


class RestartServiceAction(BaseRemediationAction):
    """
    Simulates a graceful rolling restart of service instances.
    """

    @property
    def action_name(self) -> str:
        return "restart_service"

    @property
    def default_risk_level(self) -> str:
        return "MEDIUM"

    @property
    def description(self) -> str:
        return "Simulates a graceful rolling restart of the target service instances."

    @property
    def required_parameters(self) -> List[str]:
        return ["service"]

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        if not isinstance(parameters, dict):
            raise RemediationParameterError("Parameters must be a JSON object dictionary.")
        service = parameters.get("service")
        if not service or not isinstance(service, str) or not service.strip():
            raise RemediationParameterError("Missing or empty required parameter: 'service'.")
        grace = parameters.get("grace_period_seconds")
        if grace is not None:
            if not isinstance(grace, (int, float)) or grace < 0:
                raise RemediationParameterError("'grace_period_seconds' must be a non-negative number.")

    def execute(self, parameters: Dict[str, Any]) -> RemediationResult:
        self.validate_parameters(parameters)
        service = parameters["service"].strip()
        grace_period = int(parameters.get("grace_period_seconds", 30))

        output = {
            "status": "success",
            "action": "restart_service",
            "service": service,
            "restarted_instances": 3,
            "grace_period_seconds": grace_period,
            "message": f"Simulated service restart completed for '{service}'.",
        }
        return RemediationResult(
            status="success",
            action=self.action_name,
            output=output,
            message=output["message"],
        )
