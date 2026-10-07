import pytest

from app.core.config import Settings
from app.main import _resolve_cors_origins, _validate_cors_failsafe


def test_cors_failsafe_prod_wildcard(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-101-6: prod + CORS '*' → raise."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "a" * 20)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "b" * 20)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "c" * 20)
    monkeypatch.setenv("GEMINI_API_KEY", "d" * 20)
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    s = Settings(_env_file=None)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        _validate_cors_failsafe(s)


def test_cors_failsafe_dev_wildcard_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dev + wildcard → aman."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "a" * 20)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "b" * 20)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "c" * 20)
    monkeypatch.setenv("GEMINI_API_KEY", "d" * 20)
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    s = Settings(_env_file=None)
    _validate_cors_failsafe(s)  # should not raise


def test_resolve_cors_origins_dev() -> None:
    """Dev → return localhost list."""
    from unittest.mock import MagicMock

    s = MagicMock()
    s.ENV = "dev"
    origins = _resolve_cors_origins(s)
    assert "http://localhost:3000" in origins


def test_resolve_cors_origins_prod() -> None:
    """Prod → return whitelist dari settings."""
    from unittest.mock import MagicMock

    s = MagicMock()
    s.ENV = "prod"
    s.CORS_ORIGINS = ["https://app.example.com"]
    origins = _resolve_cors_origins(s)
    assert origins == ["https://app.example.com"]
