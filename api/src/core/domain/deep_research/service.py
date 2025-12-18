"""Deep Research domain services."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.deep_research import DeepResearchConfig, DeepResearchRun


class DeepResearchConfigService(service.SQLAlchemyAsyncRepositoryService[DeepResearchConfig]):
    """Deep Research Config service."""

    class Repo(repository.SQLAlchemyAsyncRepository[DeepResearchConfig]):
        """Deep Research Config repository."""

        model_type = DeepResearchConfig

    repository_type = Repo


class DeepResearchRunService(service.SQLAlchemyAsyncRepositoryService[DeepResearchRun]):
    """Deep Research Run service."""

    class Repo(repository.SQLAlchemyAsyncRepository[DeepResearchRun]):
        """Deep Research Run repository."""

        model_type = DeepResearchRun

    repository_type = Repo
