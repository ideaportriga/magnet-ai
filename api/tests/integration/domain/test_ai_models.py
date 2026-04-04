"""Integration tests for AI Models CRUD against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.ai_models.service import AIModelsService


@pytest.mark.integration
class TestAIModelsCRUD:
    """Full CRUD lifecycle for AI Models."""

    async def test_create_ai_model(self, db_session):
        service = AIModelsService(session=db_session)
        obj = await service.create(
            {
                "name": "GPT-4o",
                "system_name": f"gpt4o-{uuid4().hex[:8]}",
                "provider_name": "openai",
                "ai_model": "gpt-4o",
                "display_name": "GPT-4o",
                "type": "chat",
                "tool_calling": True,
            }
        )
        assert obj.id is not None
        assert obj.tool_calling is True

    async def test_read_ai_model(self, db_session):
        service = AIModelsService(session=db_session)
        sn = f"model-{uuid4().hex[:8]}"
        created = await service.create(
            {
                "name": "Read Model",
                "system_name": sn,
                "provider_name": "azure",
                "ai_model": "gpt-4o",
                "display_name": "Read Model",
                "type": "chat",
            }
        )
        fetched = await service.get(created.id)
        assert fetched.system_name == sn

    async def test_update_ai_model(self, db_session):
        service = AIModelsService(session=db_session)
        created = await service.create(
            {
                "name": "Old Model",
                "system_name": f"model-{uuid4().hex[:8]}",
                "provider_name": "openai",
                "ai_model": "gpt-3.5",
                "display_name": "Old Model",
                "type": "chat",
            }
        )
        updated = await service.update(
            {"ai_model": "gpt-4o", "display_name": "New Model"},
            item_id=created.id,
        )
        assert updated.ai_model == "gpt-4o"

    async def test_boolean_fields(self, db_session):
        """Boolean fields should persist correctly."""
        service = AIModelsService(session=db_session)
        created = await service.create(
            {
                "name": "Bool Model",
                "system_name": f"model-{uuid4().hex[:8]}",
                "provider_name": "openai",
                "ai_model": "gpt-4o",
                "display_name": "Bool Model",
                "type": "chat",
                "json_mode": True,
                "json_schema": True,
                "tool_calling": True,
                "reasoning": True,
                "is_default": True,
            }
        )
        fetched = await service.get(created.id)
        assert fetched.json_mode is True
        assert fetched.json_schema is True
        assert fetched.tool_calling is True
        assert fetched.reasoning is True
        assert fetched.is_default is True

    async def test_delete_ai_model(self, db_session):
        service = AIModelsService(session=db_session)
        created = await service.create(
            {
                "name": "Del Model",
                "system_name": f"model-{uuid4().hex[:8]}",
                "provider_name": "openai",
                "ai_model": "gpt-4o",
                "display_name": "Del Model",
                "type": "chat",
            }
        )
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)
