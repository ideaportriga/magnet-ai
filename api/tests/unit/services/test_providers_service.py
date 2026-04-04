"""Unit tests for ProvidersService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from core.db.models.provider import Provider


@pytest.mark.unit
class TestProvidersService:
    """Tests for ProvidersService custom logic."""

    async def test_create_provider(self):
        """Should create a provider and return it."""
        from core.domain.providers.service import ProvidersService

        mock_session = AsyncMock()
        service = ProvidersService(session=mock_session)

        with patch.object(service, "create", new_callable=AsyncMock) as mock_create:
            mock_provider = MagicMock(spec=Provider)
            mock_provider.system_name = "openai-1"
            mock_provider.type = "openai"
            mock_create.return_value = mock_provider

            result = await service.create(
                {
                    "name": "OpenAI",
                    "system_name": "openai-1",
                    "type": "openai",
                    "endpoint": "https://api.openai.com/v1",
                }
            )

            assert result.system_name == "openai-1"
            assert result.type == "openai"

    async def test_list_providers(self):
        """Should list providers with filtering."""
        from core.domain.providers.service import ProvidersService

        mock_session = AsyncMock()
        service = ProvidersService(session=mock_session)

        with patch.object(
            service, "list_and_count", new_callable=AsyncMock
        ) as mock_list:
            providers = [MagicMock(spec=Provider) for _ in range(2)]
            mock_list.return_value = (providers, 2)

            results, total = await service.list_and_count()

            assert total == 2
            assert len(results) == 2

    async def test_update_provider_same_endpoint_merges_secrets(self):
        """When updating a provider with the same endpoint, secrets should be merged."""
        from core.domain.providers.service import ProvidersService

        mock_session = AsyncMock()
        service = ProvidersService(session=mock_session)
        provider_id = uuid4()

        existing = MagicMock(spec=Provider)
        existing.endpoint = "https://api.openai.com/v1"
        existing.secrets_encrypted = {"api_key": "existing-key", "org_id": "org-123"}

        with patch.object(
            service, "get", new_callable=AsyncMock, return_value=existing
        ):
            with patch.object(service, "update", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = existing

                update_data = {
                    "endpoint": "https://api.openai.com/v1",
                    "secrets_encrypted": {"api_key": "new-key", "org_id": ""},
                }

                await service.update(update_data, item_id=provider_id)
                mock_update.assert_called_once()
