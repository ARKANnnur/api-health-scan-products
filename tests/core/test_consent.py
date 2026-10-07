from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.core.exceptions import ValidationError
from app.features.consent import service


# ============================================================
# Endpoint tests — auth required
# ============================================================


@pytest.mark.asyncio
async def test_accept_consent_without_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/consent",
        json={"disclaimer_version": "1.0.0", "action": "accepted"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_status_without_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/consent/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_accept_consent_invalid_action(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/consent",
        json={"disclaimer_version": "1.0.0", "action": "invalid_action"},
    )
    # 401 duluan karena belum auth
    assert resp.status_code == 401


# ============================================================
# Service tests — accept_consent
# ============================================================


@pytest.mark.asyncio
async def test_accept_consent_version_mismatch(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    user = {"user_id": "user-1", "email": "test@example.com"}

    with pytest.raises(ValidationError):
        await service.accept_consent(
            db=mock_db,
            user=user,
            disclaimer_version="9.9.9",  # mismatch dengan CURRENT (1.0.0)
            ip_address="1.2.3.4",
            user_agent="test-agent",
        )


@pytest.mark.asyncio
async def test_accept_consent_success(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    # Existing check: user belum pernah accept
    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=None)

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    user = {"user_id": "user-1", "email": "TEST@Example.com  "}
    result = await service.accept_consent(
        db=mock_db,
        user=user,
        disclaimer_version="1.0.0",
        ip_address="1.2.3.4",
        user_agent="test-agent",
    )

    assert result["accepted"] is True
    assert result["disclaimer_version"] == "1.0.0"
    assert "accepted_at" in result


@pytest.mark.asyncio
async def test_accept_consent_idempotent(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    """User yang udah accept versi sama → no-op."""
    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=("1.0.0",))

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    user = {"user_id": "user-1", "email": "test@example.com"}
    result = await service.accept_consent(
        db=mock_db,
        user=user,
        disclaimer_version="1.0.0",
        ip_address="1.2.3.4",
        user_agent="test-agent",
    )

    assert result["accepted"] is True


# ============================================================
# Service tests — get_consent_status
# ============================================================


@pytest.mark.asyncio
async def test_get_status_no_consent(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=None)

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    user = {"user_id": "user-1"}
    result = await service.get_consent_status(db=mock_db, user=user)

    assert result["current_version"] == "1.0.0"
    assert result["accepted_version"] is None
    assert result["requires_consent"] is True


@pytest.mark.asyncio
async def test_get_status_already_accepted(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=("1.0.0",))

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    user = {"user_id": "user-1"}
    result = await service.get_consent_status(db=mock_db, user=user)

    assert result["current_version"] == "1.0.0"
    assert result["accepted_version"] == "1.0.0"
    assert result["requires_consent"] is False


@pytest.mark.asyncio
async def test_get_status_version_bumped(
    test_env: dict[str, str],
    mock_db: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User accepted 1.0.0, current 1.0.1 → requires_consent=True."""
    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=("1.0.0",))

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    # Bump version di settings
    monkeypatch.setenv("CURRENT_DISCLAIMER_VERSION", "1.0.1")
    import app.core.config as cfg

    cfg._settings = None

    user = {"user_id": "user-1"}
    result = await service.get_consent_status(db=mock_db, user=user)

    assert result["current_version"] == "1.0.1"
    assert result["accepted_version"] == "1.0.0"
    assert result["requires_consent"] is True


# ============================================================
# Guard tests — require_consent
# ============================================================


@pytest.mark.asyncio
async def test_require_consent_raises_when_missing(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    from app.core.exceptions import AuthorizationError
    from app.shared.deps import require_consent

    existing_result = MagicMock()
    existing_result.first = MagicMock(return_value=None)

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return existing_result

    mock_db.execute = execute_side

    user = {"user_id": "user-1"}
    with pytest.raises(AuthorizationError) as exc:
        await require_consent(user=user, db=mock_db)

    assert exc.value.code == "CONSENT_REQUIRED"
    assert exc.value.status_code == 403
