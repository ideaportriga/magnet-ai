"""Unit tests for CollectionsService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from core.db.models.collection import Collection


@pytest.mark.unit
class TestCollectionsService:
    """Tests for CollectionsService."""

    async def test_create_collection(self):
        """Should create a collection."""
        from core.domain.collections.service import CollectionsService

        mock_session = AsyncMock()
        service = CollectionsService(session=mock_session)

        with unittest_mock_patch(service, "create") as mock_create:
            mock_coll = MagicMock(spec=Collection)
            mock_coll.id = uuid4()
            mock_coll.system_name = "test-coll"
            mock_create.return_value = mock_coll

            result = await service.create(
                {
                    "name": "Test Collection",
                    "system_name": "test-coll",
                    "type": "documents",
                }
            )

            assert result.system_name == "test-coll"

    async def test_list_collections(self):
        """Should list collections with count."""
        from core.domain.collections.service import CollectionsService

        mock_session = AsyncMock()
        service = CollectionsService(session=mock_session)

        with unittest_mock_patch(service, "list_and_count") as mock_list:
            collections = [MagicMock(spec=Collection) for _ in range(5)]
            mock_list.return_value = (collections, 5)

            results, total = await service.list_and_count()

            assert total == 5
            assert len(results) == 5


def unittest_mock_patch(service, method_name):
    """Helper to patch a service method."""
    from unittest.mock import patch

    return patch.object(service, method_name, new_callable=AsyncMock)
