"""Integration tests for Users, Roles, Groups against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.users.service import UsersService


@pytest.mark.integration
class TestUsersCRUD:
    """Full CRUD lifecycle for Users."""

    async def test_create_user(self, db_session):
        service = UsersService(session=db_session)
        obj = await service.create(
            {
                "email": f"test-{uuid4().hex[:8]}@test.com",
                "name": "Test User",
                "is_active": True,
            }
        )
        assert obj.id is not None
        assert obj.is_active is True

    async def test_unique_email_constraint(self, db_session):
        service = UsersService(session=db_session)
        email = f"unique-{uuid4().hex[:8]}@test.com"
        await service.create({"email": email, "name": "First"})

        with pytest.raises(Exception):
            await service.create({"email": email, "name": "Duplicate"})

    async def test_update_user(self, db_session):
        service = UsersService(session=db_session)
        created = await service.create(
            {"email": f"upd-{uuid4().hex[:8]}@test.com", "name": "Old Name"}
        )
        updated = await service.update({"name": "New Name"}, item_id=created.id)
        assert updated.name == "New Name"

    async def test_deactivate_user(self, db_session):
        service = UsersService(session=db_session)
        created = await service.create(
            {"email": f"deact-{uuid4().hex[:8]}@test.com", "is_active": True}
        )
        updated = await service.update({"is_active": False}, item_id=created.id)
        assert updated.is_active is False

    async def test_delete_user(self, db_session):
        service = UsersService(session=db_session)
        created = await service.create({"email": f"del-{uuid4().hex[:8]}@test.com"})
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)

    async def test_list_users(self, db_session):
        service = UsersService(session=db_session)
        for i in range(3):
            await service.create(
                {"email": f"list-{uuid4().hex[:8]}@test.com", "name": f"User {i}"}
            )
        results, total = await service.list_and_count()
        assert total >= 3
