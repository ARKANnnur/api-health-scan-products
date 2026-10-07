from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database(db: AsyncSession) -> bool:
    """Return True kalau DB bisa di-query."""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
