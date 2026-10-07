import unicodedata
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

_EMOJI_RANGES = (
    (0x1F300, 0x1FAFF),
    (0x1F000, 0x1F2FF),
    (0x2600, 0x27BF),
    (0x1F1E6, 0x1F1FF),
)


def _has_emoji(s: str) -> bool:
    for ch in s:
        cp = ord(ch)
        for lo, hi in _EMOJI_RANGES:
            if lo <= cp <= hi:
                return True
    return False


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("email", mode="before")
    @classmethod
    def reject_emoji_email(cls, v: Any) -> Any:
        if isinstance(v, str) and _has_emoji(v):
            raise ValueError("Email tidak boleh mengandung emoji")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        v = unicodedata.normalize("NFKC", v)
        if v != v.strip():
            raise ValueError("Password cannot start or end with whitespace")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least 1 letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least 1 digit")
        if _has_emoji(v):
            raise ValueError("Password cannot contain emoji")
        return v


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str


class MeResponse(BaseModel):
    user_id: str
    email: str | None
    email_verified: bool
    has_consent: bool
    has_profile: bool


class SignOutResponse(BaseModel):
    revoked: int
    message: str = "Signed out successfully"
