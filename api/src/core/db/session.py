"""Database session utilities.

Both this module and the Litestar alchemy plugin (core.config.app.alchemy)
use the same engine instance from settings.db.get_engine(), so sessions
from either source share the same connection pool.
"""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.app import settings

# Session maker bound to the same engine as the Litestar alchemy plugin.
async_session_maker = async_sessionmaker(
    bind=settings.db.get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_async_session():
    """Get an async database session as context manager.

    Used by background tasks and scheduler jobs (outside Litestar route handlers).
    Route handlers get automatic commit/rollback via the Litestar alchemy plugin
    (before_send_handler="autocommit").
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
