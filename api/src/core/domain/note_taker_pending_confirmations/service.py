from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.teams.note_taker_pending_confirmation import (
    NoteTakerPendingConfirmation,
)


class NoteTakerPendingConfirmationsService(
    service.SQLAlchemyAsyncRepositoryService[NoteTakerPendingConfirmation]
):
    """Pending speaker-mapping confirmations service.

    Replaces the legacy raw-asyncpg helpers in
    `services/agents/teams/note_taker_pending_store.py` so JSONB columns
    pass through the engine's serializer/deserializer instead of relying
    on per-connection asyncpg type codecs (the source of three earlier
    JSONB-decoding production bugs).
    """

    class Repo(repository.SQLAlchemyAsyncRepository[NoteTakerPendingConfirmation]):
        model_type = NoteTakerPendingConfirmation

    repository_type = Repo
