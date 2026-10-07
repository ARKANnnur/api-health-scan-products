from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.features.nutrition.limits.service import recompute_limits_stub
from app.features.profile.resolver import resolve_age_group
from app.features.profile.schemas import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)

logger = structlog.get_logger()


async def get_by_id(
    db: AsyncSession,
    user_id: str,
) -> ProfileResponse | None:
    result = await db.execute(
        text(
            """
            SELECT id, age_years, age_group, gender, weight_kg, height_cm,
                   is_minor, disclaimer_accepted_at, profile_completed_at,
                   created_at, updated_at
            FROM profiles
            WHERE id = :uid AND deleted_at IS NULL
        """
        ),
        {"uid": user_id},
    )
    row = result.first()
    if not row:
        return None
    return ProfileResponse(
        user_id=str(row[0]),
        age_years=row[1],
        age_group=row[2],
        gender=row[3],
        weight_kg=float(row[4]),
        height_cm=float(row[5]),
        is_minor=row[6],
        disclaimer_accepted_at=row[7],
        profile_completed_at=row[8],
        created_at=row[9],
        updated_at=row[10],
    )


async def create_or_get(
    db: AsyncSession,
    user_id: str,
    payload: ProfileCreate,
) -> tuple[ProfileResponse, bool]:
    """Create profile. Kalau udah ada → return existing.

    Returns:
        (profile, created): created=True kalau baru dibuat.
    """
    existing = await get_by_id(db, user_id)
    if existing:
        logger.info("profile_already_exists", user_id=user_id)
        return existing, False

    age_group = resolve_age_group(payload.age_years)

    await db.execute(
        text(
            """
            INSERT INTO profiles
                (id, age_years, age_group, gender, weight_kg, height_cm,
                 profile_completed_at)
            VALUES
                (:uid, :age, :group, :gender, :weight, :height, NOW())
        """
        ),
        {
            "uid": user_id,
            "age": payload.age_years,
            "group": age_group.value,
            "gender": payload.gender,
            "weight": payload.weight_kg,
            "height": payload.height_cm,
        },
    )

    await recompute_limits_stub(db, user_id)

    logger.info("profile_created", user_id=user_id, age_group=age_group.value)

    created = await get_by_id(db, user_id)
    assert created is not None
    return created, True


async def update(
    db: AsyncSession,
    user_id: str,
    payload: ProfileUpdate,
) -> ProfileResponse:
    existing = await get_by_id(db, user_id)
    if not existing:
        raise ResourceNotFoundError("Profile belum diisi")

    fields: list[str] = []
    params: dict[str, Any] = {"uid": user_id}

    if payload.age_years is not None:
        fields.append("age_years = :age")
        params["age"] = payload.age_years
        fields.append("age_group = :group")
        params["group"] = resolve_age_group(payload.age_years).value

    if payload.gender is not None:
        fields.append("gender = :gender")
        params["gender"] = payload.gender

    if payload.weight_kg is not None:
        fields.append("weight_kg = :weight")
        params["weight"] = payload.weight_kg

    if payload.height_cm is not None:
        fields.append("height_cm = :height")
        params["height"] = payload.height_cm

    if not fields:
        return existing

    fields.append("updated_at = NOW()")
    query = f"""
        UPDATE profiles
        SET {", ".join(fields)}
        WHERE id = :uid AND deleted_at IS NULL
    """
    await db.execute(text(query), params)

    await recompute_limits_stub(db, user_id)

    logger.info("profile_updated", user_id=user_id, fields=len(fields) - 1)

    updated = await get_by_id(db, user_id)
    assert updated is not None
    return updated
