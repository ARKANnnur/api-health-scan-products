from fastapi import APIRouter, Request, status

from app.core.exceptions import RateLimitError
from app.features.auth import service
from app.features.auth.rate_limit import (
    signin_email_limiter,
    signin_ip_limiter,
    signup_limiter,
)
from app.features.auth.schemas import (
    AuthTokenResponse,
    MeResponse,
    SignInRequest,
    SignOutResponse,
    SignUpRequest,
)
from app.shared.deps import CurrentUser, DBDep, SessionId

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/signup",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register + auto signin",
)
async def signup(
    payload: SignUpRequest,
    request: Request,
    db: DBDep,
) -> AuthTokenResponse:
    ip = _get_client_ip(request)
    if ip and not await signup_limiter.is_allowed(ip):
        raise RateLimitError(message="Terlalu banyak percobaan signup. Coba lagi nanti.")

    result = await service.sign_up(
        db=db,
        payload=payload,
        ip_address=ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return AuthTokenResponse(**result)


@router.post(
    "/signin",
    response_model=AuthTokenResponse,
    summary="Login",
)
async def signin(
    payload: SignInRequest,
    request: Request,
    db: DBDep,
) -> AuthTokenResponse:
    ip = _get_client_ip(request)

    if ip and not await signin_ip_limiter.is_allowed(ip):
        raise RateLimitError(message="Terlalu banyak percobaan login. Coba lagi nanti.")
    if not await signin_email_limiter.is_allowed(payload.email):
        raise RateLimitError(message="Terlalu banyak percobaan login untuk email ini.")

    result = await service.sign_in(
        db=db,
        payload=payload,
        ip_address=ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return AuthTokenResponse(**result)


@router.post(
    "/signout",
    response_model=SignOutResponse,
    summary="Revoke session saat ini",
)
async def signout(
    db: DBDep,
    session_id: SessionId,
    user: CurrentUser,
) -> SignOutResponse:
    count = await service.sign_out(db=db, session_id=session_id)
    return SignOutResponse(revoked=count)


@router.post(
    "/signout-all",
    response_model=SignOutResponse,
    summary="Revoke semua session user",
)
async def signout_all(
    db: DBDep,
    user: CurrentUser,
) -> SignOutResponse:
    count = await service.sign_out_all(db=db, user_id=user["user_id"])
    return SignOutResponse(revoked=count, message="Signed out from all devices")


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Ambil state user",
)
async def me(db: DBDep, user: CurrentUser) -> MeResponse:
    return await service.get_user_state(db=db, user=user)
