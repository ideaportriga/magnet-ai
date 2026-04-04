"""Integration tests for Agents CRUD against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.agents.service import AgentsService


@pytest.mark.integration
class TestAgentsCRUD:
    """Full CRUD lifecycle for Agents with real DB."""

    async def test_create_agent(self, db_session):
        service = AgentsService(session=db_session)
        obj = await service.create(
            {
                "name": "Integration Agent",
                "system_name": f"int-agent-{uuid4().hex[:8]}",
                "description": "Created in integration test",
                "category": "test",
                "active_variant": "default",
                "variants": [{"name": "default", "system_prompt": "test"}],
            }
        )
        assert obj.id is not None
        assert obj.name == "Integration Agent"

    async def test_read_agent(self, db_session):
        service = AgentsService(session=db_session)
        created = await service.create(
            {
                "name": "Read Agent",
                "system_name": f"read-agent-{uuid4().hex[:8]}",
            }
        )
        fetched = await service.get(created.id)
        assert fetched.id == created.id
        assert fetched.name == "Read Agent"

    async def test_update_agent(self, db_session):
        service = AgentsService(session=db_session)
        created = await service.create(
            {
                "name": "Before Update",
                "system_name": f"upd-agent-{uuid4().hex[:8]}",
            }
        )
        updated = await service.update({"name": "After Update"}, item_id=created.id)
        assert updated.name == "After Update"

    async def test_delete_agent(self, db_session):
        service = AgentsService(session=db_session)
        created = await service.create(
            {
                "name": "Delete Me",
                "system_name": f"del-agent-{uuid4().hex[:8]}",
            }
        )
        await service.delete(created.id)

        with pytest.raises(Exception):
            await service.get(created.id)

    async def test_list_agents(self, db_session):
        service = AgentsService(session=db_session)
        for i in range(3):
            await service.create(
                {
                    "name": f"List Agent {i}",
                    "system_name": f"list-agent-{uuid4().hex[:8]}",
                }
            )

        results, total = await service.list_and_count()
        assert total >= 3

    async def test_get_by_system_name(self, db_session):
        service = AgentsService(session=db_session)
        sn = f"sn-agent-{uuid4().hex[:8]}"
        await service.create({"name": "SN Agent", "system_name": sn})

        fetched = await service.get_one(system_name=sn)
        assert fetched.system_name == sn

    async def test_unique_system_name_constraint(self, db_session):
        service = AgentsService(session=db_session)
        sn = f"unique-agent-{uuid4().hex[:8]}"
        await service.create({"name": "First", "system_name": sn})

        with pytest.raises(Exception):
            await service.create({"name": "Duplicate", "system_name": sn})
