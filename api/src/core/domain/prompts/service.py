from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.prompt import Prompt


class PromptsService(service.SQLAlchemyAsyncRepositoryService[Prompt]):
    """Prompts service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Prompt]):
        """Prompts repository."""

        model_type = Prompt

    repository_type = Repo
