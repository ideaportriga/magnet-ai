"""
Roles domain service — Advanced Alchemy repository/service layer.
"""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.user.role import Role


class RolesService(service.SQLAlchemyAsyncRepositoryService[Role]):
    """Roles service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Role]):
        """Roles repository."""

        model_type = Role

    repository_type = Repo
