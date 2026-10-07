from fastapi import APIRouter, Request

from app.features.consent import service
from app.features.consent.schemas import (
    ConsentAcceptRequest,
    ConsentAcceptResponse,
    ConsentStatusResponse,
)
from app.shared.deps import CurrentUser, DBDep

router = APIRouter(prefix="/api/v1/consent", tags=["consent"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "",
    response_model=ConsentAcceptResponse,
    summary="Accept medical disclaimer",
)
async def accept_consent(
    payload: ConsentAcceptRequest,
    request: Request,
    db: DBDep,
    user: CurrentUser,
) -> ConsentAcceptResponse:
    ip = _get_client_ip(request)
    ua = request.headers.get("User-Agent")

    result = await service.accept_consent(
        db=db,
        user=user,
        disclaimer_version=payload.disclaimer_version,
        ip_address=ip,
        user_agent=ua,
    )
    return ConsentAcceptResponse(**result)


@router.get(
    "/status",
    response_model=ConsentStatusResponse,
    summary="Get current consent status",
)
async def get_status(
    db: DBDep,
    user: CurrentUser,
) -> ConsentStatusResponse:
    result = await service.get_consent_status(db=db, user=user)
    return ConsentStatusResponse(**result)
