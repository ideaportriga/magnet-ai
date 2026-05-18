from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.teams.note_taker_integration_attempt import (
    NoteTakerIntegrationAttempt,
)


class NoteTakerIntegrationAttemptsService(
    service.SQLAlchemyAsyncRepositoryService[NoteTakerIntegrationAttempt]
):
    """Read + ops service for `note_taker_integration_attempt` rows.

    Used by the admin UI to inspect the outbox (which integration silently
    failed, how many retries it took, when the sweeper will pick it up
    next) and to force a manual retry by re-arming `next_retry_at` to now.
    """

    class Repo(repository.SQLAlchemyAsyncRepository[NoteTakerIntegrationAttempt]):
        model_type = NoteTakerIntegrationAttempt

    repository_type = Repo
