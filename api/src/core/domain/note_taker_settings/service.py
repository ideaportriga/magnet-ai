from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.teams.note_taker_settings import NoteTakerSettings


class NoteTakerSettingsService(
    service.SQLAlchemyAsyncRepositoryService[NoteTakerSettings]
):
    """Note Taker settings service (advanced-alchemy).

    Currently most callers reach the table via `select(NoteTakerSettings)`
    directly through `async_session_maker`. This service is the migration
    target — new lookups should go through it so the controller / runtime
    in `services/agents/teams/` can shrink.
    """

    class Repo(repository.SQLAlchemyAsyncRepository[NoteTakerSettings]):
        model_type = NoteTakerSettings

    repository_type = Repo
