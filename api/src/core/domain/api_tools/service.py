from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.api_tool.api_tool import APITool


class ApiToolsService(service.SQLAlchemyAsyncRepositoryService[APITool]):
    """API Tools service."""

    class Repo(repository.SQLAlchemyAsyncRepository[APITool]):
        """API Tools repository."""

        model_type = APITool

    repository_type = Repo
