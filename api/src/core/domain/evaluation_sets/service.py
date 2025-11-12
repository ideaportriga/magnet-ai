from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.evaluation_set.evaluation_set import EvaluationSet


class EvaluationSetsService(service.SQLAlchemyAsyncRepositoryService[EvaluationSet]):
    """Evaluation Sets service."""

    class Repo(repository.SQLAlchemyAsyncRepository[EvaluationSet]):
        """Evaluation Sets repository."""

        model_type = EvaluationSet

    repository_type = Repo
