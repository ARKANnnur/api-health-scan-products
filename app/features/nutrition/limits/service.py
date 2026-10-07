import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def recompute_limits_stub(db: AsyncSession, user_id: str) -> None:
    """Placeholder untuk recompute_limits.

    Dipanggil setiap profile dibuat/update.
    NUTRI-203-BE akan ganti ini dengan implementasi nyata.
    """
    logger.info("recompute_limits_stub_called", user_id=user_id)
