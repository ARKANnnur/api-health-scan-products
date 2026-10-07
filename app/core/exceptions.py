from typing import Any


class AppException(Exception):
    """Base exception untuk semua custom error aplikasi."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=404,
            details=details,
        )


class AuthenticationError(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401,
            details=details,
        )


class AuthorizationError(AppException):
    def __init__(
        self,
        message: str = "Not authorized",
        code: str = "AUTHORIZATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=403,
            details=details,
        )


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=422,
            details=details,
        )


class DatabaseError(AppException):
    def __init__(
        self,
        message: str = "Database error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=503,
            details=details,
        )


class ConflictError(AppException):
    def __init__(
        self,
        message: str = "Conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
            details=details,
        )


class RateLimitError(AppException):
    def __init__(
        self,
        message: str = "Too many requests",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="TOO_MANY_REQUESTS",
            message=message,
            status_code=429,
            details=details,
        )


class ExternalServiceError(AppException):
    def __init__(
        self,
        message: str = "External service unavailable",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=message,
            status_code=503,
            details=details,
        )
