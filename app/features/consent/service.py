from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ValidationError

logger = structlog.get_logger()


async def get_current_accepted_version(
    db: AsyncSession,
    user_id: str,
) -> str | None:
    """Ambil versi consent terakhir yang di-accept user (kalau ada)."""
    result = await db.execute(
        text(
            """
            SELECT disclaimer_version
            FROM consent_logs
            WHERE user_id = :uid
              AND action = 'accepted'
            ORDER BY created_at DESC
            LIMIT 1
        """
        ),
        {"uid": user_id},
    )
    row = result.first()
    return row[0] if row else None


async def accept_consent(
    db: AsyncSession,
    user: dict[str, Any],
    disclaimer_version: str,
    ip_address: str | None,
    user_agent: str | None,
) -> dict[str, Any]:
    """Catat acceptance user.

    Idempotent: kalau user udah accept versi yang sama, ga insert row baru.
    """
    settings = get_settings()
    user_id = user["user_id"]

    # 1. Validasi versi
    if disclaimer_version != settings.CURRENT_DISCLAIMER_VERSION:
        raise ValidationError(
            message=(
                f"Disclaimer version mismatch. "
                f"Expected {settings.CURRENT_DISCLAIMER_VERSION}, "
                f"got {disclaimer_version}"
            ),
        )

    # 2. Cek idempotency — udah accept versi ini?
    existing = await get_current_accepted_version(db, user_id)
    if existing == disclaimer_version:
        logger.info("consent_already_accepted", user_id=user_id, version=disclaimer_version)
        return {
            "accepted": True,
            "disclaimer_version": disclaimer_version,
            "accepted_at": datetime.now(UTC).isoformat(),
        }

    # 3. Snapshot email (lowercase + trim)
    email_raw = user.get("email")
    email_snapshot = email_raw.strip().lower() if email_raw else None

    # 4. Insert consent_logs
    await db.execute(
        text(
            """
            INSERT INTO consent_logs
                (id, user_id, user_email_snapshot, disclaimer_version,
                 action, ip_address, user_agent)
            VALUES
                (gen_random_uuid(), :uid, :email, :version,
                 'accepted', :ip, :ua)
        """
        ),
        {
            "uid": user_id,
            "email": email_snapshot,
            "version": disclaimer_version,
            "ip": ip_address,
            "ua": user_agent,
        },
    )

    # 5. Update profiles.disclaimer_version kalau row-nya udah ada (post-onboarding)
    await db.execute(
        text(
            """
            UPDATE profiles
            SET disclaimer_version = :version,
                disclaimer_accepted_at = NOW()
            WHERE id = :uid
        """
        ),
        {"uid": user_id, "version": disclaimer_version},
    )

    logger.info(
        "consent_accepted",
        user_id=user_id,
        version=disclaimer_version,
        ip=ip_address,
    )

    return {
        "accepted": True,
        "disclaimer_version": disclaimer_version,
        "accepted_at": datetime.now(UTC).isoformat(),
    }


async def get_consent_status(
    db: AsyncSession,
    user: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    user_id = user["user_id"]

    accepted_version = await get_current_accepted_version(db, user_id)

    return {
        "current_version": settings.CURRENT_DISCLAIMER_VERSION,
        "accepted_version": accepted_version,
        "requires_consent": accepted_version != settings.CURRENT_DISCLAIMER_VERSION,
    }
