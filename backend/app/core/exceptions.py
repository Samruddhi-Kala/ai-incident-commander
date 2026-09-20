from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AppException(Exception):
    """
    Base application exception.
    """
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionException(AppException):
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class RedisConnectionException(AppException):
    def __init__(self, message: str = "Redis connection failed"):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ServiceNotFoundError(NotFoundException):
    def __init__(self, message: str = "Service not found"):
        super().__init__(message=message)


class IncidentNotFoundError(NotFoundException):
    def __init__(self, message: str = "Incident not found"):
        super().__init__(message=message)


class DuplicateServiceError(AppException):
    def __init__(self, message: str = "Service already exists"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class InvalidIncidentStateError(ValidationException):
    def __init__(self, message: str = "Invalid incident status or severity transition"):
        super().__init__(message=message)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception handlers with the FastAPI application instance.
    """
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.error(f"AppException on {request.method} {request.url.path}: {exc.message}")
        payload = {
            "status": "error",
            "message": exc.message,
            "detail": exc.message,
        }
        if exc.details:
            payload["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=payload)
