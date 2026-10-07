from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ExternalServiceError,
)
from app.features.auth import service
from app.features.auth.schemas import SignInRequest, SignUpRequest

SUPABASE_URL = "https://test.supabase.co"
ADMIN_URL = f"{SUPABASE_URL}/auth/v1/admin/users"
TOKEN_URL = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"


def _mock_response(status_code: int, json_data: dict[str, Any]) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    resp.text = str(json_data)
    return resp


def _patch_httpx(post_side_effect: Any) -> Any:
    """Patch httpx.AsyncClient.post dengan side_effect yang diberikan."""
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=post_side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mock_client_cls = MagicMock(return_value=mock_client)
    return patch("httpx.AsyncClient", mock_client_cls)


@pytest.mark.asyncio
async def test_signup_success(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
    mock_db: MagicMock,
) -> None:
    def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        url = args[0] if args else kwargs.get("url", "")
        if "admin/users" in url:
            return _mock_response(200, {"id": "user-1", "email": "test@example.com"})
        return _mock_response(
            200,
            {
                "access_token": make_jwt(sub="user-1"),
                "user": {"id": "user-1", "email": "test@example.com"},
            },
        )

    with _patch_httpx(side_effect):
        result = await service.sign_up(
            db=mock_db,
            payload=SignUpRequest(email="test@example.com", password="validpass123"),
            ip_address="1.2.3.4",
            user_agent="test-agent",
        )

    assert result["user_id"] == "user-1"
    assert result["email"] == "test@example.com"
    assert result["token_type"] == "bearer"
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_signup_duplicate_email(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        return _mock_response(422, {"error": "User already registered"})

    with _patch_httpx(side_effect), pytest.raises(ConflictError):
        await service.sign_up(
            db=mock_db,
            payload=SignUpRequest(email="exists@example.com", password="validpass123"),
            ip_address="1.2.3.4",
            user_agent="test-agent",
        )


@pytest.mark.asyncio
async def test_signup_supabase_down(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        return _mock_response(500, {"error": "server error"})

    with _patch_httpx(side_effect), pytest.raises(ExternalServiceError):
        await service.sign_up(
            db=mock_db,
            payload=SignUpRequest(email="a@b.com", password="validpass123"),
            ip_address="1.2.3.4",
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_signin_success(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
    mock_db: MagicMock,
) -> None:
    def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        return _mock_response(
            200,
            {
                "access_token": make_jwt(sub="user-1"),
                "user": {"id": "user-1", "email": "test@example.com"},
            },
        )

    with _patch_httpx(side_effect):
        result = await service.sign_in(
            db=mock_db,
            payload=SignInRequest(email="test@example.com", password="validpass123"),
            ip_address="1.2.3.4",
            user_agent="test-agent",
        )

    assert result["user_id"] == "user-1"
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_signin_wrong_password(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    def side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        return _mock_response(400, {"error": "invalid_grant"})

    with _patch_httpx(side_effect), pytest.raises(AuthenticationError):
        await service.sign_in(
            db=mock_db,
            payload=SignInRequest(email="test@example.com", password="wrongpass1"),
            ip_address="1.2.3.4",
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_sign_out(mock_db: MagicMock) -> None:
    result_mock = MagicMock()
    result_mock.fetchall = MagicMock(return_value=[("session-1",)])

    async def _execute(*args: Any, **kwargs: Any) -> MagicMock:
        return result_mock

    mock_db.execute = _execute

    count = await service.sign_out(db=mock_db, session_id="session-1")
    assert count == 1


@pytest.mark.asyncio
async def test_sign_out_all(mock_db: MagicMock) -> None:
    result_mock = MagicMock()
    result_mock.fetchall = MagicMock(return_value=[("s1",), ("s2",), ("s3",)])

    async def _execute(*args: Any, **kwargs: Any) -> MagicMock:
        return result_mock

    mock_db.execute = _execute

    count = await service.sign_out_all(db=mock_db, user_id="user-1")
    assert count == 3


@pytest.mark.asyncio
async def test_get_user_state(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    result_mock = MagicMock()
    result_mock.first = MagicMock(return_value=(True, False))

    async def _execute(*args: Any, **kwargs: Any) -> MagicMock:
        return result_mock

    mock_db.execute = _execute

    user = {
        "user_id": "user-1",
        "email": "test@example.com",
        "email_verified": True,
    }
    state = await service.get_user_state(db=mock_db, user=user)

    assert state.user_id == "user-1"
    assert state.has_profile is True
    assert state.has_consent is False
