import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env minimal biar Settings bisa dibikin."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "a" * 20)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "b" * 20)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "c" * 20)
    monkeypatch.setenv("GEMINI_API_KEY", "d" * 20)
    monkeypatch.setenv("ENV", "dev")


def test_settings_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-101-1: config valid bisa dibikin."""
    _base_env(monkeypatch)
    s = Settings(_env_file=None)
    assert s.ENV == "dev"
    assert s.SUPABASE_URL == "https://test.supabase.co"


def test_settings_missing_supabase_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-101-4: missing env → ValidationError."""
    _base_env(monkeypatch)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    assert "SUPABASE_URL" in str(exc.value)


def test_settings_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-101-5: URL tidak valid → ValidationError."""
    _base_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "not-a-url")
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None)
    assert "https://" in str(exc.value)


def test_settings_invalid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """ENV harus salah satu dari dev/staging/prod."""
    _base_env(monkeypatch)
    monkeypatch.setenv("ENV", "invalid")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_secret_too_short(monkeypatch: pytest.MonkeyPatch) -> None:
    """Secret < 10 karakter → ValidationError."""
    _base_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "short")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_parse_cors_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """CORS_ORIGINS string di-parse jadi list."""
    _base_env(monkeypatch)
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    s = Settings(_env_file=None)
    assert s.CORS_ORIGINS == ["http://a.com", "http://b.com"]