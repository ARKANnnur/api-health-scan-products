from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)


def test_app_exception_base() -> None:
    e = AppException("CODE", "msg", status_code=418, details={"k": "v"})
    assert e.code == "CODE"
    assert e.message == "msg"
    assert e.status_code == 418
    assert e.details == {"k": "v"}


def test_resource_not_found() -> None:
    e = ResourceNotFoundError("User not found")
    assert e.status_code == 404
    assert e.code == "RESOURCE_NOT_FOUND"


def test_authentication_error() -> None:
    e = AuthenticationError()
    assert e.status_code == 401
    assert e.code == "AUTHENTICATION_ERROR"


def test_authorization_error() -> None:
    e = AuthorizationError()
    assert e.status_code == 403
    assert e.code == "AUTHORIZATION_ERROR"


def test_validation_error() -> None:
    e = ValidationError()
    assert e.status_code == 422
    assert e.code == "VALIDATION_ERROR"


def test_database_error() -> None:
    e = DatabaseError()
    assert e.status_code == 503
    assert e.code == "DATABASE_ERROR"
