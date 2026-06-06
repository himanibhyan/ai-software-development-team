from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(
        self,
        entity: str = "Resource",
        entity_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        message = f"{entity} not found"
        if entity_id:
            message += f": {entity_id}"
        super().__init__(message=message, status_code=404, details=details)


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=422, details=details)


class AuthenticationException(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationException(AppException):
    def __init__(
        self,
        message: str = "Forbidden",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=403, details=details)


class AgentException(AppException):
    def __init__(
        self,
        agent_type: str,
        message: str = "Agent execution failed",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=f"[{agent_type}] {message}",
            status_code=500,
            details={"agent_type": agent_type, **(details or {})},
        )


class LLMException(AppException):
    def __init__(
        self,
        message: str = "LLM service error",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=502, details=details)


class RateLimitException(AppException):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=429, details=details)
