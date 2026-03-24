import asyncio
import datetime as dt
import re
from types import SimpleNamespace
from uuid import UUID, uuid4
from logging import getLogger
from typing import Any, Awaitable, Callable

import httpx
from microsoft_agents.hosting.core import TurnContext

from core.db.models.knowledge_graph import KnowledgeGraph
from core.db.session import async_session_maker
from sqlalchemy import select
from services.knowledge_graph.sources.api_ingest.api_ingest_source import (
    ApiIngestDataSource,
    run_background_ingest,
)
from services.observability import observe
from stores import get_db_client
from speech_to_text.transcription import service as transcription_service
from services.prompt_templates import execute_prompt_template
from routes.admin.recordings import DEFAULT_PIPELINE

from .note_taker_files import _probe_remote_file_metadata, _upload_stream_to_object
from .note_taker_utils import (
    _build_note_taker_filename,
    _format_duration,
    _format_mm_ss,
    _format_recording_date_compact,
    _format_recording_date_iso,
    merge_unique_strings,
    _parse_content_length,
    parse_keyterms_list,
    _get_meeting_id_part,
    _get_meeting_title_part,
)
from .note_taker_confluence import maybe_publish_confluence_notes
from .note_taker_people import (
    get_invited_people,
    invited_people_to_first_names,
    invited_people_to_names,
)
from .transcript_postprocess import (
    annotate_transcript_speakers,
    parse_speaker_mapping_output,
)

logger = getLogger(__name__)

_TRANSCRIPTION_TIMEOUT_SECONDS = 900
_TRANSCRIPTION_POLL_SECONDS = 5


def _build_transcription_keyterms(
    *,
    settings: dict[str, Any] | None,
    invited_people: list[dict[str, Any]] | None,
) -> list[str]:
    base_keyterms = parse_keyterms_list(settings.get("keyterms")) if settings else []
    participant_keyterms = invited_people_to_first_names(invited_people)
    return merge_unique_strings(base_keyterms, participant_keyterms)


def _format_prompt_template_error(err: Exception, *, limit: int = 300) -> str:
    raw = getattr(err, "message", None)
    if raw is None:
        raw = str(err) or err.__class__.__name__

    text = re.sub(r"\s+", " ", str(raw)).strip()
    if not text:
        text = err.__class__.__name__
    if limit > 0 and len(text) > limit:
        text = text[: max(0, limit - 3)] + "..."
    return text


async def _ensure_vector_pool_ready() -> None:
    """Block until the pgvector pool is ready (to fix the issue with the first call after the startup)."""
    try:
        client = get_db_client()
        init = getattr(client, "init_pool", None)
        if callable(init):
            await init()
    except Exception as exc:
        logger.warning("Failed to pre-initialize vector DB pool: %s", exc)


async def _start_transcription_from_object_key(
    *,
    name: str,
    ext: str,
    object_key: str,
    content_type: str,
    pipeline_id: str,
    keyterms: list[str] | None = None,
    number_of_participants: str | None = None,
    on_submit: Callable[[str], Awaitable[None]] | None = None,
) -> tuple[str, dict | None]:
    await _ensure_vector_pool_ready()

    ext_no_dot = ext.lstrip(".")

    job_id = await transcription_service.submit(
        name=name,
        ext=ext_no_dot,
        bytes_=None,
        object_key=object_key,
        content_type=content_type,
        backend=pipeline_id,
        keyterms=keyterms,
        number_of_participants=number_of_participants,
    )
    if on_submit and job_id:
        try:
            await on_submit(job_id)
        except Exception:
            logger.exception(
                "on_submit callback failed for transcription job %s", job_id
            )

    deadline = asyncio.get_event_loop().time() + _TRANSCRIPTION_TIMEOUT_SECONDS
    status: str | None = None
    while True:
        status = await transcription_service.get_status(job_id)
        if status in {"completed", "transcribed", "diarized", "failed"}:
            break
        if asyncio.get_event_loop().time() > deadline:
            status = status or "timeout"
            break
        await asyncio.sleep(_TRANSCRIPTION_POLL_SECONDS)

    transcription = None
    if status in {"completed", "transcribed", "diarized"}:
        transcription = await transcription_service.get_transcription(job_id)

    return status or "unknown", {"id": job_id, "transcription": transcription}


@observe(
    name="Ingest into knowledge graph",
    channel="production",
    source="Runtime API",
)
async def _ingest_knowledge_graph_sections(
    *,
    graph_system_name: str,
    meeting: dict[str, Any] | None,
    job_id: str | None,
    conversation_date: str | None,
    sections: dict[str, str],
) -> int:
    if not graph_system_name or not sections:
        return 0

    date_part = _format_recording_date_compact(conversation_date) or dt.datetime.now(
        dt.timezone.utc
    ).strftime("%Y%m%d")
    meeting_part = (
        _get_meeting_title_part(meeting) or _get_meeting_id_part(meeting) or "meeting"
    )
    item_id = job_id or "transcription"

    async with async_session_maker() as session:
        stmt = select(KnowledgeGraph).where(
            KnowledgeGraph.system_name == graph_system_name
        )
        graph = (await session.execute(stmt)).scalars().first()
        if not graph:
            logger.warning(
                "Knowledge graph %s not found for note taker embedding.",
                graph_system_name,
            )
            return 0

        data_source = ApiIngestDataSource(source_name="Note Taker")
        source = await data_source.get_or_create_source(session, graph.id)

        items = []
        for kind, content in sections.items():
            if not content:
                continue
            filename = _build_note_taker_filename(
                kind=kind,
                meeting_id=meeting_part,
                item_id=item_id,
                date_part=date_part,
                ext=".txt",
            )
            items.append(
                SimpleNamespace(
                    kind="text",
                    filename=filename,
                    text=content,
                    file_bytes=None,
                )
            )

        if not items:
            return 0

        ingestion_id = str(uuid4())
        asyncio.create_task(
            run_background_ingest(
                ingestion_id=ingestion_id,
                graph_id=graph.id,
                source_id=UUID(str(source.id)),
                items=items,
            )
        )
        return len(items)


@observe(
    name="Execute the prompt tempates",
    channel="production",
    source="Runtime API",
)
async def _execute_transcription_prompt_templates(
    template_system_names: list[str],
    *,
    transcription: str,
    participants: list[str],
    conversation_date: str | None,
) -> list[Any]:
    async def _run_template(system_name: str):
        return await execute_prompt_template(
            system_name_or_config=system_name,
            template_values={
                "transcription": transcription,
                "participants": participants,
                "language": "the same as the transcription",
                "conversation_date": conversation_date or "",
            },
        )

    return await asyncio.gather(
        *(_run_template(system_name) for system_name in template_system_names),
        return_exceptions=True,
    )


@observe(
    name="Post-process transcription",
    channel="production",
    source="Runtime API",
)
async def _post_process_transcription(
    *,
    template_system_name: str,
    transcription: str,
    participants: list[str],
    conversation_date: str | None,
) -> Any:
    return await execute_prompt_template(
        system_name_or_config=template_system_name,
        template_values={
            "transcription": transcription,
            "participants": participants,
            "language": "the same as the transcription",
            "conversation_date": conversation_date or "",
        },
    )


async def _send_transcription_summary(
    context: TurnContext,
    *,
    status: str,
    job_id: str | None,
    transcription: dict | None,
    pipeline_id: str | None,
    conversation_date: str | None,
    conversation_time: str | None,
    settings_system_name: str | None,
    meeting_context: dict[str, Any] | None,
    settings: dict[str, Any] | None = None,
    keyterms: list[str] | None = None,
    invited_people: list[dict[str, str]] | None = None,
    send_expandable_section: Callable[..., Awaitable[None]],
    load_settings_by_system_name: Callable[[str], Awaitable[dict[str, Any]]],
    load_settings_for_context: Callable[[TurnContext], Awaitable[dict[str, Any]]],
    resolve_meeting_details: Callable[[TurnContext], dict[str, Any]],
) -> None:
    duration = None
    transcript_payload = transcription
    participants = None
    if isinstance(transcription, dict):
        duration = transcription.get("duration")
        participants = transcription.get("participants")
        nested = transcription.get("transcription")
        if isinstance(nested, dict):
            transcript_payload = nested
        job_id = job_id or transcription.get("job_id") or transcription.get("id")

    duration_str = _format_duration(duration) if duration is not None else None
    if duration_str == "Unknown":
        duration_str = None

    if status in {"completed", "transcribed", "diarized"}:
        segs_count = 0
        full_text = None
        seen_participants: set[str] = set()
        if isinstance(transcript_payload, dict):
            segs = transcript_payload.get("segments") or []
            segs_count = len(segs)
            full_text = transcript_payload.get("text") or ""
            if segs:
                lines = []
                for s in segs:
                    if not isinstance(s, dict):
                        continue
                    speaker = s.get("speaker") or "speaker_0"
                    if speaker not in seen_participants:
                        seen_participants.add(speaker)
                    text = (s.get("text") or "").strip()
                    if not text:
                        continue
                    ts = _format_mm_ss(s.get("start"))
                    lines.append(f"[{ts}] {speaker}: {text}")
                if lines:
                    full_text = "\n".join(lines)
                elif not full_text:
                    full_text = " ".join(
                        (s.get("text") or "").strip()
                        for s in segs
                        if isinstance(s, dict)
                    ).strip()

        duration_part = f", duration={duration_str}" if duration_str else ""
        speakers_count: int | None = None
        if isinstance(participants, list) and participants:
            keys: set[str] = set()
            for p in participants:
                if not isinstance(p, dict):
                    continue
                key = p.get("key") or p.get("name")
                if not key:
                    continue
                keys.add(str(key))
            if keys:
                speakers_count = len(keys)
        if speakers_count is None and seen_participants:
            speakers_count = len(seen_participants)
        speakers_part = f", speakers={speakers_count}" if speakers_count else ""
        await context.send_activity(
            f"Transcription completed (job={job_id or 'n/a'}, segments={segs_count}{speakers_part}{duration_part})."
        )

        if not full_text and segs_count == 0:
            await context.send_activity("No speech was detected in this recording.")

        if not full_text:
            return

        if settings is None:
            try:
                settings = (
                    await load_settings_by_system_name(settings_system_name)
                    if settings_system_name
                    else await load_settings_for_context(context)
                )
            except Exception as err:
                logger.warning(
                    "Skipping summaries/embedding: cannot load note taker settings: %s",
                    getattr(err, "message", str(err)),
                )
                settings = None

        if invited_people is None:
            try:
                invited_people = await get_invited_people(context)
            except Exception as err:
                logger.debug(
                    "Failed to load invited people: %s",
                    getattr(err, "message", str(err)),
                )
                invited_people = []

        participant_names = invited_people_to_names(invited_people)

        post_cfg = (
            settings.get("post_transcription") if isinstance(settings, dict) else None
        )
        if isinstance(post_cfg, dict) and post_cfg.get("enabled"):
            template_system_name = str(post_cfg.get("prompt_template") or "").strip()
            if template_system_name:
                try:
                    result = await _post_process_transcription(
                        template_system_name=template_system_name,
                        transcription=full_text,
                        participants=participant_names,
                        conversation_date=conversation_date,
                    )
                    content = getattr(result, "content", None)
                    if content is None:
                        content = str(result)
                    processed = str(content or "").strip()
                    if processed:
                        speaker_mapping = parse_speaker_mapping_output(processed)
                        if speaker_mapping:
                            full_text = annotate_transcript_speakers(
                                full_text, speaker_mapping
                            )
                            max_chars = 4000
                            snippet = processed[:max_chars]
                            suffix = "..." if len(processed) > len(snippet) else ""
                            await send_expandable_section(
                                context,
                                title="Post-transcription output",
                                content=f"{snippet}{suffix}",
                                preserve_newlines=True,
                            )
                        else:
                            await context.send_activity(
                                "Post-transcription output ignored (expected speaker_mapping JSON)."
                            )
                except Exception as err:
                    err_msg = _format_prompt_template_error(err)
                    logger.warning(
                        "Post-transcription template %s failed for job %s: %s",
                        template_system_name,
                        job_id,
                        err_msg,
                    )
                    await context.send_activity(
                        f"Post-transcription processing failed: {err_msg}"
                    )

        max_chars = 4000
        snippet = full_text[:max_chars]
        suffix = "..." if len(full_text) > len(snippet) else ""
        await send_expandable_section(
            context,
            title="Transcript",
            content=f"{snippet}{suffix}",
            preserve_newlines=True,
        )

        if not isinstance(settings, dict):
            return

        if keyterms is None:
            # Normally `keyterms` are computed upstream and passed into this function
            # (stream pipeline, and job pipeline when settings were preloaded). Keep
            # this as a defensive fallback for job-mode cases where settings couldn't
            # be loaded upstream, or for any future call sites that don't provide it.
            keyterms = _build_transcription_keyterms(
                settings=settings,
                invited_people=invited_people,
            )

        # keyterms_display = keyterms_to_display(keyterms) or None

        templates: list[tuple[str, str, str]] = []
        for key, title in (
            ("summary", "Summary"),
            ("chapters", "Chapters"),
            ("insights", "Insights"),
        ):
            section = settings.get(key)
            if not isinstance(section, dict):
                continue
            if not section.get("enabled"):
                continue
            template_name = str(section.get("prompt_template") or "").strip()
            if template_name:
                templates.append((template_name, title, key))

        if not templates:
            return

        results = await _execute_transcription_prompt_templates(
            [system_name for system_name, _, _ in templates],
            transcription=full_text,
            participants=participant_names,
            conversation_date=conversation_date,
        )

        knowledge_graph_sections: dict[str, str] = {}
        for (system_name, title, key), result in zip(templates, results):
            if isinstance(result, Exception):
                err_msg = _format_prompt_template_error(result)
                logger.warning(
                    "Prompt template %s failed for transcription job %s: %s",
                    system_name,
                    job_id,
                    err_msg,
                )
                await context.send_activity(f"{title} generation failed: {err_msg}")
                continue

            content = getattr(result, "content", None)
            if content is None:
                content = str(result)
            knowledge_graph_sections[key] = str(content)
            await send_expandable_section(
                context,
                title=f"Meeting {title.lower()}",
                content=str(content),
            )

        confluence_sections = {
            key: knowledge_graph_sections[key]
            for key in ("summary", "chapters")
            if key in knowledge_graph_sections
        }
        if confluence_sections:
            await maybe_publish_confluence_notes(
                context,
                settings=settings,
                job_id=job_id,
                pipeline_id=pipeline_id,
                meeting_context=meeting_context or resolve_meeting_details(context),
                participants=participant_names,
                conversation_date=conversation_date,
                conversation_time=conversation_time,
                duration=duration_str,
                sections=confluence_sections,
                transcript=full_text,
                keyterms=keyterms,
                invited_people=invited_people,
                send_expandable_section=send_expandable_section,
            )

            knowledge_graph_name = str(
                settings.get("knowledge_graph_system_name") or ""
            ).strip()
            embedding_enabled = bool(settings.get("create_knowledge_graph_embedding"))

            logger.info(
                "[teams note-taker] embedding enabled=%s graph=%s",
                embedding_enabled,
                knowledge_graph_name or None,
            )
            if embedding_enabled and knowledge_graph_name and knowledge_graph_sections:
                meeting_for_ingest = meeting_context or resolve_meeting_details(context)
                ingested = await _ingest_knowledge_graph_sections(
                    graph_system_name=knowledge_graph_name,
                    meeting=meeting_for_ingest,
                    job_id=job_id,
                    conversation_date=conversation_date,
                    sections=knowledge_graph_sections,
                )
                if ingested:
                    await context.send_activity(
                        f"Embedded {ingested} item(s) into knowledge graph {knowledge_graph_name}."
                    )

        return

    if status == "failed":
        err_msg = None
        if job_id:
            try:
                err_msg = await transcription_service.get_error(job_id)
            except Exception:
                err_msg = None
        duration_note = f" (duration={duration_str})" if duration_str else ""
        await context.send_activity(
            f"Transcription failed for job {job_id or 'n/a'}{duration_note}: {err_msg or 'unknown error'}"
        )
        return

    duration_note = f", duration={duration_str}" if duration_str else ""
    await context.send_activity(
        f"Transcription incomplete (status={status}, job={job_id or 'n/a'}{duration_note})."
    )


async def run_transcription_pipeline(
    context: TurnContext,
    *,
    kind: str,
    send_typing: Callable[[TurnContext], Awaitable[None]],
    send_expandable_section: Callable[..., Awaitable[None]],
    load_settings_by_system_name: Callable[[str], Awaitable[dict[str, Any]]],
    load_settings_for_context: Callable[[TurnContext], Awaitable[dict[str, Any]]],
    resolve_meeting_details: Callable[[TurnContext], dict[str, Any]],
    # stream mode:
    download_url: str | None = None,
    headers: dict[str, str] | None = None,
    name_resolver: Callable[[str, str | None, str], tuple[str, str]] | None = None,
    known_size: int | None = None,
    on_submit: Callable[[str], Awaitable[None]] | None = None,
    on_submit_factory: Callable[
        [str, str, str], Awaitable[Callable[[str], Awaitable[None]] | None]
    ]
    | None = None,
    pipeline_id: str = DEFAULT_PIPELINE,
    # job mode:
    job_id: str | None = None,
    build_on_submit_callback: Callable[
        ..., Awaitable[Callable[[str], Awaitable[None]] | None]
    ]
    | None = None,
    # shared:
    conversation_date: str | None = None,
    conversation_time: str | None = None,
    settings_system_name: str | None = None,
    meeting_context: dict[str, Any] | None = None,
) -> None:
    if kind == "stream":
        assert download_url and headers is not None and name_resolver is not None
        await send_typing(context)
        settings: dict[str, Any] | None = None
        invited_people: list[dict[str, str]] = []
        try:
            loaded = (
                await load_settings_by_system_name(settings_system_name)
                if settings_system_name
                else await load_settings_for_context(context)
            )
            if isinstance(loaded, dict):
                settings = loaded
        except Exception as err:
            logger.debug(
                "Failed to load keyterms for transcription: %s",
                getattr(err, "message", str(err)),
            )

        selected_pipeline_id = (settings or {}).get("pipeline_id")
        if isinstance(selected_pipeline_id, str) and selected_pipeline_id.strip():
            pipeline_id = selected_pipeline_id.strip()

        try:
            invited_people = await get_invited_people(context)
        except Exception as err:
            logger.debug(
                "Failed to load invited people for keyterms: %s",
                getattr(err, "message", str(err)),
            )
        keyterms = _build_transcription_keyterms(
            settings=settings,
            invited_people=invited_people,
        )
        number_of_participants: str | None = None
        if (settings or {}).get("send_number_of_speakers"):
            try:
                count = len(invited_people or [])
            except Exception:
                count = 0
            if count >= 2:
                number_of_participants = str(count)
        timeout = httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            (
                probed_size,
                probed_type,
                probed_disposition,
                probed_final_url,
            ) = await _probe_remote_file_metadata(client, download_url, headers=headers)
            async with client.stream("GET", download_url, headers=headers) as response:
                response.raise_for_status()
                content_type = (
                    (response.headers.get("Content-Type") or "application/octet-stream")
                    .split(";")[0]
                    .strip()
                )
                if not content_type or content_type == "application/octet-stream":
                    probed_ct = (probed_type or "").split(";")[0].strip()
                    if probed_ct:
                        content_type = probed_ct

                content_length = _parse_content_length(
                    response.headers.get("Content-Length")
                )
                if content_length is None:
                    content_length = known_size or probed_size

                final_url = str(response.url) if response.url else download_url
                if not final_url and probed_final_url:
                    final_url = probed_final_url
                content_disposition = response.headers.get("Content-Disposition")
                if not content_disposition:
                    content_disposition = probed_disposition

                name, ext = name_resolver(content_type, content_disposition, final_url)

                if not content_type.startswith(("audio/", "video/")):
                    await context.send_activity(
                        f"I downloaded a file of type `{content_type}` (extension `{ext or 'n/a'}`), "
                        "but I can only transcribe audio or video files like .mp3, .wav, .m4a, .mp4."
                    )
                    return

                if content_length is None:
                    await context.send_activity(
                        "I couldn't determine the file size for a streaming upload. "
                        "Please provide a direct download link with a Content-Length header."
                    )
                    return

                submit_cb = on_submit
                if submit_cb is None and on_submit_factory is not None:
                    submit_cb = await on_submit_factory(name, ext, content_type)

                try:
                    object_key = await _upload_stream_to_object(
                        stream=response.aiter_bytes(),
                        size=content_length,
                        content_type=content_type,
                        filename=f"{name}{ext}",
                    )
                except Exception as err:
                    logger.exception("Failed to upload streamed file")
                    await context.send_activity(
                        f"I couldn't upload the file for transcription: {getattr(err, 'message', str(err))}"
                    )
                    return

        try:
            status, result = await _start_transcription_from_object_key(
                name=name,
                ext=ext,
                object_key=object_key,
                content_type=content_type,
                pipeline_id=pipeline_id,
                keyterms=keyterms,
                number_of_participants=number_of_participants,
                on_submit=submit_cb,
            )
        except Exception as err:
            logger.exception("Failed to start transcription for streamed file")
            await context.send_activity(
                f"I couldn't start transcription: {getattr(err, 'message', str(err))}"
            )
            return

        job_id = (result or {}).get("id") if isinstance(result, dict) else None
        transcription = (
            (result or {}).get("transcription") if isinstance(result, dict) else None
        )

        await _send_transcription_summary(
            context,
            status=status,
            job_id=job_id,
            transcription=transcription,
            pipeline_id=pipeline_id,
            conversation_date=conversation_date,
            conversation_time=conversation_time,
            settings_system_name=settings_system_name,
            meeting_context=meeting_context,
            settings=settings,
            keyterms=keyterms,
            invited_people=invited_people,
            send_expandable_section=send_expandable_section,
            load_settings_by_system_name=load_settings_by_system_name,
            load_settings_for_context=load_settings_for_context,
            resolve_meeting_details=resolve_meeting_details,
        )
        return

    if kind == "job":
        if not job_id:
            raise ValueError("job_id is required for kind='job'.")
        await send_typing(context)
        meeting = resolve_meeting_details(context)
        meeting_part = _get_meeting_id_part(meeting)
        settings: dict[str, Any] | None = None
        invited_people: list[dict[str, str]] = []
        try:
            loaded = (
                await load_settings_by_system_name(settings_system_name)
                if settings_system_name
                else await load_settings_for_context(context)
            )
            if isinstance(loaded, dict):
                settings = loaded
        except Exception as err:
            logger.debug(
                "Failed to load keyterms for transcription job mode: %s",
                getattr(err, "message", str(err)),
            )
        try:
            invited_people = await get_invited_people(context)
        except Exception as err:
            logger.debug(
                "Failed to load invited people for keyterms in job mode: %s",
                getattr(err, "message", str(err)),
            )
        keyterms: list[str] | None = (
            _build_transcription_keyterms(
                settings=settings,
                invited_people=invited_people,
            )
            if settings is not None
            else None
        )
        source_file_type = "application/json"
        try:
            meta = await transcription_service.get_transcription(job_id)
        except Exception as err:
            logger.debug(
                "Failed to read transcription metadata for %s: %s",
                job_id,
                getattr(err, "message", str(err)),
            )
            meta = None

        if not conversation_date:
            created_at = (meta or {}).get("created_at")
            if created_at:
                conversation_date = _format_recording_date_iso(created_at)

        date_part = (
            _format_recording_date_compact(conversation_date)
            if conversation_date
            else dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
        )
        source_file_name = _build_note_taker_filename(
            kind="transcription",
            meeting_id=meeting_part,
            item_id=job_id,
            date_part=date_part,
            ext=".json",
        )
        stored_name = (meta or {}).get("filename") or ""
        stored_ext = (meta or {}).get("file_ext") or ""
        stored_content_type = (meta or {}).get("content_type") or ""
        if stored_name and stored_ext:
            source_file_name = f"{stored_name}{stored_ext}"
        if stored_content_type:
            source_file_type = stored_content_type

        if build_on_submit_callback is not None:
            on_submit = await build_on_submit_callback(
                context,
                conversation_date=conversation_date,
                source_file_name=source_file_name,
                source_file_type=source_file_type,
            )
            if on_submit:
                await on_submit(job_id)

        try:
            status = await transcription_service.get_status(job_id)
        except Exception as err:
            logger.exception("Failed to fetch transcription status for %s", job_id)
            await context.send_activity(
                f"Could not retrieve transcription status for job {job_id}: {getattr(err, 'message', str(err))}"
            )
            return

        transcription = None
        if status in {"completed", "transcribed", "diarized"}:
            try:
                transcription = await transcription_service.get_transcription(job_id)
            except Exception as err:
                logger.exception("Failed to fetch transcription for %s", job_id)
                await context.send_activity(
                    f"Could not retrieve transcription for job {job_id}: {getattr(err, 'message', str(err))}"
                )
                return

        await _send_transcription_summary(
            context,
            status=status or "unknown",
            job_id=job_id,
            transcription=transcription,
            pipeline_id=None,
            conversation_date=conversation_date,
            conversation_time=conversation_time,
            settings_system_name=settings_system_name,
            meeting_context=meeting_context,
            settings=settings,
            keyterms=keyterms,
            invited_people=invited_people,
            send_expandable_section=send_expandable_section,
            load_settings_by_system_name=load_settings_by_system_name,
            load_settings_for_context=load_settings_for_context,
            resolve_meeting_details=resolve_meeting_details,
        )
        return

    raise ValueError(f"Unknown transcription pipeline kind: {kind}")
