from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ResourceNotFoundError
from app.features.profile import service
from app.features.profile.schemas import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.shared.deps import ConsentedUser, DBDep
from app.shared.schemas import BaseResponse

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.post(
    "",
    response_model=BaseResponse[ProfileResponse],
    summary="Create profile (idempotent)",
)
async def create_profile(
    payload: ProfileCreate,
    db: DBDep,
    user: ConsentedUser,
) -> Any:  # ← ini yang ditambahin
    profile, created = await service.create_or_get(db, user["user_id"], payload)
    body = BaseResponse(data=profile)
    if created:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=body.model_dump(mode="json"),
        )
    return body


@router.get(
    "",
    response_model=BaseResponse[ProfileResponse],
    summary="Get current user profile",
)
async def get_profile(
    db: DBDep,
    user: ConsentedUser,
) -> BaseResponse[ProfileResponse]:
    profile = await service.get_by_id(db, user["user_id"])
    if not profile:
        raise ResourceNotFoundError("Profile belum diisi")
    return BaseResponse(data=profile)


@router.patch(
    "",
    response_model=BaseResponse[ProfileResponse],
    summary="Update profile (partial)",
)
async def update_profile(
    payload: ProfileUpdate,
    db: DBDep,
    user: ConsentedUser,
) -> BaseResponse[ProfileResponse]:
    profile = await service.update(db, user["user_id"], payload)
    return BaseResponse(data=profile)
