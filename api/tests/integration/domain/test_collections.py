"""Integration tests for Collections CRUD against real PostgreSQL."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.collections.service import CollectionsService


@pytest.mark.integration
class TestCollectionsCRUD:
    """Full CRUD lifecycle for Collections."""

    async def test_create_collection(self, db_session):
        service = CollectionsService(session=db_session)
        obj = await service.create(
            {
                "name": "Test Collection",
                "system_name": f"coll-{uuid4().hex[:8]}",
                "type": "documents",
                "source": {"type": "upload"},
                "chunking": {"method": "semantic", "size": 512},
                "indexing": {"method": "pgvector"},
            }
        )
        assert obj.id is not None
        assert obj.type == "documents"

    async def test_read_collection(self, db_session):
        service = CollectionsService(session=db_session)
        sn = f"coll-{uuid4().hex[:8]}"
        created = await service.create(
            {"name": "Read Coll", "system_name": sn, "type": "docs"}
        )
        fetched = await service.get(created.id)
        assert fetched.system_name == sn

    async def test_update_collection(self, db_session):
        service = CollectionsService(session=db_session)
        created = await service.create(
            {"name": "Old Coll", "system_name": f"coll-{uuid4().hex[:8]}"}
        )
        updated = await service.update({"name": "New Coll"}, item_id=created.id)
        assert updated.name == "New Coll"

    async def test_jsonb_source_config(self, db_session):
        """JSONB source config should round-trip."""
        service = CollectionsService(session=db_session)
        source = {
            "type": "sharepoint",
            "site_url": "https://company.sharepoint.com",
            "doc_lib": "Documents",
        }
        created = await service.create(
            {
                "name": "SP Coll",
                "system_name": f"coll-{uuid4().hex[:8]}",
                "source": source,
            }
        )
        fetched = await service.get(created.id)
        assert fetched.source == source

    async def test_delete_collection(self, db_session):
        service = CollectionsService(session=db_session)
        created = await service.create(
            {"name": "Delete Coll", "system_name": f"coll-{uuid4().hex[:8]}"}
        )
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)
