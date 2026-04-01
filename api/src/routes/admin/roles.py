"""Admin endpoints for role and user-role management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.exceptions import NotFoundException

from core.config.app import alchemy
from core.db.models.user.role import Role
from core.db.models.user.user_role import UserRole
from core.domain.users.roles_schemas import RoleCreate, RoleResponse, UserRoleAssign
from core.domain.users.roles_service import RolesService
from core.domain.users.service import UsersService


class RolesController(Controller):
    path = "/roles"
    tags = ["Admin / Roles"]

    @get("/", summary="List all roles")
    async def list_roles(self) -> list[RoleResponse]:
        async with alchemy.get_session() as session:
            service = RolesService(session=session)
            roles = await service.list()
            return [service.to_schema(r, schema_type=RoleResponse) for r in roles]

    @post("/", summary="Create a role")
    async def create_role(self, data: RoleCreate) -> RoleResponse:
        async with alchemy.get_session() as session:
            service = RolesService(session=session)
            role = await service.create(
                Role(name=data.name, slug=data.slug, description=data.description),
                auto_commit=True,
            )
            return service.to_schema(role, schema_type=RoleResponse)

    @post("/users/{target_user_id:uuid}/roles", summary="Assign role to user")
    async def assign_role(self, target_user_id: UUID, data: UserRoleAssign) -> dict:
        async with alchemy.get_session() as session:
            users_service = UsersService(session=session)
            roles_service = RolesService(session=session)

            user = await users_service.get_one_or_none(id=target_user_id)
            if not user:
                raise NotFoundException("User not found")

            role = await roles_service.get_one_or_none(id=data.role_id)
            if not role:
                raise NotFoundException("Role not found")

            from sqlalchemy import select

            stmt = select(UserRole).where(
                UserRole.user_id == target_user_id,
                UserRole.role_id == data.role_id,
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                return {"message": "Role already assigned"}

            session.add(
                UserRole(
                    user_id=target_user_id,
                    role_id=data.role_id,
                    assigned_at=datetime.now(UTC),
                )
            )
            await session.commit()
            return {"message": f"Role '{role.slug}' assigned to user"}

    @delete(
        "/users/{target_user_id:uuid}/roles/{role_id:uuid}",
        summary="Remove role from user",
    )
    async def remove_role(self, target_user_id: UUID, role_id: UUID) -> None:
        async with alchemy.get_session() as session:
            from sqlalchemy import select

            stmt = select(UserRole).where(
                UserRole.user_id == target_user_id,
                UserRole.role_id == role_id,
            )
            result = await session.execute(stmt)
            user_role = result.scalar_one_or_none()
            if not user_role:
                raise NotFoundException("User-role assignment not found")

            await session.delete(user_role)
            await session.commit()
