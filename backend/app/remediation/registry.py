"""
Remediation Action Registry

Manages catalog of registered, safe simulated remediation actions.
Prevents execution of unauthorized or unknown actions.
"""
from typing import Any, Dict, List, Optional
from app.remediation.base import BaseRemediationAction
from app.remediation.actions import (
    RestartServiceAction,
    RollbackDeploymentAction,
    ScaleServiceAction,
    ClearCacheAction,
)
from app.core.logging import logger


class RemediationRegistry:
    """
    Central registry of approved, simulated remediation action adapters.
    Ensures only authorized action types can be proposed or executed.
    """

    def __init__(self) -> None:
        self._actions: Dict[str, BaseRemediationAction] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register the built-in simulated actions."""
        self.register_action(RestartServiceAction())
        self.register_action(RollbackDeploymentAction())
        self.register_action(ScaleServiceAction())
        self.register_action(ClearCacheAction())

    def register_action(self, action: BaseRemediationAction) -> None:
        """Register an action adapter by its action_name."""
        self._actions[action.action_name] = action
        logger.info(f"Registered remediation action: '{action.action_name}' (risk: {action.default_risk_level})")

    def get(self, action_name: str) -> Optional[BaseRemediationAction]:
        """Retrieve an action adapter by name."""
        return self._actions.get(action_name)

    def is_registered(self, action_name: str) -> bool:
        """Check if an action type is registered."""
        return action_name in self._actions

    def list_actions(self) -> List[Dict[str, Any]]:
        """List metadata for all registered actions."""
        return [
            {
                "action_name": a.action_name,
                "description": a.description,
                "default_risk_level": a.default_risk_level,
                "required_parameters": a.required_parameters,
            }
            for a in self._actions.values()
        ]


# Singleton default registry
remediation_registry = RemediationRegistry()
