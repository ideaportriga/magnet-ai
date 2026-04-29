"""Repository / service for OAuth clients."""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.oauth.oauth_client import OAuthClient


class OAuthClientsService(service.SQLAlchemyAsyncRepositoryService[OAuthClient]):
    """OAuth clients service."""

    class Repo(repository.SQLAlchemyAsyncRepository[OAuthClient]):
        model_type = OAuthClient

    repository_type = Repo
