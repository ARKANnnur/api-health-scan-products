from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.exceptions import DatabaseError

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_database_url() -> str:
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set it in .env (postgresql+asyncpg://user:pass@host:5432/db)."
        )
    return settings.DATABASE_URL


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield AsyncSession per request. Raise DatabaseError kalau DB unavailable."""
    try:
        session_factory = get_session_factory()
    except Exception as exc:
        import structlog
        structlog.get_logger().exception("get_db_failed", error=str(exc))
        raise DatabaseError(message="Database unavailable") from exc

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            import structlog
            structlog.get_logger().exception("db_operation_failed", error=str(exc))
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None