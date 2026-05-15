"""Admin endpoint: permission catalog (read-only) + cache reload."""

from __future__ import annotations

from typing import Optional

from litestar import Controller, get, post
from pydantic import BaseModel
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.user.permission import Permission
from guards.permissions import (
    Permission as PermissionCode,
    load_role_permissions_cache,
    require_permission,
)


class PermissionEntry(BaseModel):
    """One row of the permission catalog."""

    code: str
    resource_type: str
    action: str
    description: Optional[str] = None
    is_system: bool = True


class PermissionsController(Controller):
    path = "/permissions"
    tags = ["Admin / Permissions"]
    guards = [require_permission(PermissionCode.ROLES_READ)]

    @get(summary="List permission catalog")
    async def list_permissions(
        self, resource_type: Optional[str] = None
    ) -> list[PermissionEntry]:
        async with alchemy.get_session() as session:
            stmt = select(Permission).order_by(
                Permission.resource_type, Permission.action
            )
            if resource_type:
                stmt = stmt.where(Permission.resource_type == resource_type)
            result = await session.execute(stmt)
            rows = result.scalars().all()

        return [
            PermissionEntry(
                code=r.code,
                resource_type=r.resource_type,
                action=r.action,
                description=r.description,
                is_system=r.is_system,
            )
            for r in rows
        ]

    @post(
        "/cache/reload",
        summary="Force-reload the role-permission cache",
        guards=[require_permission(PermissionCode.ROLES_WRITE)],
    )
    async def reload_cache(self) -> dict[str, str]:
        """Reload the process-wide `_ROLE_PERMISSIONS_CACHE` from the DB.

        Admin-only. Useful after seeding data through a side-channel (e.g.
        `scripts/seed_dev_fixtures.py`) — the admin role-edit endpoints
        already reload automatically. No-op if the cache is already fresh.
        """
        async with alchemy.get_session() as session:
            await load_role_permissions_cache(session=session)
        return {"status": "reloaded"}
