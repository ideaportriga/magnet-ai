"""Database session utilities."""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.app import settings

# Create async session maker
async_session_maker = async_sessionmaker(
    bind=settings.db.get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_async_session():
    """Get an async database session as context manager."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
