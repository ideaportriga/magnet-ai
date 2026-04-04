"""Integration tests for Prompts CRUD against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.prompts.service import PromptsService


@pytest.mark.integration
class TestPromptsCRUD:
    """Full CRUD lifecycle for Prompts."""

    async def test_create_prompt(self, db_session):
        service = PromptsService(session=db_session)
        obj = await service.create(
            {
                "name": "Test Prompt",
                "system_name": f"prompt-{uuid4().hex[:8]}",
                "active_variant": "v1",
                "variants": [
                    {"name": "v1", "template": "Hello, {{name}}!"},
                    {"name": "v2", "template": "Hi {{name}}, how are you?"},
                ],
            }
        )
        assert obj.id is not None
        assert len(obj.variants) == 2

    async def test_read_prompt(self, db_session):
        service = PromptsService(session=db_session)
        sn = f"prompt-{uuid4().hex[:8]}"
        created = await service.create(
            {
                "name": "Read Prompt",
                "system_name": sn,
                "active_variant": "default",
                "variants": [{"name": "default", "template": "test"}],
            }
        )
        fetched = await service.get(created.id)
        assert fetched.system_name == sn

    async def test_update_prompt_variant(self, db_session):
        service = PromptsService(session=db_session)
        created = await service.create(
            {
                "name": "Update Prompt",
                "system_name": f"prompt-{uuid4().hex[:8]}",
                "active_variant": "v1",
                "variants": [{"name": "v1", "template": "old"}],
            }
        )
        updated = await service.update(
            {
                "active_variant": "v2",
                "variants": [
                    {"name": "v1", "template": "old"},
                    {"name": "v2", "template": "new"},
                ],
            },
            item_id=created.id,
        )
        assert updated.active_variant == "v2"
        assert len(updated.variants) == 2

    async def test_delete_prompt(self, db_session):
        service = PromptsService(session=db_session)
        created = await service.create(
            {
                "name": "Delete Prompt",
                "system_name": f"prompt-{uuid4().hex[:8]}",
            }
        )
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)
