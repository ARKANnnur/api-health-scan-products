from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        settings = get_settings()
        jwks_url = settings.SUPABASE_URL + "/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwks_client


async def decode_supabase_jwt(token: str) -> dict[str, Any]:
    settings = get_settings()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError(message="Invalid JWT header") from exc

    alg = unverified_header.get("alg", "ES256")

    try:
        if alg == "HS256":
            payload: dict[str, Any] = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            client = _get_jwks_client()
            signing_key = client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
            )
    except jwt.PyJWTError as exc:
        raise AuthenticationError(message="Invalid JWT") from exc

    if not payload.get("sub"):
        raise AuthenticationError(message="JWT missing subject claim")

    return payload
