"""Integration tests for Evaluations and EvaluationSets CRUD."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.evaluations.service import EvaluationsService
from core.domain.evaluation_sets.service import EvaluationSetsService


@pytest.mark.integration
class TestEvaluationsCRUD:
    async def test_create_evaluation(self, db_session):
        service = EvaluationsService(session=db_session)
        obj = await service.create(
            {
                "status": "pending",
                "type": "rag",
                "test_sets": [{"name": "set-1"}],
            }
        )
        assert obj.id is not None
        assert obj.type == "rag"

    async def test_update_evaluation_status(self, db_session):
        service = EvaluationsService(session=db_session)
        created = await service.create({"status": "pending", "type": "rag"})
        updated = await service.update(
            {"status": "completed", "results": {"accuracy": 0.95}},
            item_id=created.id,
        )
        assert updated.status == "completed"
        assert updated.results["accuracy"] == 0.95


@pytest.mark.integration
class TestEvaluationSetsCRUD:
    async def test_create_evaluation_set(self, db_session):
        service = EvaluationSetsService(session=db_session)
        obj = await service.create(
            {
                "name": "Test Set",
                "system_name": f"eval-set-{uuid4().hex[:8]}",
                "type": "rag",
                "items": [
                    {
                        "question": "What is AI?",
                        "expected_answer": "Artificial Intelligence",
                    },
                ],
            }
        )
        assert obj.id is not None
        assert len(obj.items) == 1

    async def test_update_evaluation_set_items(self, db_session):
        service = EvaluationSetsService(session=db_session)
        created = await service.create(
            {
                "name": "Update Set",
                "system_name": f"eval-set-{uuid4().hex[:8]}",
                "type": "rag",
                "items": [],
            }
        )
        updated = await service.update(
            {"items": [{"question": "New Q?", "expected_answer": "New A"}]},
            item_id=created.id,
        )
        assert len(updated.items) == 1
