from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:   # <-- fix
    """
    Decode Supabase JWT & return user payload.
    Untuk sekarang: validasi format header aja.
    Decode JWT asli nanti di app/core/security.py.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token",
        )

    # TODO: decode JWT via app/core.security.verify_supabase_jwt
    return {"user_id": "placeholder", "token": token}


# Type aliases untuk dipakai di router
SettingsDep = Annotated[Settings, Depends(get_settings)]
DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]   # <-- fix
AuthHeader = Annotated[str | None, Header()]