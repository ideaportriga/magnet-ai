"""
RAG Tools domain models and schemas.
"""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.rag_tool import RagTool


class RagToolsService(service.SQLAlchemyAsyncRepositoryService[RagTool]):
    """RAG Tools service."""

    class Repo(repository.SQLAlchemyAsyncRepository[RagTool]):
        """RAG Tools repository."""

        model_type = RagTool

    repository_type = Repo
