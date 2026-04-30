from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.transcription.transcription import Transcription


class TranscriptionsService(service.SQLAlchemyAsyncRepositoryService[Transcription]):
    """Transcriptions service.

    Backs the legacy `PgDataStorage` adapter that the STT pipeline consumes.
    All inserts/updates flow through the SQLAlchemy engine (whose JSON
    serializer/deserializer is configured at engine_factory time), so this
    domain is not affected by the asyncpg JSONB-codec races that motivated
    the architecture review.
    """

    class Repo(repository.SQLAlchemyAsyncRepository[Transcription]):
        model_type = Transcription

    repository_type = Repo
