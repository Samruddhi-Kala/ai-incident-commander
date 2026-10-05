"""
Remediation Action Executor

Safely executes approved simulated remediation actions.
Enforces:
- Action must have status APPROVED before execution.
- Action must be registered in RemediationRegistry.
- Parameters must conform to the action's schema.
- All operations are simulated with zero infrastructure side effects.
"""
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.remediation.base import RemediationResult
from app.remediation.registry import RemediationRegistry, remediation_registry
from app.remediation.exceptions import (
    RemediationStateError,
    InvalidActionTypeError,
    RemediationParameterError,
    RemediationExecutionError,
)
from app.schemas.remediation import RemediationStatus, RemediationExecutionResult
from app.core.logging import logger


class RemediationExecutor:
    """
    Executor for approved remediation actions.
    Guarantees safety constraints and failure containment.
    """

    def __init__(self, registry: Optional[RemediationRegistry] = None):
        self.registry = registry or remediation_registry

    def execute(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        approval_status: str,
    ) -> RemediationExecutionResult:
        """
        Execute an approved remediation action safely.

        Args:
            action_name: Registered action identifier.
            parameters: Action parameters dictionary.
            approval_status: Current lifecycle state of the action.

        Returns:
            RemediationExecutionResult containing outcome, output, timestamps, and latency.

        Raises:
            RemediationStateError: If action is not in APPROVED state.
            InvalidActionTypeError: If action type is unknown/unregistered.
            RemediationParameterError: If parameters are invalid.
            RemediationExecutionError: If simulation execution fails.
        """
        started_at = datetime.now(timezone.utc)
        start_mono = time.monotonic()

        # 1. Enforce approval guard
        if approval_status != RemediationStatus.APPROVED.value:
            raise RemediationStateError(
                f"Cannot execute remediation action with status '{approval_status}'. "
                f"Only APPROVED actions may be executed."
            )

        # 2. Validate action registration
        action_adapter = self.registry.get(action_name)
        if not action_adapter:
            raise InvalidActionTypeError(
                f"Unknown remediation action type '{action_name}'. "
                f"Only registered remediation actions can be executed."
            )

        # 3. Validate parameters
        action_adapter.validate_parameters(parameters)

        # 4. Safe execution
        try:
            result: RemediationResult = action_adapter.execute(parameters)
            elapsed_ms = int((time.monotonic() - start_mono) * 1000)
            completed_at = datetime.now(timezone.utc)

            logger.info(
                f"Executed simulated remediation '{action_name}' in {elapsed_ms}ms (status={result.status})"
            )

            return RemediationExecutionResult(
                status=RemediationStatus.COMPLETED.value,
                action=action_name,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=elapsed_ms,
                output=result.output,
                error=None,
                failure_reason=None,
            )

        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start_mono) * 1000)
            completed_at = datetime.now(timezone.utc)
            error_msg = str(exc)
            logger.error(f"Remediation execution failed for '{action_name}': {error_msg}")

            return RemediationExecutionResult(
                status=RemediationStatus.FAILED.value,
                action=action_name,
                started_at=started_at,
                completed_at=completed_at,
                execution_time_ms=elapsed_ms,
                output=None,
                error=error_msg,
                failure_reason=f"Simulation failure: {error_msg}",
            )
