from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.db.enums import AgeGroup
from app.features.profile import service
from app.features.profile.resolver import resolve_age_group
from app.features.profile.schemas import ProfileCreate, ProfileUpdate


# ============================================================
# Resolver tests — pure function
# ============================================================


def test_resolve_age_group_child_school() -> None:
    assert resolve_age_group(7) == AgeGroup.CHILD_SCHOOL
    assert resolve_age_group(12) == AgeGroup.CHILD_SCHOOL


def test_resolve_age_group_teen() -> None:
    assert resolve_age_group(13) == AgeGroup.TEEN
    assert resolve_age_group(17) == AgeGroup.TEEN


def test_resolve_age_group_young_adult() -> None:
    assert resolve_age_group(18) == AgeGroup.YOUNG_ADULT
    assert resolve_age_group(25) == AgeGroup.YOUNG_ADULT


def test_resolve_age_group_mature_elder() -> None:
    assert resolve_age_group(26) == AgeGroup.MATURE_ELDER
    assert resolve_age_group(120) == AgeGroup.MATURE_ELDER


def test_resolve_age_too_young() -> None:
    with pytest.raises(ValidationError) as exc:
        resolve_age_group(6)
    assert exc.value.code == "AGE_TOO_YOUNG"


def test_resolve_age_too_old() -> None:
    with pytest.raises(ValidationError) as exc:
        resolve_age_group(121)
    assert exc.value.code == "AGE_TOO_OLD"


# ============================================================
# Schema validation tests — pakai model_validate untuk bypass type checker
# ============================================================


def test_profile_create_valid() -> None:
    p = ProfileCreate(age_years=10, gender="MALE", weight_kg=30.5, height_cm=140)
    assert p.age_years == 10
    assert p.weight_kg == 30.5


def test_profile_create_age_too_young() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 6, "gender": "MALE", "weight_kg": 30, "height_cm": 140}
        )


def test_profile_create_weight_out_of_range() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 10, "gender": "MALE", "weight_kg": 4, "height_cm": 140}
        )


def test_profile_create_height_out_of_range() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 10, "gender": "MALE", "weight_kg": 30, "height_cm": 300}
        )


def test_profile_create_gender_invalid() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 10, "gender": "OTHER", "weight_kg": 30, "height_cm": 140}
        )


def test_profile_create_trim_whitespace() -> None:
    p = ProfileCreate.model_validate(
        {"age_years": 10, "gender": "MALE", "weight_kg": "  30  ", "height_cm": "140"}
    )
    assert p.weight_kg == 30.0


def test_profile_create_reject_script() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 10, "gender": "MALE", "weight_kg": "<script>", "height_cm": 140}
        )


def test_profile_create_reject_null_byte() -> None:
    with pytest.raises(PydanticValidationError):
        ProfileCreate.model_validate(
            {"age_years": 10, "gender": "MALE", "weight_kg": "\x0030", "height_cm": 140}
        )


# ============================================================
# Endpoint tests — auth required
# ============================================================


@pytest.mark.asyncio
async def test_create_profile_without_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/profile",
        json={"age_years": 10, "gender": "MALE", "weight_kg": 30, "height_cm": 140},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_without_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/profile")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_patch_profile_without_auth(client: AsyncClient) -> None:
    resp = await client.patch("/api/v1/profile", json={"weight_kg": 35})
    assert resp.status_code == 401


# ============================================================
# Helper untuk bikin mock row profile
# ============================================================


def _profile_row() -> tuple[Any, ...]:
    now = datetime.now(UTC)
    return (
        "user-1",  # id
        10,  # age_years
        "CHILD_SCHOOL",  # age_group
        "MALE",  # gender
        30.5,  # weight_kg
        140.0,  # height_cm
        True,  # is_minor
        now,  # disclaimer_accepted_at
        now,  # profile_completed_at
        now,  # created_at
        now,  # updated_at
    )


# ============================================================
# Service tests
# ============================================================


@pytest.mark.asyncio
async def test_create_profile_success(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    call_count = {"n": 0}

    def make_result() -> MagicMock:
        result = MagicMock()
        if call_count["n"] == 0:
            result.first = MagicMock(return_value=None)
        else:
            result.first = MagicMock(return_value=_profile_row())
        call_count["n"] += 1
        return result

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return make_result()

    mock_db.execute = execute_side

    payload = ProfileCreate(age_years=10, gender="MALE", weight_kg=30.5, height_cm=140)
    profile, created = await service.create_or_get(mock_db, "user-1", payload)

    assert created is True
    assert profile.user_id == "user-1"
    assert profile.age_group == "CHILD_SCHOOL"
    assert profile.is_minor is True


@pytest.mark.asyncio
async def test_create_profile_idempotent(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    result = MagicMock()
    result.first = MagicMock(return_value=_profile_row())

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return result

    mock_db.execute = execute_side

    payload = ProfileCreate(age_years=10, gender="MALE", weight_kg=30.5, height_cm=140)
    profile, created = await service.create_or_get(mock_db, "user-1", payload)

    assert created is False
    assert profile.user_id == "user-1"


@pytest.mark.asyncio
async def test_get_profile_not_found(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    result = MagicMock()
    result.first = MagicMock(return_value=None)

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return result

    mock_db.execute = execute_side

    profile = await service.get_by_id(mock_db, "user-1")
    assert profile is None


@pytest.mark.asyncio
async def test_update_profile_not_found(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    result = MagicMock()
    result.first = MagicMock(return_value=None)

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return result

    mock_db.execute = execute_side

    payload = ProfileUpdate(weight_kg=35)
    with pytest.raises(ResourceNotFoundError):
        await service.update(mock_db, "user-1", payload)


@pytest.mark.asyncio
async def test_update_profile_success(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    # Sequence:
    # 1. get_by_id (existing check) → row ada
    # 2. UPDATE (bisa apa aja)
    # 3. get_by_id (post-update) → row
    call_count = {"n": 0}

    def make_result() -> MagicMock:
        result = MagicMock()
        # existing check & post-update → row
        result.first = MagicMock(return_value=_profile_row())
        call_count["n"] += 1
        return result

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return make_result()

    mock_db.execute = execute_side

    payload = ProfileUpdate(weight_kg=35)
    profile = await service.update(mock_db, "user-1", payload)
    assert profile.user_id == "user-1"
    assert call_count["n"] >= 3


@pytest.mark.asyncio
async def test_update_profile_empty_payload(
    test_env: dict[str, str],
    mock_db: MagicMock,
) -> None:
    """Kalau payload kosong, return existing tanpa update."""
    result = MagicMock()
    result.first = MagicMock(return_value=_profile_row())

    async def execute_side(*args: Any, **kwargs: Any) -> MagicMock:
        return result

    mock_db.execute = execute_side

    payload = ProfileUpdate()
    profile = await service.update(mock_db, "user-1", payload)
    assert profile.user_id == "user-1"
