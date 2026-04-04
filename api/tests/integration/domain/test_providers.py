"""Integration tests for Providers CRUD against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.providers.service import ProvidersService


@pytest.mark.integration
class TestProvidersCRUD:
    """Full CRUD lifecycle for Providers with real DB."""

    async def test_create_provider(self, db_session):
        service = ProvidersService(session=db_session)
        obj = await service.create(
            {
                "name": "Test Provider",
                "system_name": f"provider-{uuid4().hex[:8]}",
                "type": "openai",
                "endpoint": "https://api.openai.com/v1",
            }
        )
        assert obj.id is not None
        assert obj.type == "openai"

    async def test_read_provider(self, db_session):
        service = ProvidersService(session=db_session)
        sn = f"provider-{uuid4().hex[:8]}"
        created = await service.create(
            {"name": "Read Provider", "system_name": sn, "type": "azure"}
        )
        fetched = await service.get(created.id)
        assert fetched.system_name == sn

    async def test_update_provider(self, db_session):
        service = ProvidersService(session=db_session)
        created = await service.create(
            {
                "name": "Old Name",
                "system_name": f"provider-{uuid4().hex[:8]}",
                "type": "openai",
                "endpoint": "https://old.api.com",
            }
        )
        updated = await service.update({"name": "New Name"}, item_id=created.id)
        assert updated.name == "New Name"

    async def test_delete_provider(self, db_session):
        service = ProvidersService(session=db_session)
        created = await service.create(
            {
                "name": "Delete Me",
                "system_name": f"provider-{uuid4().hex[:8]}",
                "type": "openai",
            }
        )
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)

    async def test_provider_jsonb_connection_config(self, db_session):
        """JSONB fields should round-trip correctly."""
        service = ProvidersService(session=db_session)
        config = {"api_version": "2024-01", "max_tokens": 4096}
        created = await service.create(
            {
                "name": "JSONB Provider",
                "system_name": f"provider-{uuid4().hex[:8]}",
                "type": "azure",
                "connection_config": config,
            }
        )
        fetched = await service.get(created.id)
        assert fetched.connection_config == config
