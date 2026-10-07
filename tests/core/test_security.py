from collections.abc import Callable

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import decode_supabase_jwt


@pytest.mark.asyncio
async def test_decode_valid_token(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt()
    payload = await decode_supabase_jwt(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_decode_expired_token(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt(exp_delta_hours=-1)
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_wrong_secret(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt(secret="wrong_secret_that_is_32_chars_long_xx")
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_wrong_audience(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt(aud="other_role")
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_wrong_issuer(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt(iss="https://attacker.supabase.co/auth/v1")
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_missing_sub(
    test_env: dict[str, str],
    make_jwt: Callable[..., str],
) -> None:
    token = make_jwt(sub=None)
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_alg_none_rejected(test_env: dict[str, str]) -> None:
    import base64
    import json
    from datetime import UTC, datetime, timedelta

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = b64url(
        json.dumps(
            {
                "sub": "user-123",
                "aud": "authenticated",
                "iss": "https://test.supabase.co/auth/v1",
                "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            }
        ).encode()
    )
    token = f"{header}.{payload}."

    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt(token)


@pytest.mark.asyncio
async def test_decode_malformed_token(test_env: dict[str, str]) -> None:
    with pytest.raises(AuthenticationError):
        await decode_supabase_jwt("this.is.not.a.jwt")
