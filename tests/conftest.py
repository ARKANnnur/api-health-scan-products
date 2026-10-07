import os
from collections.abc import AsyncIterator, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("ENV", "dev")

TEST_JWT_SECRET = "test_jwt_secret_at_least_32_chars_long_here"
TEST_SUPABASE_URL = "https://test.supabase.co"
TEST_ISSUER = f"{TEST_SUPABASE_URL}/auth/v1"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    env = {
        "SUPABASE_URL": TEST_SUPABASE_URL,
        "SUPABASE_ANON_KEY": "a" * 20,
        "SUPABASE_SERVICE_ROLE_KEY": "b" * 20,
        "SUPABASE_JWT_SECRET": TEST_JWT_SECRET,
        "GEMINI_API_KEY": "d" * 20,
        "ENV": "dev",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    import app.core.config as cfg

    cfg._settings = None
    return env


@pytest.fixture
def make_jwt() -> Callable[..., str]:
    from datetime import UTC, datetime, timedelta

    import jwt

    def _make(
        sub: str | None = "user-123",
        email: str | None = "test@example.com",
        session_id: str | None = "session-123",
        exp_delta_hours: int = 1,
        secret: str = TEST_JWT_SECRET,
        **overrides: Any,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=exp_delta_hours)).timestamp()),
        }
        if sub is not None:
            payload["sub"] = sub
        if email is not None:
            payload["email"] = email
        if session_id is not None:
            payload["session_id"] = session_id
        payload.update(overrides)
        return jwt.encode(payload, secret, algorithm="HS256")

    return _make


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock AsyncSession untuk service test tanpa DB nyata."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db
