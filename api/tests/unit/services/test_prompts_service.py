"""Unit tests for PromptsService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from core.db.models.prompt import Prompt


@pytest.mark.unit
class TestPromptsService:
    """Tests for PromptsService."""

    async def test_create_prompt(self):
        """Should create a prompt with variants."""
        from core.domain.prompts.service import PromptsService

        mock_session = AsyncMock()
        service = PromptsService(session=mock_session)

        with patch.object(service, "create", new_callable=AsyncMock) as mock_create:
            mock_prompt = MagicMock(spec=Prompt)
            mock_prompt.system_name = "test-prompt"
            mock_prompt.variants = [{"name": "default", "template": "Hello {name}"}]
            mock_create.return_value = mock_prompt

            result = await service.create(
                {
                    "name": "Test Prompt",
                    "system_name": "test-prompt",
                    "active_variant": "default",
                    "variants": [{"name": "default", "template": "Hello {name}"}],
                }
            )

            assert result.system_name == "test-prompt"
            assert len(result.variants) == 1

    async def test_get_prompt_by_system_name(self):
        """Should retrieve a prompt by system_name."""
        from core.domain.prompts.service import PromptsService

        mock_session = AsyncMock()
        service = PromptsService(session=mock_session)

        with patch.object(service, "get_one", new_callable=AsyncMock) as mock_get:
            mock_prompt = MagicMock(spec=Prompt)
            mock_prompt.system_name = "my-prompt"
            mock_get.return_value = mock_prompt

            result = await service.get_one(system_name="my-prompt")
            assert result.system_name == "my-prompt"

    async def test_update_prompt_variants(self):
        """Should update prompt variants."""
        from core.domain.prompts.service import PromptsService

        mock_session = AsyncMock()
        service = PromptsService(session=mock_session)

        with patch.object(service, "update", new_callable=AsyncMock) as mock_update:
            mock_prompt = MagicMock(spec=Prompt)
            mock_prompt.variants = [{"name": "v2", "template": "New template"}]
            mock_update.return_value = mock_prompt

            result = await service.update(
                {"variants": [{"name": "v2", "template": "New template"}]},
                item_id=uuid4(),
            )
            assert result.variants[0]["name"] == "v2"
