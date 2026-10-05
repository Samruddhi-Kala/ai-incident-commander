"""
Simulated Deployment Rollback Action
"""
from typing import Any, Dict, List
from app.remediation.base import BaseRemediationAction, RemediationResult
from app.remediation.exceptions import RemediationParameterError


class RollbackDeploymentAction(BaseRemediationAction):
    """
    Simulates rolling back a service deployment to a prior stable version.
    """

    @property
    def action_name(self) -> str:
        return "rollback_deployment"

    @property
    def default_risk_level(self) -> str:
        return "HIGH"

    @property
    def description(self) -> str:
        return "Simulates rolling back a service deployment to a prior verified release artifact."

    @property
    def required_parameters(self) -> List[str]:
        return ["service", "target_version"]

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        if not isinstance(parameters, dict):
            raise RemediationParameterError("Parameters must be a JSON object dictionary.")
        service = parameters.get("service")
        if not service or not isinstance(service, str) or not service.strip():
            raise RemediationParameterError("Missing or empty required parameter: 'service'.")
        target_version = parameters.get("target_version")
        if not target_version or not isinstance(target_version, str) or not target_version.strip():
            raise RemediationParameterError("Missing or empty required parameter: 'target_version'.")

    def execute(self, parameters: Dict[str, Any]) -> RemediationResult:
        self.validate_parameters(parameters)
        service = parameters["service"].strip()
        target_version = parameters["target_version"].strip()
        current_version = parameters.get("current_version")

        output = {
            "status": "success",
            "action": "rollback_deployment",
            "service": service,
            "target_version": target_version,
            "current_version": current_version,
            "traffic_shifted_pct": 100,
            "message": f"Simulated deployment rollback completed for '{service}' to version '{target_version}'.",
        }
        return RemediationResult(
            status="success",
            action=self.action_name,
            output=output,
            message=output["message"],
        )
