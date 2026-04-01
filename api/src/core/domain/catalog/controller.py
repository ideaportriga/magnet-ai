from __future__ import annotations

from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import CatalogItem
from .service import get_catalog


class CatalogController(Controller):
    """Unified entity catalog for global search."""

    path = "/catalog"
    tags = ["Admin / Catalog"]

    @get()
    async def list_catalog(self, db_session: AsyncSession) -> list[CatalogItem]:
        rows = await get_catalog(db_session)
        return [CatalogItem(**row) for row in rows]
