"""Integration tests for Jobs CRUD against real PostgreSQL."""

from __future__ import annotations


import pytest

from core.domain.jobs.service import JobsService


@pytest.mark.integration
class TestJobsCRUD:
    """CRUD lifecycle for Jobs."""

    async def test_create_job(self, db_session):
        service = JobsService(session=db_session)
        obj = await service.create(
            {
                "status": "pending",
                "definition": {"type": "sync", "collection": "test-coll"},
            }
        )
        assert obj.id is not None
        assert obj.status == "pending"

    async def test_update_job_status(self, db_session):
        service = JobsService(session=db_session)
        created = await service.create({"status": "pending", "definition": {}})
        updated = await service.update({"status": "running"}, item_id=created.id)
        assert updated.status == "running"

    async def test_list_jobs(self, db_session):
        service = JobsService(session=db_session)
        for status in ["pending", "running", "completed"]:
            await service.create({"status": status, "definition": {}})

        results, total = await service.list_and_count()
        assert total >= 3

    async def test_delete_job(self, db_session):
        service = JobsService(session=db_session)
        created = await service.create({"status": "pending", "definition": {}})
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)

    async def test_jsonb_definition(self, db_session):
        """JSONB definition should round-trip."""
        service = JobsService(session=db_session)
        definition = {
            "type": "evaluation",
            "config": {"model": "gpt-4o", "max_tokens": 1000},
            "items": [{"question": "test?"}],
        }
        created = await service.create({"status": "pending", "definition": definition})
        fetched = await service.get(created.id)
        assert fetched.definition == definition
