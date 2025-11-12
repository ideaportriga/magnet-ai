"""
Retrieval Tools domain models and schemas.
"""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.retrieval_tool import RetrievalTool


class RetrievalToolsService(service.SQLAlchemyAsyncRepositoryService[RetrievalTool]):
    """Retrieval Tools service."""

    class Repo(repository.SQLAlchemyAsyncRepository[RetrievalTool]):
        """Retrieval Tools repository."""

        model_type = RetrievalTool

    repository_type = Repo
