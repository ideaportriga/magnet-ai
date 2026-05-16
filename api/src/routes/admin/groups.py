"""Admin endpoints for group management.

Groups are tenant-scoped (PR 6 of access-control plan). Each call inherits
the caller's tenant from `auth.tenant_id`; cross-tenant operations are not
possible from this surface.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from litestar import Controller, Request, delete, get, post
from litestar.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.user.group import Group
from core.db.models.user.user import User
from core.db.models.user.user_group import UserGroup
from core.domain.users.roles_schemas import GroupCreate, GroupMemberAdd, GroupResponse
from guards.permissions import Permission, require_permission
from middlewares.auth import Auth


def _tenant_id_from_request(request: Request) -> UUID:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required for group management.")
    return UUID(auth.tenant_id)


class GroupsController(Controller):
    path = "/groups"
    tags = ["Admin / Groups"]

    @get(
        "/",
        summary="List groups in the caller's tenant",
        guards=[require_permission(Permission.GROUPS_READ)],
    )
    async def list_groups(self, request: Request) -> list[GroupResponse]:
        tenant_id = _tenant_id_from_request(request)
        async with alchemy.get_session() as session:
            result = await session.execute(
                select(Group).where(Group.tenant_id == tenant_id)
            )
            groups = result.scalars().all()
            return [
                GroupResponse(
                    id=g.id,
                    name=g.name,
                    slug=g.slug,
                    description=g.description,
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                )
                for g in groups
            ]

    @post(
        "/",
        summary="Create a group in the caller's tenant",
        guards=[require_permission(Permission.GROUPS_WRITE)],
    )
    async def create_group(self, request: Request, data: GroupCreate) -> GroupResponse:
        tenant_id = _tenant_id_from_request(request)
        async with alchemy.get_session() as session:
            group = Group(
                tenant_id=tenant_id,
                name=data.name,
                slug=data.slug,
                description=data.description,
            )
            session.add(group)
            try:
                await session.commit()
            except Exception as exc:
                raise ValidationException(
                    f"Could not create group (slug/name collision in tenant?): {exc}"
                ) from exc
            await session.refresh(group)
            return GroupResponse(
                id=group.id,
                name=group.name,
                slug=group.slug,
                description=group.description,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )

    @post(
        "/{group_id:uuid}/members",
        summary="Add user to group",
        guards=[require_permission(Permission.GROUPS_WRITE)],
    )
    async def add_member(
        self, request: Request, group_id: UUID, data: GroupMemberAdd
    ) -> dict:
        tenant_id = _tenant_id_from_request(request)
        async with alchemy.get_session() as session:
            group = await session.get(Group, group_id)
            if not group or group.tenant_id != tenant_id:
                raise NotFoundException("Group not found")

            target_user = (
                await session.execute(select(User).where(User.id == data.user_id))
            ).scalar_one_or_none()
            if not target_user or target_user.tenant_id != tenant_id:
                raise NotFoundException("User not found")

            stmt = select(UserGroup).where(
                UserGroup.tenant_id == tenant_id,
                UserGroup.user_id == data.user_id,
                UserGroup.group_id == group_id,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return {"message": "User already a member of this group"}

            session.add(
                UserGroup(
                    tenant_id=tenant_id,
                    user_id=data.user_id,
                    group_id=group_id,
                    role_in_group=data.role_in_group,
                    assigned_at=datetime.now(UTC),
                )
            )
            await session.commit()
            return {"message": f"User added to group '{group.slug}'"}

    @delete(
        "/{group_id:uuid}/members/{member_id:uuid}",
        summary="Remove user from group",
        guards=[require_permission(Permission.GROUPS_WRITE)],
    )
    async def remove_member(
        self, request: Request, group_id: UUID, member_id: UUID
    ) -> None:
        tenant_id = _tenant_id_from_request(request)
        async with alchemy.get_session() as session:
            # Ensure the group is in the caller's tenant before touching it.
            group = await session.get(Group, group_id)
            if not group or group.tenant_id != tenant_id:
                raise NotFoundException("Group not found")

            stmt = select(UserGroup).where(
                UserGroup.tenant_id == tenant_id,
                UserGroup.user_id == member_id,
                UserGroup.group_id == group_id,
            )
            result = await session.execute(stmt)
            membership = result.scalar_one_or_none()
            if not membership:
                raise NotFoundException("User is not a member of this group")

            await session.delete(membership)
            await session.commit()
