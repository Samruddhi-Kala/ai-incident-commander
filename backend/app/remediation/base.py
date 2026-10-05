"""
Base Remediation Action Abstraction

Defines the contract for simulated, safe remediation actions.
Guarantees deterministic execution, parameter validation, and zero side-effects.
Strictly prohibited: subprocess, shell commands, eval, exec, real infrastructure calls.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RemediationResult(BaseModel):
    """Container for the output of a simulated remediation execution."""
    status: str = Field(default="success", description="Outcome status: success or error")
    action: str = Field(..., description="Action name executed")
    output: Dict[str, Any] = Field(default_factory=dict, description="Structured simulation output")
    message: str = Field(..., description="Human-readable result summary")
    error: Optional[str] = Field(default=None, description="Error detail if status is error")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp",
    )


class BaseRemediationAction(ABC):
    """
    Abstract base class for simulated remediation actions.
    Every registered action must implement validation and simulated execution.
    """

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Unique identifier for this action (e.g., 'restart_service')."""
        ...

    @property
    @abstractmethod
    def default_risk_level(self) -> str:
        """Default risk level ('LOW', 'MEDIUM', 'HIGH')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this action simulates."""
        ...

    @property
    @abstractmethod
    def required_parameters(self) -> List[str]:
        """List of required parameter keys."""
        ...

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate incoming parameters against action requirements.
        Raises RemediationParameterError if required keys are missing or invalid.
        """
        ...

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> RemediationResult:
        """
        Execute the simulated remediation action.
        Must be deterministic, simulated, and safe.
        No real infrastructure mutation, no subprocess, no shell.
        """
        ...
