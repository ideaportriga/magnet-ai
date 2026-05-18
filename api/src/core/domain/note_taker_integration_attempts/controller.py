from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Optional
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, get, post
from litestar.exceptions import HTTPException
from litestar.params import Dependency, Parameter

from core.db.models.teams.note_taker_integration_attempt import (
    NoteTakerIntegrationAttempt,
)
from core.domain.note_taker_integration_attempts.service import (
    NoteTakerIntegrationAttemptsService,
)
from guards.permissions import Permission, require_permission

from .schemas import (
    IntegrationAttemptRetryResponse,
    NoteTakerIntegrationAttemptSchema,
)

_KNOWN_KINDS = frozenset({"confluence", "salesforce", "knowledge_graph"})
_KNOWN_STATUSES = frozenset({"pending", "done", "failed"})


class NoteTakerIntegrationAttemptsController(Controller):
    """Admin API for the note-taker outbox journal.

    Read endpoint gives operators a way to see which integration
    publishes silently dropped (`status='failed'`, `error_class`, last
    `finished_at`) without dropping into psql. The retry endpoint
    re-arms `next_retry_at` so the housekeeping sweeper can pick the
    row up on its next tick, and immediately enqueues a replay task
    for integration kinds that have one.
    """

    path = "/note-taker/integration-attempts"
    tags = ["Admin / Note Taker"]

    dependencies = providers.create_service_dependencies(
        NoteTakerIntegrationAttemptsService,
        "attempts_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "pagination_size": 50,
            "sort_field": "started_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.NOTE_TAKER_READ)])
    async def list_attempts(
        self,
        attempts_service: NoteTakerIntegrationAttemptsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
        job_id: Annotated[
            Optional[str],
            Parameter(query="job_id", required=False, default=None),
        ] = None,
        integration_kind: Annotated[
            Optional[str],
            Parameter(query="integration_kind", required=False, default=None),
        ] = None,
        status: Annotated[
            Optional[str],
            Parameter(query="status", required=False, default=None),
        ] = None,
    ) -> service.OffsetPagination[NoteTakerIntegrationAttemptSchema]:
        """List integration attempts with optional filters.

        Filters use exact match — no fuzzy search; the outbox is small
        enough that paginated exact queries are cheap and pages cleanly
        compose under the admin UI's typical "show me failed
        confluence pushes for job X" workflow.
        """
        if integration_kind and integration_kind not in _KNOWN_KINDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid integration_kind={integration_kind!r}; "
                    f"expected one of {sorted(_KNOWN_KINDS)}."
                ),
            )
        if status and status not in _KNOWN_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid status={status!r}; expected one of {sorted(_KNOWN_STATUSES)}."
                ),
            )

        extra: list[Any] = list(filters)
        if job_id:
            extra.append(NoteTakerIntegrationAttempt.job_id == job_id)
        if integration_kind:
            extra.append(
                NoteTakerIntegrationAttempt.integration_kind == integration_kind
            )
        if status:
            extra.append(NoteTakerIntegrationAttempt.status == status)

        results, total = await attempts_service.list_and_count(*extra)
        return attempts_service.to_schema(
            results,
            total,
            filters=filters,
            schema_type=NoteTakerIntegrationAttemptSchema,
        )

    @get(
        "/{attempt_id:uuid}",
        guards=[require_permission(Permission.NOTE_TAKER_READ)],
    )
    async def get_attempt(
        self,
        attempts_service: NoteTakerIntegrationAttemptsService,
        attempt_id: UUID,
    ) -> NoteTakerIntegrationAttemptSchema:
        obj = await attempts_service.get(attempt_id)
        return attempts_service.to_schema(
            obj, schema_type=NoteTakerIntegrationAttemptSchema
        )

    @post(
        "/{attempt_id:uuid}/retry",
        guards=[require_permission(Permission.NOTE_TAKER_WRITE)],
    )
    async def retry_attempt(
        self,
        attempts_service: NoteTakerIntegrationAttemptsService,
        attempt_id: UUID,
    ) -> IntegrationAttemptRetryResponse:
        """Force a retry of one failed integration attempt.

        Sets `next_retry_at = now()` so the next sweeper tick can pick
        it up. If the integration kind has a replay task, kiq() it right
        away so operators do not have to wait for the cron beat.
        """
        obj = await attempts_service.get(attempt_id)
        if obj.status != "failed":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Attempt is not in 'failed' state (status={obj.status!r}); "
                    "only failed rows are eligible for retry."
                ),
            )
        if obj.retry_payload is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Attempt has no retry_payload — was recorded before the "
                    "outbox column was populated. Use rerun_postprocessing "
                    "on the parent job instead."
                ),
            )

        # Re-arm next_retry_at in one statement; the sweeper acquires
        # rows via `next_retry_at <= now()` so this immediately
        # surfaces them on the next tick.
        from sqlalchemy import update

        session = attempts_service.repository.session
        await session.execute(
            update(NoteTakerIntegrationAttempt)
            .where(NoteTakerIntegrationAttempt.id == attempt_id)
            .values(next_retry_at=datetime.now(timezone.utc))
        )
        await session.commit()

        immediately_requeued = False
        replay_task = None
        if obj.integration_kind == "knowledge_graph":
            from tasks.definitions import note_taker_kg_ingest_bg_task

            replay_task = note_taker_kg_ingest_bg_task
        elif obj.integration_kind == "salesforce":
            from tasks.definitions import note_taker_salesforce_publish_bg_task

            replay_task = note_taker_salesforce_publish_bg_task
        elif obj.integration_kind == "confluence":
            from tasks.definitions import note_taker_confluence_publish_bg_task

            replay_task = note_taker_confluence_publish_bg_task

        if replay_task is not None:
            try:
                await replay_task.kiq(**(obj.retry_payload or {}))
                immediately_requeued = True
            except Exception as exc:  # noqa: BLE001
                # If the broker rejects, the sweeper will pick it up
                # on the next 5-min beat thanks to the next_retry_at
                # we just set. Surface the failure cause to the caller.
                raise HTTPException(
                    status_code=502,
                    detail=f"Replay kiq() failed: {type(exc).__name__}: {exc}",
                ) from exc

        refreshed = await attempts_service.get(attempt_id)
        return IntegrationAttemptRetryResponse(
            id=refreshed.id,
            integration_kind=refreshed.integration_kind,
            job_id=refreshed.job_id,
            next_retry_at=refreshed.next_retry_at,
            immediately_requeued=immediately_requeued,
        )
