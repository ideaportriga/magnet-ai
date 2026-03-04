"""Prompt Queue domain services."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.prompt_queue import PromptQueueConfig


class PromptQueueConfigService(
    service.SQLAlchemyAsyncRepositoryService[PromptQueueConfig]
):
    """Prompt Queue Config service."""

    class Repo(repository.SQLAlchemyAsyncRepository[PromptQueueConfig]):
        """Prompt Queue Config repository."""

        model_type = PromptQueueConfig

    repository_type = Repo
