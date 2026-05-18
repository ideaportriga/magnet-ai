from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, Request, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body

from core.db.models.teams.note_taker_job import NoteTakerJob as NoteTakerJobModel
from core.domain.note_taker_jobs.service import NoteTakerJobsService
from guards.permissions import Permission, require_permission
from services.access_control.record_level import (
    enforce_action_or_403,
    enforce_view_or_404,
    visibility_filter_for,
)

from .schemas import NoteTakerJobCreate, NoteTakerJobSchema
from .status import JobStatus

if TYPE_CHECKING:
    pass


NOTE_TAKER_RESOURCE_TYPE = "note_taker"


def _stamp_owner_fields(data: Any, request: Request) -> None:
    """Populate `tenant_id`, `owner_id`, and legacy `user_id` from auth.

    Mirrors `force_create_fields` but writes onto a Pydantic create-schema
    instance instead of a dict, because `NoteTakerJobCreate` is the typed
    payload the service layer expects. The legacy `user_id` (Text) is kept
    in sync so the Teams-side ownership check (`/process-transcript-job`)
    continues to recognize jobs created via the admin panel.
    """
    auth = request.scope.get("auth")
    if auth is None:
        return
    tenant_id = getattr(auth, "tenant_id", None)
    user = getattr(auth, "user", None)
    if tenant_id is not None and hasattr(data, "tenant_id"):
        data.tenant_id = tenant_id
    if user is not None and getattr(user, "id", None):
        if hasattr(data, "owner_id"):
            data.owner_id = user.id
        if hasattr(data, "user_id"):
            data.user_id = str(user.id)


class NoteTakerJobsController(Controller):
    """Admin API for note-taker preview jobs."""

    path = "/note-taker/jobs"
    tags = ["Admin / Note Taker"]

    dependencies = providers.create_service_dependencies(
        NoteTakerJobsService,
        "jobs_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "pagination_size": 50,
        },
    )

    @get(
        "/{settings_id:uuid}",
        guards=[require_permission(Permission.NOTE_TAKER_READ)],
    )
    async def list_jobs(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
    ) -> list[NoteTakerJobSchema]:
        """List preview jobs for a settings record, scoped by record visibility."""
        extra_filters: list[Any] = [
            NoteTakerJobsService.Repo.model_type.settings_id == settings_id,
        ]
        where = await visibility_filter_for(
            jobs_service,
            request=request,
            model=NoteTakerJobModel,
            resource_type=NOTE_TAKER_RESOURCE_TYPE,
        )
        if where is not None:
            extra_filters.append(where)

        results, _ = await jobs_service.list_and_count(*extra_filters)
        return [
            jobs_service.to_schema(r, schema_type=NoteTakerJobSchema) for r in results
        ]

    @get(
        "/{settings_id:uuid}/{job_id:uuid}",
        guards=[require_permission(Permission.NOTE_TAKER_READ)],
    )
    async def get_job(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        job_id: UUID,
        request: Request,
    ) -> NoteTakerJobSchema:
        """Get a single preview job (404 if no view permission on the record)."""
        obj = await jobs_service.get(job_id)
        await enforce_view_or_404(
            jobs_service,
            request=request,
            resource=obj,
            resource_type=NOTE_TAKER_RESOURCE_TYPE,
        )
        return jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

    @post(
        "/{settings_id:uuid}/run",
        guards=[require_permission(Permission.NOTE_TAKER_WRITE)],
    )
    async def run_preview(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
        data: NoteTakerJobCreate = Body(),
    ) -> NoteTakerJobSchema:
        """Submit a new preview transcription job."""

        # SSRF guard: reject internal / loopback / link-local URLs before
        # the worker tries to fetch them. See P2-5.
        if data.source_url:
            from services.agents.teams.url_safety import (
                UnsafeSourceURLError,
                check_source_url,
            )

            try:
                check_source_url(data.source_url)
            except UnsafeSourceURLError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Unsafe source URL: {exc}"
                ) from exc

        data.settings_id = settings_id
        _stamp_owner_fields(data, request)

        obj = await jobs_service.create(data)
        job = jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

        from tasks.definitions import note_taker_preview_bg_task

        await note_taker_preview_bg_task.kiq(
            job_id=str(job.id),
            settings_id=str(settings_id),
            source_url=data.source_url,
            participants=data.participants or [],
            stt_model_system_name=data.stt_model_system_name,
        )

        return job

    @post(
        "/{settings_id:uuid}/run-upload",
        guards=[require_permission(Permission.NOTE_TAKER_WRITE)],
    )
    async def run_preview_upload(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
        data: Annotated[
            dict[str, Any], Body(media_type=RequestEncodingType.MULTI_PART)
        ],
    ) -> NoteTakerJobSchema:
        """Submit a new preview transcription job with a file upload.

        The bytes are staged into object storage here (synchronously, before
        the job is enqueued) so that taskiq workers running in a separate
        process can pick the job up. URL and upload paths share the same
        background task.
        """
        from services.agents.teams.note_taker_files import _upload_stream_to_object

        file: UploadFile | None = data.get("file")  # type: ignore[assignment]
        if file is None:
            raise HTTPException(status_code=400, detail="No file provided.")

        file_bytes = await file.read()
        upload_filename = file.filename
        upload_content_type = file.content_type or "application/octet-stream"

        participants_raw = data.get("participants") or ""
        if isinstance(participants_raw, str):
            participants = [p.strip() for p in participants_raw.split(",") if p.strip()]
        elif isinstance(participants_raw, list):
            participants = [str(p) for p in participants_raw if p]
        else:
            participants = []

        stt_model_system_name = str(data.get("stt_model_system_name") or "") or None

        create_data = NoteTakerJobCreate(
            settings_id=settings_id,
            participants=participants,
        )
        _stamp_owner_fields(create_data, request)
        obj = await jobs_service.create(create_data)
        job = jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

        async def _bytes_iter(payload: bytes, chunk: int = 65536):
            for i in range(0, len(payload), chunk):
                yield payload[i : i + chunk]

        object_key = await _upload_stream_to_object(
            stream=_bytes_iter(file_bytes),
            size=len(file_bytes),
            content_type=upload_content_type,
            filename=upload_filename or f"preview_{job.id}",
        )

        from tasks.definitions import note_taker_preview_bg_task

        await note_taker_preview_bg_task.kiq(
            job_id=str(job.id),
            settings_id=str(settings_id),
            source_url=None,
            object_key=object_key,
            upload_filename=upload_filename,
            upload_content_type=upload_content_type,
            participants=participants,
            stt_model_system_name=stt_model_system_name,
        )

        return job

    @post(
        "/{settings_id:uuid}/rerun",
        guards=[require_permission(Permission.NOTE_TAKER_WRITE)],
    )
    async def rerun_postprocessing(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
        data: dict[str, Any] = Body(),
    ) -> dict[str, Any]:
        """Re-run post-processing on an existing completed job."""

        job_id = data.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required.")

        obj = await jobs_service.get(UUID(job_id))
        await enforce_action_or_403(
            jobs_service,
            request=request,
            action="edit",
            resource=obj,
            resource_type=NOTE_TAKER_RESOURCE_TYPE,
        )
        if not JobStatus.can_rerun(obj.status):
            raise HTTPException(
                status_code=409, detail=f"Job is not completed (status={obj.status})."
            )

        from tasks.definitions import note_taker_rerun_bg_task

        await note_taker_rerun_bg_task.kiq(
            job_id=job_id,
            settings_id=str(settings_id),
            speaker_mapping=data.get("speaker_mapping", {}),
            extra_keyterms=data.get("extra_keyterms", []),
            meeting_notes=data.get("meeting_notes") or None,
        )

        return {"job_id": job_id, "status": JobStatus.RERUNNING.value}
