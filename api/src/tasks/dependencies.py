"""TaskiqDepends providers for task functions.

Currently only exposes `get_db_session` — an async session tied to the same
engine the Litestar app uses. Tasks should depend on this rather than open
their own sessions via `alchemy.get_session()` so that test fixtures can
override the engine cleanly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    from core.config.app import alchemy

    async with alchemy.get_session() as session:
        yield session
