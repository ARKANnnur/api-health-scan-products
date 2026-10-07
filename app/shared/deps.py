from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_supabase_jwt
from app.db.session import get_db

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Verify JWT + cek session masih aktif."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError(message="Missing Authorization header")

    token = credentials.credentials
    payload = await decode_supabase_jwt(token)

    session_id = payload.get("session_id") or f"{payload['sub']}-{payload.get('iat', 0)}"

    result = await db.execute(
        text(
            """
            SELECT 1 FROM user_sessions
            WHERE id = :sid
              AND revoked_at IS NULL
              AND expires_at > NOW()
        """
        ),
        {"sid": session_id},
    )
    if not result.first():
        raise AuthenticationError(message="Session expired or revoked")

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", True),
        "role": payload.get("role", "authenticated"),
        "session_id": session_id,
        "raw": payload,
    }


async def require_consent(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    settings = get_settings()
    result = await db.execute(
        text(
            """
            SELECT 1 FROM consent_logs
            WHERE user_id = :uid
              AND action = 'accepted'
              AND disclaimer_version = :version
            LIMIT 1
        """
        ),
        {"uid": user["user_id"], "version": settings.CURRENT_DISCLAIMER_VERSION},
    )
    if not result.first():
        raise AuthorizationError(
            code="CONSENT_REQUIRED",
            message=f"Consent versi {settings.CURRENT_DISCLAIMER_VERSION} wajib diisi",
        )
    return user


async def require_profile(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    result = await db.execute(
        text("SELECT 1 FROM profiles WHERE id = :uid"),
        {"uid": user["user_id"]},
    )
    if not result.first():
        raise AuthorizationError(
            code="PROFILE_REQUIRED",
            message="Profile harus dilengkapi dulu",
        )
    return user


# ============================================================
# TYPE ALIASES
# ============================================================
SettingsDep = Annotated[Settings, Depends(get_settings)]
DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
ConsentedUser = Annotated[dict[str, Any], Depends(require_consent)]
ProfiledUser = Annotated[dict[str, Any], Depends(require_profile)]


async def _get_session_id(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> str:
    session_id: str = user["session_id"]
    return session_id


SessionId = Annotated[str, Depends(_get_session_id)]
