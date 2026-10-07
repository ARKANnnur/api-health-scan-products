from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        enable_decoding=False,
    )

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # External APIs
    GEMINI_API_KEY: str

    # Database (opsional — isi kalau udah punya Supabase asli)
    DATABASE_URL: str | None = None

    # App
    ENV: str = "dev"
    CORS_ORIGINS: list[str] = []
    # Consent
    CURRENT_DISCLAIMER_VERSION: str = "v1.0"

    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("SUPABASE_URL must start with https://")
        if len(v) < 15:
            raise ValueError("SUPABASE_URL too short")
        return v

    @field_validator("CURRENT_DISCLAIMER_VERSION")
    @classmethod
    def validate_disclaimer_version(cls, v: str) -> str:
        if not v or len(v) < 2:
            raise ValueError("CURRENT_DISCLAIMER_VERSION must be at least 2 chars")
        return v

    @field_validator(
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "GEMINI_API_KEY",
    )
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Secret/key must be at least 10 characters")
        return v

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"dev", "staging", "prod"}
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
