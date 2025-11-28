from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.api_key.api_key import APIKey


class APIKeysService(service.SQLAlchemyAsyncRepositoryService[APIKey]):
    """API Keys service."""

    class Repo(repository.SQLAlchemyAsyncRepository[APIKey]):
        """API Keys repository."""

        model_type = APIKey

    repository_type = Repo
