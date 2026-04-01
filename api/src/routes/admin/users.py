"""Admin endpoints for user management."""

from __future__ import annotations

from uuid import UUID

from litestar import Controller, get, patch

from core.config.app import alchemy
from core.domain.users.schemas import User as UserSchema
from core.domain.users.schemas import UserUpdate
from core.domain.users.service import UsersService


class UsersController(Controller):
    path = "/users"
    tags = ["Admin / Users"]

    @get("/", summary="List users")
    async def list_users(self) -> list[UserSchema]:
        async with alchemy.get_session() as session:
            service = UsersService(session=session)
            users = await service.list()
            return [service.to_schema(u, schema_type=UserSchema) for u in users]

    @get("/{id:uuid}", summary="Get user by ID")
    async def get_user(self, id: UUID) -> UserSchema:
        async with alchemy.get_session() as session:
            service = UsersService(session=session)
            user = await service.get(id)
            return service.to_schema(user, schema_type=UserSchema)

    @patch("/{id:uuid}", summary="Update user")
    async def update_user(self, id: UUID, data: UserUpdate) -> UserSchema:
        async with alchemy.get_session() as session:
            service = UsersService(session=session)
            user = await service.get(id)
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)
            user = await service.update(user, auto_commit=True)
            return service.to_schema(user, schema_type=UserSchema)
