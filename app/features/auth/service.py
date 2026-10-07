from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ExternalServiceError,
)
from app.db.models.user_session import UserSession
from app.features.auth.schemas import MeResponse, SignInRequest, SignUpRequest

logger = structlog.get_logger()

JWT_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 hari


def _supabase_admin_headers() -> dict[str, str]:
    settings = get_settings()
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


async def sign_up(
    db: AsyncSession,
    payload: SignUpRequest,
    ip_address: str | None,
    user_agent: str | None,
) -> dict[str, Any]:
    """Bikin user via Supabase Admin API, lalu auto-signin."""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Create user via Admin API
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers=_supabase_admin_headers(),
            json={
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
            },
        )

        if resp.status_code == 422:
            # Email sudah terdaftar
            raise ConflictError(message="Email sudah terdaftar")
        if resp.status_code >= 400:
            logger.error("supabase_signup_failed", status=resp.status_code, body=resp.text)
            raise ExternalServiceError(message="Gagal membuat akun, coba lagi")

        # 2. Sign in untuk dapat token
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            json={"email": payload.email, "password": payload.password},
        )

        if resp.status_code >= 400:
            logger.error("supabase_signin_failed", status=resp.status_code, body=resp.text)
            raise ExternalServiceError(message="Akun dibuat tapi gagal login, coba signin")

        data = resp.json()

    access_token = data["access_token"]
    user = data["user"]

    # 3. Simpan session
    await _save_session(
        db=db,
        access_token=access_token,
        user_id=user["id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info("user_signed_up", user_id=user["id"], email=user["email"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRY_SECONDS,
        "user_id": user["id"],
        "email": user["email"],
    }


async def sign_in(
    db: AsyncSession,
    payload: SignInRequest,
    ip_address: str | None,
    user_agent: str | None,
) -> dict[str, Any]:
    """Login via Supabase Auth, simpan session."""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            json={"email": payload.email, "password": payload.password},
        )

    if resp.status_code >= 400:
        logger.warning(
            "signin_failed",
            email=payload.email,
            ip=ip_address,
            status=resp.status_code,
        )
        raise AuthenticationError(message="Email atau password salah")

    data = resp.json()
    access_token = data["access_token"]
    user = data["user"]

    await _save_session(
        db=db,
        access_token=access_token,
        user_id=user["id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info("user_signed_in", user_id=user["id"], email=user["email"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRY_SECONDS,
        "user_id": user["id"],
        "email": user["email"],
    }


async def sign_out(
    db: AsyncSession,
    session_id: str,
) -> int:
    """Revoke session spesifik."""
    result = await db.execute(
        text(
            """
            UPDATE user_sessions
            SET revoked_at = NOW()
            WHERE id = :sid AND revoked_at IS NULL
            RETURNING id
        """
        ),
        {"sid": session_id},
    )
    count = len(result.fetchall())

    logger.info("user_signed_out", session_id=session_id, count=count)
    return count


async def sign_out_all(
    db: AsyncSession,
    user_id: str,
) -> int:
    """Revoke semua session user."""
    result = await db.execute(
        text(
            """
            UPDATE user_sessions
            SET revoked_at = NOW()
            WHERE user_id = :uid AND revoked_at IS NULL
            RETURNING id
        """
        ),
        {"uid": user_id},
    )
    count = len(result.fetchall())

    logger.info("user_signed_out_all", user_id=user_id, count=count)
    return count


async def get_user_state(
    db: AsyncSession,
    user: dict[str, Any],
) -> MeResponse:
    """Ambil user state untuk GET /auth/me."""
    settings = get_settings()
    user_id = user["user_id"]

    result = await db.execute(
        text(
            """
            SELECT
                EXISTS(SELECT 1 FROM profiles WHERE id = :uid) AS has_profile,
                EXISTS(
                    SELECT 1 FROM profiles
                    WHERE id = :uid
                      AND disclaimer_version = :version
                      AND disclaimer_accepted_at IS NOT NULL
                ) AS has_consent
        """
        ),
        {"uid": user_id, "version": settings.CURRENT_DISCLAIMER_VERSION},
    )
    row = result.first()
    has_profile = bool(row[0]) if row else False
    has_consent = bool(row[1]) if row else False

    return MeResponse(
        user_id=user_id,
        email=user.get("email"),
        email_verified=user.get("email_verified", True),
        has_consent=has_consent,
        has_profile=has_profile,
    )


# ============================================================
# INTERNAL
# ============================================================


async def _save_session(
    db: AsyncSession,
    access_token: str,
    user_id: str,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    """Decode JWT untuk dapetin session_id + exp, lalu insert ke user_sessions."""
    from app.core.security import decode_supabase_jwt

    payload = await decode_supabase_jwt(access_token)

    session_id = payload.get("session_id")
    if not session_id:
        # Fallback: bikin synthetic ID dari sub + iat
        session_id = f"{payload['sub']}-{payload.get('iat', 0)}"

    exp = payload.get("exp", 0)
    expires_at = datetime.fromtimestamp(exp, tz=UTC)

    session = UserSession(
        id=session_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        expires_at=expires_at,
    )
    db.add(session)
