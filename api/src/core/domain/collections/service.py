from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.collection.collection import Collection


class CollectionsService(service.SQLAlchemyAsyncRepositoryService[Collection]):
    """Collections service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Collection]):
        """Collections repository."""

        model_type = Collection

    repository_type = Repo
