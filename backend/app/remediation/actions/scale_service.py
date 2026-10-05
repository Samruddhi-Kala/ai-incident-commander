"""
Simulated Service Scaling Action
"""
from typing import Any, Dict, List
from app.remediation.base import BaseRemediationAction, RemediationResult
from app.remediation.exceptions import RemediationParameterError


class ScaleServiceAction(BaseRemediationAction):
    """
    Simulates scaling the horizontal replica count for a service deployment.
    """

    @property
    def action_name(self) -> str:
        return "scale_service"

    @property
    def default_risk_level(self) -> str:
        return "MEDIUM"

    @property
    def description(self) -> str:
        return "Simulates scaling the replica capacity of a service deployment."

    @property
    def required_parameters(self) -> List[str]:
        return ["service", "replicas"]

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        if not isinstance(parameters, dict):
            raise RemediationParameterError("Parameters must be a JSON object dictionary.")
        service = parameters.get("service")
        if not service or not isinstance(service, str) or not service.strip():
            raise RemediationParameterError("Missing or empty required parameter: 'service'.")
        replicas = parameters.get("replicas")
        if replicas is None or not isinstance(replicas, int) or replicas <= 0 or replicas > 100:
            raise RemediationParameterError("Parameter 'replicas' must be an integer between 1 and 100.")

    def execute(self, parameters: Dict[str, Any]) -> RemediationResult:
        self.validate_parameters(parameters)
        service = parameters["service"].strip()
        replicas = int(parameters["replicas"])

        output = {
            "status": "success",
            "action": "scale_service",
            "service": service,
            "replicas": replicas,
            "message": f"Simulated scaling service '{service}' to {replicas} replicas completed.",
        }
        return RemediationResult(
            status="success",
            action=self.action_name,
            output=output,
            message=output["message"],
        )
