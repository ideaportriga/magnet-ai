from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.metric import Metric


class MetricsService(service.SQLAlchemyAsyncRepositoryService[Metric]):
    """Metrics service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Metric]):
        """Metrics repository."""

        model_type = Metric

    repository_type = Repo
