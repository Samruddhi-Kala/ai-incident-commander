"""
Remediation Exceptions

Domain-specific exceptions for remediation proposal, approval, and execution lifecycles.
Inherit from AppException to ensure consistent HTTP status mapping and JSON responses.
"""
from typing import Any, Dict, Optional
from fastapi import status
from app.core.exceptions import AppException, NotFoundException, ValidationException


class RemediationError(AppException):
    """Base exception for all remediation errors."""
    def __init__(
        self,
        message: str = "Remediation error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message=message, status_code=status_code, details=details)


class RemediationNotFoundError(NotFoundException):
    """Raised when a specified remediation action ID does not exist."""
    def __init__(self, message: str = "Remediation action not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message)
        self.details = details or {}


class RemediationInvestigationNotFoundError(NotFoundException):
    """Raised when the investigation associated with a remediation does not exist."""
    def __init__(self, message: str = "Associated investigation not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message)
        self.details = details or {}


class InvalidActionTypeError(ValidationException):
    """Raised when attempting to propose or execute an unregistered remediation action."""
    def __init__(self, message: str = "Invalid or unregistered remediation action type", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class RemediationParameterError(ValidationException):
    """Raised when remediation parameters fail schema validation or are malformed."""
    def __init__(self, message: str = "Malformed or missing remediation parameters", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class RemediationStateError(AppException):
    """Raised when a lifecycle state transition is prohibited."""
    def __init__(self, message: str = "Invalid remediation state transition", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class RemediationApprovalError(AppException):
    """Raised when an unauthorized actor attempts approval (e.g., AI self-approval)."""
    def __init__(self, message: str = "Remediation authorization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class RemediationExecutionError(RemediationError):
    """Raised when execution of an approved remediation fails."""
    def __init__(self, message: str = "Remediation execution failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )
