import asyncio
import json
import logging
from typing import Any, Optional
from uuid import UUID

import httpx
from litestar import Controller, delete, get, post, put
from litestar.params import Body
from litestar.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func

from core.db.models.teams.note_taker_settings import NoteTakerSettings
from core.db.session import async_session_maker

logger = logging.getLogger(__name__)


NOTE_TAKER_SETTINGS_SYSTEM_NAME = "NOTE_TAKER_SETTINGS"


class PromptSettingSchema(BaseModel):
    enabled: bool = False
    prompt_template: str = ""


class NoteTakerSettingsSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subscription_recordings_ready: bool = False
    # pipeline_id stores the stt_model_system_name (e.g. "ELEVENLABS2_SCRIBE_V1").
    # Empty string means the transcription service will use its own default provider.
    pipeline_id: str = ""
    send_number_of_speakers: bool = False
    accept_commands_from_non_organizer: bool = False
    create_knowledge_graph_embedding: bool = False
    knowledge_graph_system_name: str = ""
    keyterms: str = ""
    integration: dict[str, Any] = Field(
        default_factory=lambda: {
            "confluence": {
                "enabled": False,
                "confluence_api_server": "",
                "confluence_create_page_tool": "",
                "space_key": "",
                "parent_id": "",
                "title_template": "Meeting notes: {meeting_title} ({date})",
            },
            "salesforce": {
                "send_transcript_to_salesforce": False,
                "salesforce_api_server": "",
                "salesforce_stt_recording_tool": "",
            },
        }
    )
    chapters: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    summary: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    insights: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    post_transcription: PromptSettingSchema = Field(default_factory=PromptSettingSchema)


class NoteTakerSettingsRecordCreateSchema(BaseModel):
    name: str
    system_name: str
    description: str = ""
    config: NoteTakerSettingsSchema = Field(default_factory=NoteTakerSettingsSchema)
    provider_system_name: Optional[str] = None
    superuser_id: Optional[str] = None


class NoteTakerSettingsRecordUpdateSchema(BaseModel):
    name: Optional[str] = None
    system_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[NoteTakerSettingsSchema] = None
    provider_system_name: Optional[str] = None
    superuser_id: Optional[str] = None


def _default_settings_payload() -> dict[str, Any]:
    return NoteTakerSettingsSchema().model_dump()


def _settings_to_payload(settings: NoteTakerSettings) -> dict[str, Any]:
    return {
        "id": str(settings.id),
        "name": settings.name,
        "system_name": settings.system_name,
        "description": settings.description,
        "config": settings.config or _default_settings_payload(),
        "provider_system_name": settings.provider_system_name,
        "superuser_id": settings.superuser_id,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }


def _validate_salesforce_settings(data: NoteTakerSettingsSchema) -> None:
    salesforce_settings = (data.integration or {}).get("salesforce") or {}
    if salesforce_settings.get("send_transcript_to_salesforce") and (
        not salesforce_settings.get("salesforce_api_server")
        or not salesforce_settings.get("salesforce_stt_recording_tool")
    ):
        raise ValueError(
            "Salesforce API server and STT recording tool are required when "
            "send_transcript_to_salesforce is enabled."
        )


def _validate_confluence_settings(data: NoteTakerSettingsSchema) -> None:
    confluence_settings = (data.integration or {}).get("confluence") or {}
    if not confluence_settings.get("enabled"):
        return

    if not confluence_settings.get("space_key"):
        raise ValueError(
            "Confluence space_id is required when confluence is enabled (enter numeric spaceId from Confluence REST v2)."
        )

    server = (
        confluence_settings.get("confluence_api_server")
        # or confluence_settings.get("api_server_system_name")
    )
    tool = (
        confluence_settings.get("confluence_create_page_tool")
        # or confluence_settings.get("api_tool_system_name")
        # or confluence_settings.get("tool_system_name")
    )
    if not server or not tool:
        raise ValueError(
            "Confluence API server and create-page tool are required when confluence is enabled."
        )


def _validate_post_transcription_settings(data: NoteTakerSettingsSchema) -> None:
    section = data.post_transcription
    if not section.enabled:
        return
    if not str(section.prompt_template or "").strip():
        raise ValueError(
            "Prompt template is required when post-transcription processing is enabled."
        )


async def _get_settings_by_id_or_system_name(
    session, settings_id: str
) -> NoteTakerSettings | None:
    try:
        parsed_id = UUID(settings_id)
    except (TypeError, ValueError):
        parsed_id = None

    if parsed_id is not None:
        stmt = select(NoteTakerSettings).where(NoteTakerSettings.id == parsed_id)
    else:
        stmt = select(NoteTakerSettings).where(
            NoteTakerSettings.system_name == settings_id
        )
    result = await session.execute(stmt)
    return result.scalars().first()


class NoteTakerSettingsController(Controller):
    path = "/note-taker/settings"
    tags = ["Admin / Note Taker"]

    @get()
    async def list_settings(self) -> list[dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = select(NoteTakerSettings).order_by(
                NoteTakerSettings.created_at.asc()
            )
            result = await session.execute(stmt)
            settings = result.scalars().all()
            return [_settings_to_payload(item) for item in settings]

    @get("/{settings_id:str}")
    async def get_settings(self, settings_id: str) -> dict[str, Any]:
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                return {}
            return _settings_to_payload(settings)

    @post()
    async def create_settings(
        self,
        data: NoteTakerSettingsRecordCreateSchema = Body(),
        request: Any = None,
    ) -> dict[str, Any]:
        _validate_salesforce_settings(data.config)
        _validate_confluence_settings(data.config)
        _validate_post_transcription_settings(data.config)
        async with async_session_maker() as session:
            settings = NoteTakerSettings(
                name=data.name,
                system_name=data.system_name,
                description=data.description,
                config=data.config.model_dump(),
                provider_system_name=data.provider_system_name or None,
                superuser_id=data.superuser_id or None,
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        return _settings_to_payload(settings)

    @put()
    async def update_settings(
        self,
        data: NoteTakerSettingsSchema = Body(),
    ) -> dict[str, Any]:
        _validate_salesforce_settings(data)
        _validate_confluence_settings(data)
        _validate_post_transcription_settings(data)
        async with async_session_maker() as session:
            stmt = select(NoteTakerSettings).where(
                NoteTakerSettings.system_name == NOTE_TAKER_SETTINGS_SYSTEM_NAME
            )
            result = await session.execute(stmt)
            settings = result.scalars().first()

            if settings is None:
                settings = NoteTakerSettings(
                    name="Note Taker Settings",
                    system_name=NOTE_TAKER_SETTINGS_SYSTEM_NAME,
                    description="Settings for the Teams note taker bot.",
                    config=_default_settings_payload(),
                )
                session.add(settings)

            settings.config = data.model_dump()
            await session.commit()
            await session.refresh(settings)
            return _settings_to_payload(settings)

    @put("/{settings_id:str}")
    async def update_settings_by_id(
        self,
        settings_id: str,
        data: NoteTakerSettingsRecordUpdateSchema = Body(),
        request: Any = None,
    ) -> dict[str, Any]:
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                raise ValueError("Note taker settings not found.")

            if data.config is not None:
                _validate_salesforce_settings(data.config)
                _validate_confluence_settings(data.config)
                _validate_post_transcription_settings(data.config)
                settings.config = data.config.model_dump()
            if data.name is not None:
                settings.name = data.name
            if data.system_name is not None:
                settings.system_name = data.system_name
            if data.description is not None:
                settings.description = data.description
            if data.provider_system_name is not None:
                settings.provider_system_name = data.provider_system_name or None
            if data.superuser_id is not None:
                settings.superuser_id = data.superuser_id or None

            await session.commit()
            await session.refresh(settings)

        return _settings_to_payload(settings)

    @delete("/{settings_id:str}", status_code=200)
    async def delete_settings(
        self, settings_id: str, request: Any = None
    ) -> dict[str, Any]:
        """Delete a note taker settings record and unregister its runtime from the registry."""
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                raise HTTPException(
                    status_code=404, detail="Note taker settings not found."
                )
            payload = _settings_to_payload(settings)
            provider_sn = str(settings.provider_system_name or "").strip()
            deleted_id = settings.id

            # Count how many OTHER settings still reference the same provider
            remaining_count = 0
            if provider_sn:
                count_result = await session.execute(
                    select(func.count())
                    .select_from(NoteTakerSettings)
                    .where(
                        NoteTakerSettings.provider_system_name == provider_sn,
                        NoteTakerSettings.id != deleted_id,
                    )
                )
                remaining_count = count_result.scalar_one_or_none() or 0

            await session.delete(settings)
            await session.commit()

        # Unregister from registry if available
        if request is not None:
            from services.agents.teams.note_taker import NoteTakerRegistry

            registry: NoteTakerRegistry | None = getattr(
                getattr(request, "app", None) and request.app.state,
                "note_taker_registry",
                None,
            )
            if registry is not None and provider_sn:
                runtime = registry.get_by_provider_system_name(provider_sn)
                if runtime is not None and remaining_count == 0:
                    # Last settings for this provider — unregister the runtime
                    registry._by_provider_system_name.pop(provider_sn, None)
                    for k, v in list(registry._runtimes.items()):
                        if v is runtime:
                            registry._runtimes.pop(k, None)

        return payload

    @post("/{settings_id:str}/reload", status_code=200)
    async def reload_runtime(
        self, settings_id: str, request: Any = None
    ) -> dict[str, Any]:
        """
        Reload the runtime for a note taker settings record.
        Resolves credentials from the linked Provider record.
        Hot-reloads without restarting the application.
        """
        from core.db.models.provider.provider import Provider as _Provider
        from services.agents.teams.note_taker import (
            NoteTakerRegistry,
            NoteTakerSettings as _NTSettings,
            build_note_taker_runtime,
        )

        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                raise HTTPException(
                    status_code=404, detail="Note taker settings not found."
                )

            # Resolve credentials from Provider
            creds: dict[str, str] = {}
            if settings.provider_system_name:
                stmt = select(_Provider).where(
                    _Provider.system_name == settings.provider_system_name
                )
                provider = (await session.execute(stmt)).scalars().first()
                if provider is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Provider '{settings.provider_system_name}' not found.",
                    )
                secrets = provider.secrets_encrypted or {}
                conn = provider.connection_config or {}
                creds = {
                    "client_id": secrets.get("client_id")
                    or conn.get("client_id")
                    or "",
                    "client_secret": secrets.get("client_secret") or "",
                    "tenant_id": secrets.get("tenant_id")
                    or conn.get("tenant_id")
                    or "",
                    "auth_handler_id": conn.get("auth_handler_id") or "",
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No provider_system_name configured for this record.",
                )

        client_id = str(creds.get("client_id") or "").strip()
        client_secret = str(creds.get("client_secret") or "").strip()
        tenant_id = str(creds.get("tenant_id") or "").strip()
        auth_handler_id = str(
            creds.get("auth_handler_id") or f"note_taker_{settings.system_name}"
        ).strip()

        if not (client_id and client_secret and tenant_id):
            raise HTTPException(
                status_code=400,
                detail="Incomplete credentials (need client_id, client_secret, tenant_id).",
            )

        try:
            settings_obj = _NTSettings(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                auth_handler_id=auth_handler_id,
            )
            runtime = build_note_taker_runtime(settings_obj)
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Failed to build runtime: {exc}"
            ) from exc

        if request is not None:
            registry: NoteTakerRegistry | None = getattr(
                getattr(request, "app", None) and request.app.state,
                "note_taker_registry",
                None,
            )
            if registry is not None:
                await registry.register(
                    client_id,
                    runtime,
                    provider_system_name=settings.provider_system_name or "",
                )

        return {
            "status": "reloaded",
            "system_name": settings.system_name,
            "client_id": client_id,
        }

    @get("/{settings_id:str}/status", status_code=200)
    async def get_runtime_status(
        self, settings_id: str, request: Any = None
    ) -> dict[str, Any]:
        """Check if the runtime for this settings record is loaded in the registry."""
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                raise HTTPException(
                    status_code=404, detail="Note taker settings not found."
                )

        has_credentials = bool(settings.provider_system_name)
        runtime_loaded = False

        if request is not None:
            from services.agents.teams.note_taker import NoteTakerRegistry

            registry: NoteTakerRegistry | None = getattr(
                getattr(request, "app", None) and request.app.state,
                "note_taker_registry",
                None,
            )
            if registry is not None:
                runtime_loaded = (
                    registry.get_by_provider_system_name(
                        settings.provider_system_name or ""
                    )
                    is not None
                )

        return {
            "system_name": settings.system_name,
            "has_credentials": has_credentials,
            "runtime_loaded": runtime_loaded,
        }


# ---------------------------------------------------------------------------
# Preview job status update helper (used by background runners)
# ---------------------------------------------------------------------------


async def _update_preview_job_status(
    job_id: str, *, status: str, result: dict[str, Any] | None = None
) -> None:
    """Update a preview job's status and result via the domain service."""
    from core.db.models.teams.note_taker_job import NoteTakerJob
    from uuid import UUID

    async with async_session_maker() as session:
        stmt = select(NoteTakerJob).where(NoteTakerJob.id == UUID(job_id))
        row = (await session.execute(stmt)).scalars().first()
        if row is None:
            return
        row.status = status
        if result is not None:
            row.result = result
        await session.commit()


# ---------------------------------------------------------------------------
# Background job runners (no TurnContext dependency)
# ---------------------------------------------------------------------------


async def _run_preview_job_background(
    *,
    job_id: str,
    settings_id: str,
    source_url: str | None,
    file_bytes: bytes | None = None,
    upload_filename: str | None = None,
    upload_content_type: str | None = None,
    participants: list[str],
    stt_model_system_name: str | None,
) -> None:
    """Drive the transcription pipeline for a preview job, updating DB status.

    Either ``source_url`` (remote file to download) or ``file_bytes`` (already
    in-memory from a multipart upload) must be provided.
    """
    from speech_to_text.transcription import service as transcription_service
    from .note_taker_files import _probe_remote_file_metadata, _upload_stream_to_object

    await _update_preview_job_status(job_id, status="running")

    try:
        if not source_url and not file_bytes:
            await _update_preview_job_status(
                job_id, status="failed", result={"error": "No source provided."}
            )
            return

        name = f"preview_{job_id}"
        object_key: str

        if file_bytes is not None:
            # --- Multipart upload path ---
            raw_ct = (
                (upload_content_type or "application/octet-stream")
                .split(";")[0]
                .strip()
            )
            if not raw_ct.startswith(("audio/", "video/")):
                # Try to guess from filename extension
                from pathlib import Path as _Path

                suffix = _Path(upload_filename or "").suffix.lower()
                _EXT_MAP = {
                    ".mp3": "audio/mpeg",
                    ".mp4": "video/mp4",
                    ".m4a": "audio/mp4",
                    ".wav": "audio/wav",
                    ".ogg": "audio/ogg",
                    ".webm": "video/webm",
                    ".mkv": "video/x-matroska",
                    ".flac": "audio/flac",
                }
                raw_ct = _EXT_MAP.get(suffix, raw_ct)
                if not raw_ct.startswith(("audio/", "video/")):
                    await _update_preview_job_status(
                        job_id,
                        status="failed",
                        result={"error": f"Unsupported content type: {raw_ct}"},
                    )
                    return

            content_type = raw_ct
            suffix_from_ct = (
                "." + content_type.split("/")[-1] if "/" in content_type else ".bin"
            )
            filename = upload_filename or f"{name}{suffix_from_ct}"
            ext = (
                "." + filename.rsplit(".", 1)[-1] if "." in filename else suffix_from_ct
            )

            async def _bytes_iter(data: bytes, chunk: int = 65536):
                for i in range(0, len(data), chunk):
                    yield data[i : i + chunk]

            object_key = await _upload_stream_to_object(
                stream=_bytes_iter(file_bytes),
                size=len(file_bytes),
                content_type=content_type,
                filename=filename,
            )
        else:
            # --- URL download path ---
            timeout = httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0)
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                (
                    probed_size,
                    content_type,
                    _disposition,
                    _final_url,
                ) = await _probe_remote_file_metadata(client, source_url)

            content_type = (
                (content_type or "application/octet-stream").split(";")[0].strip()
            )
            if not content_type.startswith(("audio/", "video/")):
                await _update_preview_job_status(
                    job_id,
                    status="failed",
                    result={"error": f"Unsupported content type: {content_type}"},
                )
                return

            ext = "." + content_type.split("/")[-1] if "/" in content_type else ".bin"

            timeout = httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0)
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                async with client.stream("GET", source_url) as response:
                    response.raise_for_status()
                    size = (
                        int(response.headers.get("Content-Length") or 0) or probed_size
                    )
                    object_key = await _upload_stream_to_object(
                        stream=response.aiter_bytes(),
                        size=size,
                        content_type=content_type,
                        filename=f"{name}{ext}",
                    )

        # Resolve STT model: explicit param > note taker settings > default
        effective_stt_model = stt_model_system_name or None
        if not effective_stt_model:
            try:
                async with async_session_maker() as session:
                    nt_settings = await _get_settings_by_id_or_system_name(
                        session, settings_id
                    )
                    if nt_settings is not None:
                        cfg = nt_settings.config or {}
                        effective_stt_model = (
                            str(cfg.get("pipeline_id") or "").strip() or None
                        )
            except Exception as cfg_err:
                logger.warning(
                    "Preview job %s: failed to load settings for pipeline_id: %s",
                    job_id,
                    cfg_err,
                )

        # Ensure STT storage pool is initialized before submitting.
        try:
            from stores import get_db_store

            db_store = get_db_store()
            await db_store.client._ensure_pool_initialized()
        except Exception as pool_err:
            logger.warning("Preview job %s: pool init warning: %s", job_id, pool_err)

        transcription_job_id = await transcription_service.submit(
            name=name,
            ext=ext.lstrip("."),
            bytes_=None,
            object_key=object_key,
            content_type=content_type,
            stt_model_system_name=effective_stt_model,
            keyterms=participants or None,
        )

        async def _poll_transcription() -> str:
            delay = 5
            iterations = 0
            while True:
                st = await transcription_service.get_status(transcription_job_id)
                if st in {"completed", "transcribed", "diarized", "failed"}:
                    return st or "unknown"
                iterations += 1
                if iterations == 30:
                    logger.warning(
                        "Preview job %s: transcription still pending after %d polls",
                        job_id,
                        iterations,
                    )
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, 30)

        try:
            status: str = await asyncio.wait_for(_poll_transcription(), timeout=900)
        except asyncio.TimeoutError:
            status = "timeout"

        if status not in {"completed", "transcribed", "diarized"}:
            await _update_preview_job_status(
                job_id,
                status="failed",
                result={
                    "error": f"Transcription status: {status}",
                    "transcription_job_id": transcription_job_id,
                },
            )
            return

        transcription = await transcription_service.get_transcription(
            transcription_job_id
        )

        # Extract speaker labels and build display text.
        from .note_taker_utils import format_transcript_segments

        full_text, speaker_labels = format_transcript_segments(transcription)

        # Run post-transcription AI prompt to get speaker name suggestions.
        ai_speaker_mapping: dict[str, str] = {}
        ai_suggested_keyterms: list[str] = []
        try:
            async with async_session_maker() as session:
                nt_settings = await _get_settings_by_id_or_system_name(
                    session, settings_id
                )
            raw_config = (nt_settings.config if nt_settings else None) or {}
            if isinstance(raw_config, str):
                raw_config = json.loads(raw_config)
            from .note_taker_utils import _merge_note_taker_settings

            merged_settings = _merge_note_taker_settings(
                raw_config if isinstance(raw_config, dict) else None
            )
            post_cfg = merged_settings.get("post_transcription")
            if isinstance(post_cfg, dict) and post_cfg.get("enabled"):
                template_name = str(post_cfg.get("prompt_template") or "").strip()
                if template_name:
                    from services.prompt_templates import execute_prompt_template
                    from .transcript_postprocess import (
                        parse_speaker_mapping_output,
                        parse_suggested_keyterms_from_output,
                    )

                    result_ai = await execute_prompt_template(
                        system_name_or_config=template_name,
                        template_values={
                            "transcription": full_text,
                            "participants": participants,
                            "language": "the same as the transcription",
                            "conversation_date": "",
                        },
                    )
                    content_ai = getattr(result_ai, "content", None)
                    if content_ai is None:
                        content_ai = str(result_ai)
                    processed = str(content_ai or "").strip()
                    if processed:
                        ai_speaker_mapping = parse_speaker_mapping_output(processed)
                        ai_suggested_keyterms = parse_suggested_keyterms_from_output(
                            processed
                        )
                        # Filter to only known speaker labels.
                        ai_speaker_mapping = {
                            k: v
                            for k, v in ai_speaker_mapping.items()
                            if k in speaker_labels or k.startswith("speaker")
                        }
                    logger.info(
                        "Preview job %s: post-transcription AI mapping=%r, keyterms=%r",
                        job_id,
                        ai_speaker_mapping,
                        ai_suggested_keyterms,
                    )
        except Exception as pt_err:
            logger.warning(
                "Preview job %s: post-transcription prompt failed: %s",
                job_id,
                pt_err,
            )

        # Build speaker_mapping: raw labels with AI suggestions pre-filled.
        speaker_mapping_result = {
            sp: ai_speaker_mapping.get(sp, "") for sp in speaker_labels
        }

        await _update_preview_job_status(
            job_id,
            status="transcribed",
            result={
                "transcription_job_id": transcription_job_id,
                "transcription": transcription,
                "participants": participants,
                "speaker_labels": speaker_labels,
                "speaker_mapping": speaker_mapping_result,
                "suggested_keyterms": ai_suggested_keyterms,
                "full_text": full_text,
            },
        )

    except Exception as exc:
        logger.exception("Preview job %s failed: %s", job_id, exc)
        await _update_preview_job_status(
            job_id, status="failed", result={"error": str(exc)}
        )


async def _rerun_postprocessing_background(
    *,
    job_id: str,
    settings_id: str,
    speaker_mapping: dict[str, str],
    extra_keyterms: list[str],
    meeting_notes: str | None = None,
) -> None:
    """Re-run post-processing (summaries, chapters, insights) on a completed job."""
    from speech_to_text.transcription import service as transcription_service
    from services.prompt_templates import execute_prompt_template
    from .note_taker_utils import _merge_note_taker_settings, format_transcript_segments
    from .transcript_postprocess import annotate_transcript_speakers

    await _update_preview_job_status(job_id, status="rerunning")

    try:
        from core.db.models.teams.note_taker_job import NoteTakerJob
        from uuid import UUID as _UUID

        async with async_session_maker() as session:
            stmt = select(NoteTakerJob).where(NoteTakerJob.id == _UUID(job_id))
            job_row = (await session.execute(stmt)).scalars().first()
        if not job_row:
            return

        result = job_row.result or {}
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                result = {}

        transcription_job_id = result.get("transcription_job_id")
        if not transcription_job_id:
            await _update_preview_job_status(
                job_id,
                status="failed",
                result={"error": "No transcription_job_id in job result."},
            )
            return

        transcription = await transcription_service.get_transcription(
            transcription_job_id
        )
        if not transcription:
            await _update_preview_job_status(
                job_id, status="failed", result={"error": "Transcription not found."}
            )
            return

        full_text, _ = format_transcript_segments(transcription)

        if speaker_mapping:
            full_text = annotate_transcript_speakers(full_text, speaker_mapping)

        async with async_session_maker() as session:
            settings_rec = await _get_settings_by_id_or_system_name(
                session, settings_id
            )
        raw_config = (settings_rec.config if settings_rec else None) or {}
        if isinstance(raw_config, str):
            try:
                raw_config = json.loads(raw_config)
            except Exception:
                raw_config = {}
        settings = _merge_note_taker_settings(
            raw_config if isinstance(raw_config, dict) else None
        )

        participants = result.get("participants") or []
        # Merge settings keyterms with extra keyterms from the re-run request.
        all_keyterms: list[str] = list(extra_keyterms or [])
        settings_keyterms_raw = str(settings.get("keyterms") or "").strip()
        if settings_keyterms_raw:
            from .note_taker_utils import parse_keyterms_list, merge_unique_strings

            all_keyterms = merge_unique_strings(
                parse_keyterms_list(settings_keyterms_raw), all_keyterms
            )

        postprocessing_results: dict[str, str] = {}

        for key, title in (
            ("summary", "Summary"),
            ("chapters", "Chapters"),
            ("insights", "Insights"),
        ):
            section = settings.get(key)
            if not isinstance(section, dict) or not section.get("enabled"):
                continue
            template_name = str(section.get("prompt_template") or "").strip()
            if not template_name:
                continue
            try:
                res = await execute_prompt_template(
                    system_name_or_config=template_name,
                    template_values={
                        "transcription": full_text,
                        "participants": participants,
                        "keyterms": ", ".join(all_keyterms) if all_keyterms else "",
                        "meeting_notes": meeting_notes or "",
                        "language": "the same as the transcription",
                        "conversation_date": "",
                    },
                )
                content = getattr(res, "content", None)
                if content is None:
                    content = str(res)
                postprocessing_results[key] = str(content)
            except Exception as exc:
                logger.warning(
                    "Postprocessing template %s failed: %s", template_name, exc
                )
                postprocessing_results[key] = f"[Error: {exc}]"

        await _update_preview_job_status(
            job_id,
            status="completed",
            result={
                **result,
                "speaker_mapping": speaker_mapping,
                "full_text": full_text,
                "postprocessing": postprocessing_results,
            },
        )

    except Exception as exc:
        logger.exception("Rerun postprocessing for job %s failed: %s", job_id, exc)
        await _update_preview_job_status(
            job_id, status="failed", result={"error": str(exc)}
        )
