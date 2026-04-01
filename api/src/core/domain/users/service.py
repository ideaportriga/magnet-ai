"""
Users domain service — Advanced Alchemy repository/service layer.
"""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.user.user import User


class UsersService(service.SQLAlchemyAsyncRepositoryService[User]):
    """Users service."""

    class Repo(repository.SQLAlchemyAsyncRepository[User]):
        """Users repository."""

        model_type = User

    repository_type = Repo
