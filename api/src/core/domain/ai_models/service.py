from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.ai_model import AIModel


class AIModelsService(service.SQLAlchemyAsyncRepositoryService[AIModel]):
    """AI Models service."""

    class Repo(repository.SQLAlchemyAsyncRepository[AIModel]):
        """AI Models repository."""

        model_type = AIModel

    repository_type = Repo
