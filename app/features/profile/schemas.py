import unicodedata
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

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


def _has_forbidden_chars(s: str) -> bool:
    for ch in s:
        cp = ord(ch)
        if cp == 0:
            return True
        if 0x01 <= cp <= 0x1F and ch not in ("\n", "\t"):
            return True
    return False


def _sanitize_number(v: Any) -> Any:
    if isinstance(v, str):
        if _has_emoji(v) or _has_forbidden_chars(v):
            raise ValueError("Karakter tidak valid")
        if "<" in v or ">" in v:
            raise ValueError("Karakter tidak valid")
        v = unicodedata.normalize("NFKC", v).strip()
    return v


class ProfileCreate(BaseModel):
    age_years: int = Field(..., ge=7, le=120)
    gender: Literal["MALE", "FEMALE"]
    weight_kg: float = Field(..., ge=5, le=300)
    height_cm: float = Field(..., ge=50, le=250)

    @field_validator("weight_kg", "height_cm", mode="before")
    @classmethod
    def trim_and_normalize(cls, v: Any) -> Any:
        return _sanitize_number(v)


class ProfileUpdate(BaseModel):
    age_years: int | None = Field(None, ge=7, le=120)
    gender: Literal["MALE", "FEMALE"] | None = None
    weight_kg: float | None = Field(None, ge=5, le=300)
    height_cm: float | None = Field(None, ge=50, le=250)

    @field_validator("weight_kg", "height_cm", mode="before")
    @classmethod
    def trim_and_normalize(cls, v: Any) -> Any:
        if v is None:
            return v
        return _sanitize_number(v)


class ProfileResponse(BaseModel):
    user_id: str
    age_years: int
    age_group: str
    gender: str
    weight_kg: float
    height_cm: float
    is_minor: bool
    disclaimer_accepted_at: datetime | None
    profile_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
