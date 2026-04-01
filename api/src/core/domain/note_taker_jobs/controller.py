from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, Request, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body

from core.domain.note_taker_jobs.service import NoteTakerJobsService

from .schemas import NoteTakerJobCreate, NoteTakerJobSchema

if TYPE_CHECKING:
    pass


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

    @get("/{settings_id:uuid}")
    async def list_jobs(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
    ) -> list[NoteTakerJobSchema]:
        """List preview jobs for a settings record."""
        results, _ = await jobs_service.list_and_count(
            NoteTakerJobsService.Repo.model_type.settings_id == settings_id,
        )
        return [
            jobs_service.to_schema(r, schema_type=NoteTakerJobSchema) for r in results
        ]

    @get("/{settings_id:uuid}/{job_id:uuid}")
    async def get_job(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        job_id: UUID,
    ) -> NoteTakerJobSchema:
        """Get a single preview job."""
        obj = await jobs_service.get(job_id)
        return jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

    @post("/{settings_id:uuid}/run")
    async def run_preview(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
        data: NoteTakerJobCreate = Body(),
    ) -> NoteTakerJobSchema:
        """Submit a new preview transcription job."""
        from services.agents.teams.note_taker_settings import (
            _run_preview_job_background,
        )

        data.settings_id = settings_id
        data.user_id = str(request.scope.get("user_id") or "") or None

        obj = await jobs_service.create(data)
        job = jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

        from core.server.background_tasks import spawn_background_task

        spawn_background_task(
            _run_preview_job_background(
                job_id=str(job.id),
                settings_id=str(settings_id),
                source_url=data.source_url,
                participants=data.participants or [],
                stt_model_system_name=data.stt_model_system_name,
            ),
            name=f"note-taker-preview-{job.id}",
        )

        return job

    @post("/{settings_id:uuid}/run-upload")
    async def run_preview_upload(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        request: Request,
        data: Annotated[
            dict[str, Any], Body(media_type=RequestEncodingType.MULTI_PART)
        ],
    ) -> NoteTakerJobSchema:
        """Submit a new preview transcription job with a file upload."""
        from services.agents.teams.note_taker_settings import (
            _run_preview_job_background,
        )

        file: UploadFile | None = data.get("file")  # type: ignore[assignment]
        file_bytes: bytes | None = None
        upload_filename: str | None = None
        upload_content_type: str | None = None
        if file is not None:
            file_bytes = await file.read()
            upload_filename = file.filename
            upload_content_type = file.content_type

        participants_raw = data.get("participants") or ""
        if isinstance(participants_raw, str):
            participants = [p.strip() for p in participants_raw.split(",") if p.strip()]
        elif isinstance(participants_raw, list):
            participants = [str(p) for p in participants_raw if p]
        else:
            participants = []

        stt_model_system_name = str(data.get("stt_model_system_name") or "") or None

        from .schemas import NoteTakerJobCreate

        create_data = NoteTakerJobCreate(
            settings_id=settings_id,
            user_id=str(request.scope.get("user_id") or "") or None,
            participants=participants,
        )
        obj = await jobs_service.create(create_data)
        job = jobs_service.to_schema(obj, schema_type=NoteTakerJobSchema)

        asyncio.create_task(
            _run_preview_job_background(
                job_id=str(job.id),
                settings_id=str(settings_id),
                source_url=None,
                file_bytes=file_bytes,
                upload_filename=upload_filename,
                upload_content_type=upload_content_type,
                participants=participants,
                stt_model_system_name=stt_model_system_name,
            )
        )

        return job

    @post("/{settings_id:uuid}/rerun")
    async def rerun_postprocessing(
        self,
        jobs_service: NoteTakerJobsService,
        settings_id: UUID,
        data: dict[str, Any] = Body(),
    ) -> dict[str, Any]:
        """Re-run post-processing on an existing completed job."""
        from services.agents.teams.note_taker_settings import (
            _rerun_postprocessing_background,
        )

        job_id = data.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required.")

        obj = await jobs_service.get(UUID(job_id))
        if obj.status not in {"completed", "failed", "transcribed"}:
            raise HTTPException(
                status_code=409, detail=f"Job is not completed (status={obj.status})."
            )

        from core.server.background_tasks import spawn_background_task

        spawn_background_task(
            _rerun_postprocessing_background(
                job_id=job_id,
                settings_id=str(settings_id),
                speaker_mapping=data.get("speaker_mapping", {}),
                extra_keyterms=data.get("extra_keyterms", []),
                meeting_notes=data.get("meeting_notes") or None,
            ),
            name=f"note-taker-rerun-{job_id}",
        )

        return {"job_id": job_id, "status": "rerunning"}
