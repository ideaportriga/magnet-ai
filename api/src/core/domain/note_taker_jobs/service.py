from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.teams.note_taker_job import NoteTakerJob


class NoteTakerJobsService(service.SQLAlchemyAsyncRepositoryService[NoteTakerJob]):
    """Note Taker preview jobs service."""

    class Repo(repository.SQLAlchemyAsyncRepository[NoteTakerJob]):
        """Note Taker Jobs repository."""

        model_type = NoteTakerJob

    repository_type = Repo
