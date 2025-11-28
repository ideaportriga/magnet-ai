from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.ai_app.ai_app import AIApp


class AiAppsService(service.SQLAlchemyAsyncRepositoryService[AIApp]):
    """AI Apps service."""

    class Repo(repository.SQLAlchemyAsyncRepository[AIApp]):
        """AI Apps repository."""

        model_type = AIApp

    repository_type = Repo
