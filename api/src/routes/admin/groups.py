"""Admin endpoints for group management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.exceptions import NotFoundException
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.user.group import Group
from core.db.models.user.user_group import UserGroup
from core.domain.users.roles_schemas import GroupCreate, GroupMemberAdd, GroupResponse
from core.domain.users.service import UsersService


class GroupsController(Controller):
    path = "/groups"
    tags = ["Admin / Groups"]

    @get("/", summary="List all groups")
    async def list_groups(self) -> list[GroupResponse]:
        async with alchemy.get_session() as session:
            result = await session.execute(select(Group))
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

    @post("/", summary="Create a group")
    async def create_group(self, data: GroupCreate) -> GroupResponse:
        async with alchemy.get_session() as session:
            group = Group(name=data.name, slug=data.slug, description=data.description)
            session.add(group)
            await session.commit()
            await session.refresh(group)
            return GroupResponse(
                id=group.id,
                name=group.name,
                slug=group.slug,
                description=group.description,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )

    @post("/{group_id:uuid}/members", summary="Add user to group")
    async def add_member(self, group_id: UUID, data: GroupMemberAdd) -> dict:
        async with alchemy.get_session() as session:
            # Verify group exists
            group = await session.get(Group, group_id)
            if not group:
                raise NotFoundException("Group not found")

            # Verify user exists
            users_service = UsersService(session=session)
            user = await users_service.get_one_or_none(id=data.user_id)
            if not user:
                raise NotFoundException("User not found")

            # Check if already a member
            stmt = select(UserGroup).where(
                UserGroup.user_id == data.user_id,
                UserGroup.group_id == group_id,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return {"message": "User already a member of this group"}

            session.add(
                UserGroup(
                    user_id=data.user_id,
                    group_id=group_id,
                    role_in_group=data.role_in_group,
                    assigned_at=datetime.now(UTC),
                )
            )
            await session.commit()
            return {"message": f"User added to group '{group.slug}'"}

    @delete(
        "/{group_id:uuid}/members/{member_id:uuid}", summary="Remove user from group"
    )
    async def remove_member(self, group_id: UUID, member_id: UUID) -> None:
        async with alchemy.get_session() as session:
            stmt = select(UserGroup).where(
                UserGroup.user_id == member_id,
                UserGroup.group_id == group_id,
            )
            result = await session.execute(stmt)
            membership = result.scalar_one_or_none()
            if not membership:
                raise NotFoundException("User is not a member of this group")

            await session.delete(membership)
            await session.commit()
