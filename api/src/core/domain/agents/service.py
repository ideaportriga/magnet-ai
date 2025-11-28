from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.agent import Agent


class AgentsService(service.SQLAlchemyAsyncRepositoryService[Agent]):
    """Agents service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Agent]):
        """Agents repository."""

        model_type = Agent

    repository_type = Repo
