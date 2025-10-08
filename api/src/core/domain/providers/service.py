from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.provider import Provider


class ProvidersService(service.SQLAlchemyAsyncRepositoryService[Provider]):
    """Providers service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Provider]):
        """Providers repository."""

        model_type = Provider

    repository_type = Repo
