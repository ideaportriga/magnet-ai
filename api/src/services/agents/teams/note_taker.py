import asyncio
import mimetypes
import datetime as dt
import os
import base64
from pathlib import Path
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse, quote, unquote
from types import SimpleNamespace

import httpx
from microsoft_agents.activity import (
    Activity,
    ActionTypes,
    CardAction,
    ChannelAccount,
    ConversationReference,
    Mention,
    OAuthCard,
    TextFormatTypes,
)
from microsoft_agents.authentication.msal import MsalAuth
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    AuthTypes,
    TurnContext,
    TurnState,
)
from microsoft_agents.hosting.core.app.app_options import ApplicationOptions
from microsoft_agents.hosting.core.app import AuthHandler
from microsoft_agents.hosting.core.app.oauth import Authorization
from microsoft_agents.hosting.core.app.oauth.authorization import (
    AUTHORIZATION_TYPE_MAP,
)
from microsoft_agents.hosting.core.app.oauth._handlers._user_authorization import (
    _UserAuthorization,
)
from microsoft_agents.hosting.core._oauth import _FlowStateTag
from microsoft_agents.hosting.core.rest_channel_service_client_factory import (
    RestChannelServiceClientFactory,
)
from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.card_factory import CardFactory
from microsoft_agents.hosting.core.message_factory import MessageFactory
from microsoft_agents.hosting.teams import TeamsInfo

from core.db.session import async_session_maker
from core.db.models.teams import TeamsMeeting, TeamsUser
from sqlalchemy import func, select, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from .config import NOTE_TAKER_GRAPH_SCOPES, ISSUER, SCOPE
from .graph import (
    GRAPH_BASE_URL,
    create_graph_client_with_token,
    get_meeting_recordings,
    get_recording_by_id,
)
from .static_connections import StaticConnections
from .teams_user_store import upsert_teams_user, normalize_bot_id
from speech_to_text.transcription import service as transcription_service
from services.prompt_templates import execute_prompt_template
from stores import get_db_client
from utils import upload_handler

logger = getLogger(__name__)


ENV_PREFIX = "TEAMS_NOTE_TAKER_"
_DEFAULT_TRANSCRIPTION_LANGUAGE = os.getenv(f"{ENV_PREFIX}TRANSCRIPTION_LANGUAGE", "en")
_DEFAULT_PIPELINE_ID = os.getenv(f"{ENV_PREFIX}TRANSCRIPTION_PIPELINE", "elevenlabs")
_TRANSCRIPTION_TIMEOUT_SECONDS = float(
    os.getenv(f"{ENV_PREFIX}TRANSCRIPTION_TIMEOUT_SECONDS", "900")
)
_TRANSCRIPTION_POLL_SECONDS = float(
    os.getenv(f"{ENV_PREFIX}TRANSCRIPTION_POLL_SECONDS", "5")
)
PROMPT_TEMPLATE_STT_SUMMARY = "STT_SUMMARY"
PROMPT_TEMPLATE_STT_CHAPTERS = "STT_CHAPTERS"
PROMPT_TEMPLATE_STT_INSIGHTS = "STT_INSIGHTS"
_ORGANIZER_SIGN_IN_PROMPT = (
    "I need you to sign in with /sign-in in our 1:1 chat so I can access meeting resources."
)


def _format_duration(seconds: float | int | None) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return "Unknown"
    try:
        total_seconds = float(seconds)
    except (TypeError, ValueError):
        return "Unknown"
    if total_seconds < 0:
        return "Unknown"

    whole_seconds = int(total_seconds)
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    fractional = total_seconds - whole_seconds
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    if fractional:
        return f"{total_seconds:.1f}s"
    return f"{secs}s"


def _format_mm_ss(seconds: float | int | None) -> str:
    """Format seconds to mm:ss with leading zeros."""
    try:
        total_seconds = int(float(seconds))
    except (TypeError, ValueError):
        return "00:00"
    total_seconds = max(total_seconds, 0)
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def _format_file_size(size_bytes: int | None) -> str:
    """Format file size in bytes to human-readable string."""
    if size_bytes is None:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_recording_datetime(iso_datetime: str | None) -> tuple[str, str]:
    if not iso_datetime:
        return ("Unknown date", "Unknown time")
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
        date_str = dt_obj.strftime("%b %d, %Y")
        time_str = dt_obj.strftime("%I:%M %p UTC")
        return (date_str, time_str)
    except Exception:
        return (iso_datetime, "")


def _format_recording_date_iso(iso_datetime: str | None) -> str | None:
    if not iso_datetime:
        return None
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    except Exception:
        return None
    return dt_obj.date().isoformat()


async def _ensure_vector_pool_ready() -> None:
    """Block until the pgvector pool is ready (to fix the issue with the first call after the startup)."""
    try:
        client = get_db_client()
        init = getattr(client, "init_pool", None)
        if callable(init):
            await init()
    except Exception as exc:
        logger.warning("Failed to pre-initialize vector DB pool: %s", exc)


def _parse_content_disposition_filename(header_value: str | None) -> str | None:
    if not header_value:
        return None
    parts = header_value.split(";")
    for part in parts:
        part = part.strip()
        if part.lower().startswith("filename*="):
            value = part.split("=", 1)[1]
            if "''" in value:
                value = value.split("''", 1)[1]
            return value.strip("\"'")
        if part.lower().startswith("filename="):
            value = part.split("=", 1)[1]
            return value.strip("\"'")
    return None


def _guess_filename_from_link(link: str) -> str:
    parsed = urlparse(link)
    filename = Path(parsed.path).name
    if filename:
        return filename

    query = parse_qs(parsed.query)
    file_urls = (
        query.get("fileUrl")
        or query.get("fileurl")
        or query.get("file_url")
        or query.get("file")
    )
    if file_urls:
        nested_url = file_urls[0]
        nested_parsed = urlparse(nested_url)
        nested_name = Path(nested_parsed.path).name
        if nested_name:
            return nested_name

    return "file"


def _format_iso_datetime(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return value


async def _download_file_from_link(
    link: str, token: str | None
) -> tuple[bytes, str, str, str]:
    # Unwrap Teams deep links first
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    file_urls = (
        query.get("fileUrl")
        or query.get("fileurl")
        or query.get("file_url")
        or query.get("file")
    )
    if file_urls:
        link = file_urls[0]
        parsed = urlparse(link)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # If it's a SharePoint/OneDrive URL, go via Graph /shares
    if parsed.netloc.endswith("sharepoint.com") or "d.docs.live.net" in parsed.netloc:
        # Build Graph /shares URL
        raw_url = link
        # base64url encode WITHOUT padding
        share_id = "u!" + base64.urlsafe_b64encode(raw_url.encode("utf-8")).decode(
            "ascii"
        ).rstrip("=")
        graph_download_url = (
            f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
        )

        download_url = graph_download_url
    else:
        # Otherwise download directly
        download_url = link

    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        async with client.stream("GET", download_url, headers=headers) as response:
            response.raise_for_status()
            buf = bytearray()
            async for chunk in response.aiter_bytes():
                if chunk:
                    buf.extend(chunk)

            content_type = (
                (response.headers.get("Content-Type") or "application/octet-stream")
                .split(";")[0]
                .strip()
            )

            filename = _parse_content_disposition_filename(
                response.headers.get("Content-Disposition")
            )
            if not filename:
                filename = _guess_filename_from_link(str(response.url) or link)

            path = Path(filename)
            name = path.stem or "file"
            ext = path.suffix
            if not ext:
                guessed_ext = mimetypes.guess_extension(content_type) or ".bin"
                ext = guessed_ext

    return bytes(buf), content_type, name, ext


@dataclass(frozen=True, slots=True)
class NoteTakerSettings:
    client_id: str
    client_secret: str
    tenant_id: str
    auth_handler_id: str

    @classmethod
    def from_env(cls) -> "NoteTakerSettings | None":
        client_id = os.getenv(f"{ENV_PREFIX}clientId", "").strip()
        client_secret = os.getenv(f"{ENV_PREFIX}clientSecret", "").strip()
        tenant_id = os.getenv(f"{ENV_PREFIX}tenantId", "").strip()
        auth_handler_id = os.getenv(f"{ENV_PREFIX}AUTH_HANDLER_ID", "").strip()

        if not all([client_id, client_secret, tenant_id, auth_handler_id]):
            logger.info(
                "Teams note-taker bot env vars missing; skipping bot initialization."
            )
            return None

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            auth_handler_id=auth_handler_id,
        )


@dataclass(slots=True)
class NoteTakerRuntime:
    validation_config: AgentAuthConfiguration
    adapter: CloudAdapter
    agent_app: AgentApplication[TurnState]
    auth_handler_id: str


class _CustomUserAuthorization(_UserAuthorization):
    """Override OAuth card content without modifying the SDK package."""

    async def _handle_flow_response(self, context: TurnContext, flow_response):
        flow_state = flow_response.flow_state

        if flow_state.tag == _FlowStateTag.BEGIN:
            sign_in_resource = flow_response.sign_in_resource
            assert sign_in_resource

            button_title = self._handler.title or "Sign in."
            card_text = self._handler.text or "Sign in.."

            o_card = CardFactory.oauth_card(
                OAuthCard(
                    text=card_text,
                    connection_name=flow_state.connection,
                    buttons=[
                        CardAction(
                            title=button_title,
                            type=ActionTypes.signin,
                            value=sign_in_resource.sign_in_link,
                            channel_data=None,
                        )
                    ],
                    token_exchange_resource=sign_in_resource.token_exchange_resource,
                    token_post_resource=sign_in_resource.token_post_resource,
                )
            )
            await context.send_activity(MessageFactory.attachment(o_card))
            return

        await super()._handle_flow_response(context, flow_response)


# Override the default handler mapping so our custom OAuth card text/title is used.
AUTHORIZATION_TYPE_MAP["userauthorization"] = _CustomUserAuthorization


class _SignInInvokeMiddleware:
    """Ensures Teams sign-in invocations return 200 to avoid UX errors. (fixes Delegated Auth issue)"""

    async def on_turn(self, context: TurnContext, call_next):
        await call_next()

        activity = getattr(context, "activity", None)
        name = getattr(activity, "name", "") if activity else ""

        if (
            activity
            and activity.type == "invoke"
            and name in {"signin/verifyState", "signin/tokenExchange"}
        ):
            await context.send_activity(
                Activity(
                    type="invokeResponse",
                    value={"status": 200, "body": {}},
                )
            )

            # Delete the original sign-in card once the user completes sign-in to avoid double-clicking.
            reply_to_id = getattr(activity, "reply_to_id", None)
            if reply_to_id:
                try:
                    await context.delete_activity(reply_to_id)
                except Exception as err:
                    logger.debug(
                        "Failed to delete sign-in card activity %s: %s",
                        reply_to_id,
                        err,
                    )


def _is_personal_teams_conversation(context: TurnContext) -> bool:
    activity = getattr(context, "activity", None)
    conversation = getattr(activity, "conversation", None)
    conversation_type = getattr(conversation, "conversation_type", None)
    return conversation_type == "personal"


def _is_meeting_conversation(context: TurnContext) -> bool:
    activity = getattr(context, "activity", None)
    conversation = getattr(activity, "conversation", None)
    conversation_type = getattr(conversation, "conversation_type", None)
    return conversation_type == "groupChat"


def _resolve_meeting_details(context: TurnContext) -> Dict[str, Any]:
    activity = getattr(context, "activity", None)
    channel_data = getattr(activity, "channel_data", None) or {}
    conversation = getattr(activity, "conversation", None)
    meeting_data = channel_data.get("meeting") or {}
    return {
        "id": meeting_data.get("id"),
        "conversationId": getattr(conversation, "id", None),
        "joinUrl": meeting_data.get("joinUrl") or meeting_data.get("joinWebUrl"),
        "title": meeting_data.get("title") or meeting_data.get("subject"),
    }


def _resolve_user_info(context: TurnContext) -> Dict[str, Any]:
    activity = getattr(context, "activity", None)
    from_user = getattr(activity, "from_property", None) or getattr(
        activity, "from", None
    )
    conversation = getattr(activity, "conversation", None)

    return {
        "id": getattr(from_user, "id", None),
        "name": getattr(from_user, "name", None)
        or getattr(from_user, "display_name", None),
        "aad_object_id": getattr(from_user, "aad_object_id", None),
        "conversation_type": getattr(conversation, "conversation_type", None),
    }


async def _upsert_teams_user_record(context: TurnContext) -> None:
    try:
        async with async_session_maker() as session:
            try:
                await upsert_teams_user(session, context)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception as exc:
        logger.exception("Failed to upsert Teams user record: %s", exc)


async def _upsert_teams_meeting_record(
    context: TurnContext, *, is_bot_installed: bool
) -> None:
    """Upsert Teams meeting state when the bot is added or removed."""
    if not _is_meeting_conversation(context):
        return

    meeting = _resolve_meeting_details(context)
    meeting_id = meeting.get("id")
    chat_id = meeting.get("conversationId")
    if not chat_id:
        logger.debug(
            "Skipping Teams meeting upsert: missing conversation id (meeting=%s)",
            meeting,
        )
        return

    join_url = meeting.get("joinUrl")
    title = meeting.get("title")
    bot_id = normalize_bot_id(
        getattr(
            getattr(getattr(context, "activity", None), "recipient", None), "id", None
        )
    )

    online_meeting_id: str | None = None
    try:
        online_meeting_id = await _get_online_meeting_id(context)
    except Exception as exc:
        logger.debug(
            "Failed to resolve online meeting id for chat %s: %s", chat_id, exc
        )

    now = dt.datetime.now(dt.timezone.utc)
    removed_at = None if is_bot_installed else now
    added_at = now if is_bot_installed else None
    added_by = _resolve_user_info(context) if is_bot_installed else {}

    insert_stmt = pg_insert(TeamsMeeting).values(
        chat_id=chat_id,
        meeting_id=meeting_id,
        graph_online_meeting_id=online_meeting_id,
        join_url=join_url,
        title=title,
        bot_id=bot_id,
        is_bot_installed=is_bot_installed,
        removed_from_meeting_at=removed_at,
        added_to_meeting_at=added_at,
        added_by_user_id=added_by.get("id"),
        added_by_aad_object_id=added_by.get("aad_object_id"),
        added_by_display_name=added_by.get("name"),
        last_seen_at=now,
    )

    update_values: dict[str, Any] = {
        "is_bot_installed": is_bot_installed,
        "removed_from_meeting_at": removed_at,
        "last_seen_at": now,
        "updated_at": func.now(),
    }
    if meeting_id is not None:
        update_values["meeting_id"] = meeting_id
    if join_url is not None:
        update_values["join_url"] = join_url
    if title is not None:
        update_values["title"] = title
    if bot_id is not None:
        update_values["bot_id"] = bot_id
    if online_meeting_id:
        update_values["graph_online_meeting_id"] = online_meeting_id
    if is_bot_installed:
        update_values["added_to_meeting_at"] = added_at
        if added_by.get("id"):
            update_values["added_by_user_id"] = added_by["id"]
        if added_by.get("aad_object_id"):
            update_values["added_by_aad_object_id"] = added_by["aad_object_id"]
        if added_by.get("name"):
            update_values["added_by_display_name"] = added_by["name"]

    stmt = insert_stmt.on_conflict_do_update(
        index_elements=[TeamsMeeting.chat_id],
        set_=update_values,
    )

    try:
        async with async_session_maker() as session:
            try:
                await session.execute(stmt)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception as exc:
        logger.exception(
            "Failed to upsert Teams meeting record for chat %s: %s", chat_id, exc
        )


async def _fetch_organizer_conversation_reference(
    *, organizer_aad: str, bot_app_id: str
) -> dict | None:
    if not organizer_aad or not bot_app_id:
        return None

    normalized_bot_id = normalize_bot_id(bot_app_id)

    async with async_session_maker() as session:
        try:
            logger.info(
                "Organizer conversation lookup start (aad=%s, bot=%s)",
                organizer_aad,
                bot_app_id,
            )

            stmt = (
                select(TeamsUser.conversation_reference)
                .where(
                    TeamsUser.bot_id == normalized_bot_id,
                    TeamsUser.aad_object_id == organizer_aad,
                )
                .order_by(
                    TeamsUser.last_seen_at.desc(),
                )
            )
            result = await session.execute(stmt)
            conv_ref = result.scalars().first()
            if conv_ref:
                logger.info("Organizer conversation found")
            return conv_ref

        except Exception as err:
            logger.warning(
                "Failed to load organizer conversation reference from DB: %s",
                getattr(err, "message", str(err)),
            )
            return None


def _build_recording_filename(
    meeting: Dict[str, Any], recording: Dict[str, Any], content_url: str
) -> str:
    meeting_part = meeting.get("title") or meeting.get("id") or "meeting"
    rec_part = recording.get("id") or "recording"
    ext = Path(urlparse(content_url).path).suffix or ".mp4"
    base = f"{meeting_part}-{rec_part}"
    return f"{base}{ext}"


async def _download_recording_bytes(
    recording: Dict[str, Any],
    token: str,
    meeting: Dict[str, Any],
) -> tuple[bytes, str, str, str] | None:
    """Fetch recording content into memory (full memory read)."""
    content_url = recording.get("contentUrl")
    if not content_url:
        return None

    filename = _build_recording_filename(meeting, recording, content_url)
    name = Path(filename).stem
    ext = Path(filename).suffix

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        async with client.stream("GET", content_url, headers=headers) as response:
            response.raise_for_status()
            buf = bytearray()
            async for chunk in response.aiter_bytes():
                if chunk:
                    buf.extend(chunk)
            content_type = (
                (response.headers.get("Content-Type") or "application/octet-stream")
                .split(";")[0]
                .strip()
            )
    return bytes(buf), content_type, name, ext


async def _start_transcription_from_bytes(
    *,
    name: str,
    ext: str,
    data: bytes,
    content_type: str,
    language: str,
    pipeline_id: str,
) -> tuple[str, dict | None]:
    await _ensure_vector_pool_ready()

    ext_no_dot = ext.lstrip(".")
    ext_with_dot = f".{ext_no_dot}" if ext_no_dot else ""

    session = await upload_handler.make_multipart_session(
        filename=f"{name}{ext_with_dot}",
        size=len(data),
        content_type=content_type,
    )

    object_key = (session or {}).get("object_key")
    upload_url = (session or {}).get("upload_url") or (session or {}).get("url")
    upload_headers: dict[str, str] = (session or {}).get("upload_headers") or {}
    if not upload_url:
        presigned_urls = (session or {}).get("presigned_urls") or []
        upload_url = presigned_urls[0] if presigned_urls else None

    if not object_key:
        raise RuntimeError("Upload session did not return an object key.")

    logger.info("[teams note-taker] uploading bytes to object: %s", object_key)
    logger.info("[teams note-taker] upload_url: %s", upload_url)

    if not upload_url:
        raise RuntimeError("Upload session missing upload URL.")

    upload_headers = {
        "Content-Type": content_type,
        **upload_headers,
    }

    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        response = await client.put(
            upload_url,
            content=data,
            headers=upload_headers,
        )
        response.raise_for_status()

    job_id = await transcription_service.submit(
        name=name,
        ext=ext_no_dot,
        bytes_=None,
        object_key=object_key,
        content_type=content_type,
        backend=pipeline_id,
        # language=language,
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


async def _send_transcription_summary(
    context: TurnContext,
    status: str,
    job_id: str | None,
    transcription: dict | None,
    conversation_date: str | None = None,
) -> None:
    duration = None
    transcript_payload = transcription
    if isinstance(transcription, dict):
        duration = transcription.get("duration")
        nested = transcription.get("transcription")
        if isinstance(nested, dict):
            transcript_payload = nested
        job_id = job_id or transcription.get("job_id") or transcription.get("id")

    if duration is None and isinstance(transcript_payload, dict):
        duration = transcript_payload.get("duration")

    duration_str = _format_duration(duration) if duration is not None else None
    if duration_str == "Unknown":
        duration_str = None

    if status in {"completed", "transcribed", "diarized"}:
        segs_count = 0
        full_text = None
        participants: list[str] = []
        if isinstance(transcript_payload, dict):
            segs = transcript_payload.get("segments") or []
            segs_count = len(segs)
            full_text = transcript_payload.get("text") or ""
            if segs:
                lines = []
                seen_participants: set[str] = set()
                for s in segs:
                    if not isinstance(s, dict):
                        continue
                    speaker = s.get("speaker") or "speaker_0"
                    if speaker not in seen_participants:
                        seen_participants.add(speaker)
                        participants.append(speaker)
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
        await context.send_activity(
            f"Transcription completed (job={job_id or 'n/a'}, segments={segs_count}{duration_part})."
        )
        if full_text:
            snippet = full_text[:1000]
            suffix = "." if len(full_text) > len(snippet) else ""
            await context.send_activity(f"Transcript text: {snippet}{suffix}")
        elif segs_count == 0:
            await context.send_activity("No speech was detected in this recording.")

        if full_text:
            templates = [
                (PROMPT_TEMPLATE_STT_SUMMARY, "Summary"),
                (PROMPT_TEMPLATE_STT_CHAPTERS, "Chapters"),
                (PROMPT_TEMPLATE_STT_INSIGHTS, "Insights"),
            ]

            async def _run_template(system_name: str):
                return await execute_prompt_template(
                    system_name_or_config=system_name,
                    template_values={
                        "transcription": full_text,
                        "participants": participants,
                        "language": "the same as the transcription",
                        "conversation_date": conversation_date or "",
                    },
                )

            results = await asyncio.gather(
                *(_run_template(system_name) for system_name, _ in templates),
                return_exceptions=True,
            )

            for (system_name, title), result in zip(templates, results):
                if isinstance(result, Exception):
                    logger.warning(
                        "Prompt template %s failed for transcription job %s: %s",
                        system_name,
                        job_id,
                        getattr(result, "message", str(result)),
                    )
                    await context.send_activity(f"{title} generation failed.")
                    continue

                await context.send_activity(f"{title}:\n{result.content}")
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


async def _get_online_meeting_id(context: TurnContext) -> Optional[str]:
    meeting_info = await TeamsInfo.get_meeting_info(context)
    details = getattr(meeting_info, "details", None) or {}
    return getattr(details, "ms_graph_resource_id", None)


def _resolve_recordings_ready_webhook_url() -> str | None:
    base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base_url:
        return f"{base_url}/api/user/agents/teams/webhooks/recordings-ready"

    return None


def _resolve_recordings_lifecycle_webhook_url() -> str | None:
    base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base_url:
        return f"{base_url}/api/user/agents/teams/webhooks/recordings-lifecycle"

    return None


def _extract_meeting_id_from_notification(notification: dict[str, Any]) -> str | None:
    resource_data = notification.get("resourceData") or {}
    meeting_id = resource_data.get("meetingId")
    if meeting_id:
        return meeting_id

    resource = str(notification.get("resource") or "")
    if not resource:
        return None
    # Look for onlineMeetings('...') in the resource string
    marker = "onlineMeetings("
    if marker in resource:
        start = resource.index(marker) + len(marker)
        end = resource.find(")", start)
        if end > start:
            raw = resource[start:end].strip("'\"")
            return unquote(raw)
    return None


def _extract_user_from_resource(notification: dict[str, Any]) -> str | None:
    resource = str(notification.get("resource") or "")
    if not resource:
        return None
    if "users(" not in resource:
        return None
    try:
        start = resource.index("users(") + len("users(")
        end = resource.index(")", start)
        return unquote(resource[start:end]).strip("'\"")
    except ValueError:
        return None


async def _lookup_conversation_reference_by_user_hint(
    session,
    *,
    bot_app_id: str | None,
    user_hint: str,
):
    """Try to find a TeamsUser conversation reference by either AAD or Teams user id."""
    if not user_hint or not bot_app_id:
        return None

    normalized_bot = normalize_bot_id(bot_app_id)
    stmt = (
        select(TeamsUser.conversation_reference)
        .where(
            or_(
                TeamsUser.aad_object_id == user_hint,
                TeamsUser.teams_user_id == user_hint,
            ),
            TeamsUser.bot_id == normalized_bot,
        )
        .order_by(TeamsUser.last_seen_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().first()


def _register_note_taker_handlers(
    app: AgentApplication[TurnState],
    auth_handler_id: str,
    *,
    adapter: CloudAdapter,
    bot_app_id: str,
    bot_tenant_id: str,
) -> None:
    async def _send_typing(context: TurnContext) -> None:
        try:
            await context.send_activity(Activity(type="typing"))
        except Exception as err:
            logger.debug(
                "Failed to send typing indicator: %s",
                getattr(err, "message", str(err)),
            )

    async def _get_delegated_token(
        context: TurnContext,
        handler_id: str,
        failure_message: str,
    ) -> str | None:
        try:
            # app.auth.get_token(context, handler_id) returns cached token?
            handler = app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            token = getattr(token_response, "token", None)
            # logger.info("[teams note-taker] delegated token: %s", token)
            return token
        except Exception as err:
            logger.error(
                "Auth failed handler_id=%s message=%s",
                handler_id,
                getattr(err, "message", str(err)),
            )

        # If we get here, either no token or an error.
        await context.send_activity(failure_message)
        return None

    async def _send_recordings_summary(
        context: TurnContext, recordings: list, token: str
    ) -> None:
        if not recordings:
            await context.send_activity("No recordings found.")
            return

        lines = [f"📹 Found {len(recordings)} recording(s):"]

        for idx, rec in enumerate(recordings, start=1):
            file_size = rec.get("size")
            duration = rec.get("duration")
            rec_id = rec.get("id") or "n/a"
            date_str, time_str = _format_recording_datetime(rec.get("createdDateTime"))
            size_str = _format_file_size(file_size)

            duration_str = _format_duration(duration) if duration is not None else None

            parts = [f"{idx}. 📅 {date_str} ⏰ {time_str}"]
            if duration_str:
                parts.append(f"⏱️ {duration_str}")
            parts.append(f"💾 {size_str}")
            parts.append(f"id={rec_id}")

            lines.append("   ".join(parts))

        await context.send_activity("\n\n".join(lines))

    async def _transcribe_bytes_and_notify(
        context: TurnContext,
        *,
        name: str,
        ext: str,
        file_bytes: bytes,
        content_type: str,
        conversation_date: str | None = None,
    ) -> None:
        await _send_typing(context)
        if not content_type.startswith(("audio/", "video/")):
            await context.send_activity(
                f"I downloaded a file of type `{content_type}` (extension `{ext or 'n/a'}`), "
                "but I can only transcribe audio or video files like .mp3, .wav, .m4a, .mp4."
            )
            return

        try:
            status, result = await _start_transcription_from_bytes(
                name=name,
                ext=ext,
                data=file_bytes,
                content_type=content_type,
                language=_DEFAULT_TRANSCRIPTION_LANGUAGE,
                pipeline_id=_DEFAULT_PIPELINE_ID,
            )
        except Exception as err:
            logger.exception("Failed to start transcription for streamed file")
            await context.send_activity(
                f"I couldn't start transcription: {getattr(err, 'message', str(err))}"
            )
            return

        logger.info(
            "[teams note-taker] transcription result: %s",
            result,
        )

        job_id = (result or {}).get("id") if isinstance(result, dict) else None
        transcription = (
            (result or {}).get("transcription") if isinstance(result, dict) else None
        )

        await _send_transcription_summary(
            context,
            status,
            job_id,
            transcription,
            conversation_date=conversation_date,
        )

    async def _has_existing_token(context: TurnContext, handler_id: str) -> bool:
        """Try to detect an existing ABS token without sending a new OAuth card."""
        try:
            handler = app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            return bool(getattr(token_response, "token", None))
        except Exception as err:
            logger.debug(
                "Token precheck failed during install flow (handler=%s): %s",
                handler_id,
                getattr(err, "message", str(err)),
            )
            return False

    async def _get_meeting_organizer_identity(
        context: TurnContext,
    ) -> dict[str, str | None]:
        meeting_info = await TeamsInfo.get_meeting_info(context)
        organizer_obj = getattr(meeting_info, "organizer", None) or {}
        return {
            "id": getattr(organizer_obj, "id", None),
            "aad_object_id": getattr(organizer_obj, "aadObjectId", None),
        }

    async def _build_organizer_mention_activity(
        context: TurnContext, *, organizer_id: str | None, organizer_aad: str | None
    ) -> Activity | None:
        if not organizer_id:
            return None
        try:
            member = await TeamsInfo.get_member(context, organizer_id)
        except Exception:
            return None

        organizer_name = (
            getattr(member, "name", None)
            or getattr(member, "user_principal_name", None)
            or getattr(member, "email", None)
        )
        if not organizer_name:
            return None

        mention_text = f"<at>{organizer_name}</at>"
        mention = Mention(
            mentioned=ChannelAccount(
                id=organizer_id,
                name=organizer_name,
                aad_object_id=organizer_aad,
            ),
            text=mention_text,
        )
        return Activity(
            type="message",
            text=f"{mention_text} {_ORGANIZER_SIGN_IN_PROMPT}",
            text_format=TextFormatTypes.xml,
            entities=[mention],
        )

    async def _send_organizer_sign_in_prompt(
        context: TurnContext, *, organizer_id: str | None, organizer_aad: str | None
    ) -> None:
        activity = await _build_organizer_mention_activity(
            context, organizer_id=organizer_id, organizer_aad=organizer_aad
        )
        if activity:
            await context.send_activity(activity)
            return
        await context.send_activity(_ORGANIZER_SIGN_IN_PROMPT)

    async def _is_meeting_organizer(context: TurnContext) -> bool:
        user = _resolve_user_info(context)
        organizer = await _get_meeting_organizer_identity(context)
        organizer_id = organizer.get("id")
        organizer_aad = organizer.get("aad_object_id")

        user_id = user.get("id")
        user_aad = user.get("aad_object_id")

        if user_id and organizer_id and user_id == organizer_id:
            return True
        if user_aad and organizer_aad and user_aad == organizer_aad:
            return True
        return False

    async def _ensure_meeting_organizer_and_signed_in(
        context: TurnContext, handler_id: str
    ) -> bool:
        try:
            is_organizer = await _is_meeting_organizer(context)
        except Exception as err:
            logger.warning(
                "Unable to verify meeting organizer: %s",
                getattr(err, "message", str(err)),
            )
            await context.send_activity(
                "I couldn't verify that you're the meeting organizer. Please try again or message me directly."
            )
            return False

        if not is_organizer:
            await context.send_activity(
                "Meeting commands are accepted only from the meeting organizer."
            )
            return False

        signed_in = await _has_existing_token(context, handler_id)
        if not signed_in:
            await context.send_activity(
                "Please authenticate with me in our cozy 1:1 chat before using meeting commands."
            )
            return False

        return True

    async def _ensure_organizer_delegated_token_cached(  # TODO: remove this
        context: TurnContext,
        handler_id: str,
        *,
        prompt_on_missing: bool = True,
    ) -> bool:
        if not _is_meeting_conversation(context):
            return False

        try:
            organizer = await _get_meeting_organizer_identity(context)
        except Exception as err:
            logger.warning(
                "Unable to resolve meeting organizer for delegated token check: %s",
                getattr(err, "message", str(err)),
            )
            return False

        organizer_aad = organizer.get("aad_object_id")
        organizer_id = organizer.get("id")
        if not organizer_aad and not organizer_id:
            logger.info(
                "Organizer identity missing; skipping delegated token check for meeting."
            )
            return False

        conv_ref = await _fetch_organizer_conversation_reference(
            organizer_aad=organizer_aad, bot_app_id=bot_app_id
        )

        if not conv_ref:
            logger.info(
                "No organizer personal conversation reference available for token check."
            )
            if prompt_on_missing:
                await _send_organizer_sign_in_prompt(
                    context, organizer_id=organizer_id, organizer_aad=organizer_aad
                )
            return False

        token = await _get_token_proactively(
            adapter=adapter,
            app=app,
            bot_app_id=bot_app_id,
            conv_ref=conv_ref,
            handler_id=handler_id,
            aad_object_id=organizer_aad,
            user_id=organizer_id,
            tenant_id=bot_tenant_id,
            notify_if_missing=False,
        )

        if token:
            logger.info("Organizer delegated token already cached for this meeting.")
            return True

        if prompt_on_missing:
            await _send_organizer_sign_in_prompt(
                context, organizer_id=organizer_id, organizer_aad=organizer_aad
            )

        return False

    async def _handle_install_flow(context: TurnContext, _state: TurnState) -> None:
        if not _is_personal_teams_conversation(context):
            return

        try:
            already_signed_in = await _has_existing_token(context, auth_handler_id)
        except Exception:
            already_signed_in = False

        if already_signed_in:
            return

        await context.send_activity(
            "Thanks for installing the Magnet note taker bot. Please sign in so I can access your meeting recordings."
        )
        try:
            await app.auth._start_or_continue_sign_in(context, _state, auth_handler_id)
        except Exception as err:
            logger.warning(
                "Failed to start sign-in on installation: %s",
                getattr(err, "message", str(err)),
            )

    async def _handle_recordings_find(
        context: TurnContext, state: Optional[TurnState]
    ) -> None:
        meeting = _resolve_meeting_details(context)
        if not (meeting.get("id") or meeting.get("conversationId")):
            logger.warning("No meeting id found for recordings-find command.")
            return

        delegated_token = await _get_delegated_token(
            context,
            auth_handler_id,
            "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
        )
        if not delegated_token:
            return

        await _send_typing(context)

        try:
            online_meeting_id = await _get_online_meeting_id(context)
            if not online_meeting_id:
                await context.send_activity(
                    "No online meeting id found for this meeting."
                )
                return

            async with create_graph_client_with_token(delegated_token) as graph_client:
                recordings = await get_meeting_recordings(
                    client=graph_client,
                    online_meeting_id=online_meeting_id,
                    add_size=True,
                    content_token=delegated_token,
                )
        except Exception as err:
            logger.exception("Failed to fetch meeting recordings")
            await context.send_activity(
                f"Could not retrieve meeting recordings for {meeting.get('title') or 'meeting'}: {getattr(err, 'message', str(err))}"
            )
            return

        await _send_recordings_summary(context, recordings, delegated_token)

        if recordings:
            await context.send_activity("Streaming the latest recording now...")
            await _send_typing(context)
            try:
                recording_bytes = await _download_recording_bytes(
                    recordings[0], delegated_token, meeting
                )
            except Exception as err:
                logger.exception("Failed to download first recording")
                await context.send_activity(
                    f"I couldn't download the first recording: {getattr(err, 'message', str(err))}"
                )
                return

            if recording_bytes:
                file_bytes, content_type, name, ext = recording_bytes
                await context.send_activity(
                    "Recording downloaded; starting transcription..."
                )
                await _send_typing(context)

                await _transcribe_bytes_and_notify(
                    context,
                    name=name,
                    ext=ext,
                    file_bytes=file_bytes,
                    content_type=content_type,
                    conversation_date=_format_recording_date_iso(
                        recordings[0].get("createdDateTime")
                    ),
                )
            else:
                await context.send_activity(
                    "The first recording had no downloadable URL."
                )

    async def _handle_process_recording(
        context: TurnContext, state: Optional[TurnState], recording_id: str
    ) -> None:
        meeting = _resolve_meeting_details(context)
        if not (meeting.get("id") or meeting.get("conversationId")):
            logger.warning("No meeting id found for process-recording command.")
            await context.send_activity(
                "No meeting information available in this chat."
            )
            return

        delegated_token = await _get_delegated_token(
            context,
            auth_handler_id,
            "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
        )
        if not delegated_token:
            return

        await _send_typing(context)

        try:
            online_meeting_id = await _get_online_meeting_id(context)
            if not online_meeting_id:
                await context.send_activity(
                    "No online meeting id found for this meeting."
                )
                return

            async with create_graph_client_with_token(delegated_token) as graph_client:
                recording = await get_recording_by_id(
                    client=graph_client,
                    online_meeting_id=online_meeting_id,
                    recording_id=recording_id,
                )
        except Exception as err:
            logger.exception("Failed to fetch recording by id")
            await context.send_activity(
                f"Could not retrieve recording {recording_id}: {getattr(err, 'message', str(err))}"
            )
            return

        if not recording:
            await context.send_activity(f"No recording found with id {recording_id}.")
            return

        if recording and not recording.get("contentUrl"):
            if recording.get("recordingContentUrl"):
                recording["contentUrl"] = recording.get("recordingContentUrl")

        try:
            recording_bytes = await _download_recording_bytes(
                recording, delegated_token, meeting
            )
        except Exception as err:
            logger.exception("Failed to download recording by id")
            await context.send_activity(
                f"I couldn't download recording {recording_id}: {getattr(err, 'message', str(err))}"
            )
            return

        if not recording_bytes:
            await context.send_activity("Recording did not include a downloadable URL.")
            return

        file_bytes, content_type, name, ext = recording_bytes
        await context.send_activity("Recording downloaded; starting transcription...")
        await _send_typing(context)

        await _transcribe_bytes_and_notify(
            context,
            name=name,
            ext=ext,
            file_bytes=file_bytes,
            content_type=content_type,
            conversation_date=_format_recording_date_iso(
                recording.get("createdDateTime")
            ),
        )

    async def _handle_process_file(
        context: TurnContext, state: Optional[TurnState], link: str
    ) -> None:
        delegated_token = await _get_delegated_token(
            context,
            auth_handler_id,
            "Please sign in (File processing) so I can fetch the link with delegated Graph permissions.",
        )
        if not delegated_token:
            return

        await _send_typing(context)

        await context.send_activity("Fetching the file from your link...")

        try:
            file_bytes, content_type, name, ext = await _download_file_from_link(
                link, delegated_token
            )
        except Exception as err:
            logger.exception("Failed to download file from link")
            await context.send_activity(
                f"I couldn't download that link: {getattr(err, 'message', str(err))}"
            )
            return

        await context.send_activity("File downloaded; starting transcription...")

        await _transcribe_bytes_and_notify(
            context,
            name=name,
            ext=ext,
            file_bytes=file_bytes,
            content_type=content_type,
        )

    async def _get_token_proactively(
        *,
        adapter: CloudAdapter,
        app: AgentApplication,
        bot_app_id: str,
        conv_ref,
        handler_id: str,
        aad_object_id: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        notify_if_missing: bool = True,
    ) -> str | None:
        continuation = Activity.create_event_activity()
        continuation.name = "proactiveTokenCheck"

        normalized_ref = ConversationReference.model_validate(conv_ref)

        continuation.apply_conversation_reference(normalized_ref, is_incoming=True)

        if aad_object_id and getattr(continuation, "from_property", None):
            continuation.from_property.aad_object_id = aad_object_id
        if user_id and getattr(continuation, "from_property", None):
            continuation.from_property.id = user_id

        if tenant_id:
            continuation.channel_data = continuation.channel_data or {}
            continuation.channel_data.setdefault("tenant", {"id": tenant_id})

            conv = getattr(continuation, "conversation", None)
            if conv is not None and getattr(conv, "tenant_id", None) in (None, ""):
                try:
                    conv.tenant_id = tenant_id
                except Exception:
                    pass

        token_holder: dict[str, str | None] = {"token": None}

        async def callback(proactive_context: TurnContext):
            try:
                handler = app.auth._resolve_handler(handler_id)
                flow, _ = await handler._load_flow(proactive_context)
                token_response = await flow.get_user_token()
                token_holder["token"] = getattr(token_response, "token", None)
            except Exception as err:
                message = getattr(err, "message", None) or str(err)
                logger.warning(
                    "Proactive token check failed (handler=%s): %s",
                    handler_id,
                    message,
                )
                return

            if not token_holder["token"] and notify_if_missing:
                await proactive_context.send_activity(
                    "I need your delegated token to proceed. "
                    "Please use **/sign-in** in our 1:1 chat to authenticate."
                )

            # await proactive_context.send_activity(
            #    "I completed getting your delegated token."
            # )

        try:
            await adapter.continue_conversation(bot_app_id, continuation, callback)
        except Exception as err:
            logger.warning(
                "Proactive token check conversation failed (handler=%s): %s",
                handler_id,
                getattr(err, "message", None) or str(err),
            )

        return token_holder["token"]

    async def _get_organizer_delegated_token_from_cache(
        context: TurnContext,
    ) -> str | None:
        if not _is_meeting_conversation(context):
            return None

        try:
            organizer = await _get_meeting_organizer_identity(context)
        except Exception as err:
            logger.warning(
                "Unable to resolve meeting organizer for subscription: %s",
                getattr(err, "message", str(err)),
            )
            return None

        organizer_aad = organizer.get("aad_object_id")
        organizer_id = organizer.get("id")
        if not organizer_aad and not organizer_id:
            logger.info(
                "Organizer identity missing; skipping delegated token fetch for subscription."
            )
            return None

        conv_ref = await _fetch_organizer_conversation_reference(
            organizer_aad=organizer_aad, bot_app_id=bot_app_id
        )
        if not conv_ref:
            logger.info(
                "No organizer personal conversation reference available for subscription token fetch."
            )
            return None

        return await _get_token_proactively(
            adapter=adapter,
            app=app,
            bot_app_id=bot_app_id,
            conv_ref=conv_ref,
            handler_id=auth_handler_id,
            aad_object_id=organizer_aad,
            user_id=organizer_id,
            tenant_id=bot_tenant_id,
            notify_if_missing=False,
        )

    async def _subscribe_to_recording_notifications(
        context: TurnContext,
    ) -> None:
        webhook_url = _resolve_recordings_ready_webhook_url()
        if not webhook_url:
            logger.warning(
                "[teams note-taker] recordings-ready webhook URL not configured; skipping subscription."
            )
            return

        meeting = _resolve_meeting_details(context)
        chat_id = meeting.get("conversationId")

        online_meeting_id = await _get_online_meeting_id(context)
        if not online_meeting_id:
            logger.info(
                "[teams note-taker] cannot create recording subscription; missing online meeting id."
            )
            return

        delegated_token = await _get_organizer_delegated_token_from_cache(context)
        if not delegated_token:
            logger.info(
                "[teams note-taker] organizer delegated token unavailable; cannot create recording subscription."
            )
            return

        expiration = (
            dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=4)
        ).isoformat()
        if expiration.endswith("+00:00"):
            expiration = expiration.replace("+00:00", "Z")

        lifecycle_webhook = _resolve_recordings_lifecycle_webhook_url()

        encoded_meeting_id = quote(online_meeting_id, safe="")
        resource = f"communications/onlineMeetings/{encoded_meeting_id}/recordings"
        body = {
            "changeType": "created",
            "notificationUrl": webhook_url,
            "resource": resource,
            "expirationDateTime": expiration,
            "clientState": "recordings-ready",
            "latestSupportedTlsVersion": "v1_2",
        }
        if lifecycle_webhook:
            body["lifecycleNotificationUrl"] = lifecycle_webhook

        subscription_id = None
        expiration_dt: dt.datetime | None = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{GRAPH_BASE_URL}/subscriptions",
                    headers={"Authorization": f"Bearer {delegated_token}"},
                    json=body,
                )
                if response.status_code >= 400:
                    logger.error(
                        "[teams note-taker] recording subscription failed status=%s body=%s",
                        response.status_code,
                        response.text,
                    )
                    response.raise_for_status()

                payload = response.json()
                subscription_id = payload.get("id")
                exp_raw = payload.get("expirationDateTime")
                if exp_raw:
                    try:
                        expiration_dt = dt.datetime.fromisoformat(
                            exp_raw.replace("Z", "+00:00")
                        )
                    except Exception:
                        expiration_dt = None

                logger.info(
                    "[teams note-taker] recording subscription created id=%s expires=%s chat_id=%s meeting=%s",
                    subscription_id,
                    exp_raw,
                    chat_id,
                    online_meeting_id,
                )
        except Exception as err:
            logger.exception(
                "[teams note-taker] failed to create recording subscription for meeting %s",
                online_meeting_id,
            )
            try:
                async with async_session_maker() as session:
                    try:
                        await session.execute(
                            pg_insert(TeamsMeeting)
                            .values(
                                chat_id=chat_id,
                                graph_online_meeting_id=online_meeting_id,
                                subscription_last_error=getattr(
                                    err, "message", str(err)
                                ),
                                last_seen_at=dt.datetime.now(dt.timezone.utc),
                            )
                            .on_conflict_do_update(
                                index_elements=[TeamsMeeting.chat_id],
                                set_={
                                    "graph_online_meeting_id": online_meeting_id,
                                    "subscription_last_error": getattr(
                                        err, "message", str(err)
                                    ),
                                    "updated_at": func.now(),
                                    "last_seen_at": func.now(),
                                },
                            )
                        )
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
            except Exception:
                logger.debug(
                    "[teams note-taker] failed to persist subscription error for chat %s",
                    chat_id,
                )
            return

        if not chat_id or not subscription_id:
            return

        try:
            conv_ref_obj = context.activity.get_conversation_reference()
            conv_ref = (
                ConversationReference.model_validate(conv_ref_obj).model_dump()
                if conv_ref_obj
                else None
            )
        except Exception:
            conv_ref = None

        now = dt.datetime.now(dt.timezone.utc)
        try:
            async with async_session_maker() as session:
                try:
                    stmt = pg_insert(TeamsMeeting).values(
                        chat_id=chat_id,
                        graph_online_meeting_id=online_meeting_id,
                        subscription_id=subscription_id,
                        subscription_expires_at=expiration_dt,
                        subscription_is_active=True,
                        subscription_last_error=None,
                        subscription_conversation_reference=conv_ref,
                        last_seen_at=now,
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[TeamsMeeting.chat_id],
                        set_={
                            "graph_online_meeting_id": online_meeting_id,
                            "subscription_id": subscription_id,
                            "subscription_expires_at": expiration_dt,
                            "subscription_is_active": True,
                            "subscription_last_error": None,
                            "subscription_conversation_reference": conv_ref,
                            "last_seen_at": now,
                            "updated_at": func.now(),
                        },
                    )
                    await session.execute(stmt)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        except Exception as err:
            logger.warning(
                "[teams note-taker] failed to persist recording subscription metadata for chat %s: %s",
                chat_id,
                getattr(err, "message", str(err)),
            )

    async def _check_meeting_in_progress(
        context: TurnContext, meeting_id: str
    ) -> bool | None:
        continuation_token: str | None = None
        try:
            while True:
                paged = await TeamsInfo.get_paged_members(
                    context, page_size=20, continuation_token=continuation_token
                )
                for member in getattr(paged, "members", None) or []:
                    participant_id = getattr(member, "id", None)
                    if not participant_id:
                        continue
                    try:
                        participant = await TeamsInfo.get_meeting_participant(
                            context,
                            meeting_id=meeting_id,
                            participant_id=participant_id,
                        )
                        logger.info(
                            "[teams note-taker] participant: %s (%s)",
                            participant,
                            type(participant),
                        )
                    except Exception as err:
                        logger.debug(
                            "Meeting participant check failed (user=%s): %s",
                            participant_id,
                            err,
                        )
                        continue

                    meeting_info = participant.get("meeting")
                    in_meeting_flag = meeting_info.get(
                        "in_meeting"
                    ) or meeting_info.get("inMeeting")

                    if in_meeting_flag:
                        return True

                continuation_token = getattr(paged, "continuation_token", None)
                if not continuation_token:
                    break
        except Exception as err:
            logger.debug("Failed to iterate meeting participants: %s", err)
            return None

        return False

    async def _handle_meeting_info(
        context: TurnContext, state: Optional[TurnState]
    ) -> None:
        meeting_context = _resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        if not meeting_id:
            await context.send_activity(
                "I couldn't find a meeting id in the channel data for this conversation."
            )
            return

        await _send_typing(context)

        meeting_info = None
        try:
            meeting_info = await TeamsInfo.get_meeting_info(context)
            logger.info("[teams note-taker] meeting info: %s", meeting_info)
        except Exception as err:
            logger.exception("Failed to fetch meeting details via connector")
            await context.send_activity(
                f"Could not retrieve meeting details: {getattr(err, 'message', str(err))}"
            )
            return

        details = getattr(meeting_info, "details", None) or {}
        organizer_obj = getattr(meeting_info, "organizer", None) or {}
        online_meeting_id = getattr(details, "ms_graph_resource_id", None)
        start_time = getattr(details, "scheduled_start_time", None)
        end_time = getattr(details, "scheduled_end_time", None)
        meeting_type = getattr(details, "type", None)
        organizer_id = getattr(organizer_obj, "id", None)
        organizer_aad = getattr(organizer_obj, "aadObjectId", None)

        try:
            member = await TeamsInfo.get_member(context, organizer_id)
            organizer_name = getattr(member, "name", None)
            organizer_email = getattr(member, "email", None) or getattr(
                member, "user_principal_name", None
            )
        except Exception:
            pass

        organizer = f"Organizer: {organizer_name} ({organizer_email}) [id: {organizer_id}, aadObjectId: {organizer_aad}]"

        try:
            in_progress = await _check_meeting_in_progress(context, meeting_id)
        except Exception as err:
            logger.debug("Meeting in-progress check failed: %s", err)
            in_progress = None

        status = (
            "yes (at least one participant found in meeting)"
            if in_progress is True
            else "no active participants found in meeting"
            if in_progress is False
            else "unknown (could not verify participants)"
        )

        lines = [
            "Meeting info:",
            f"- Type: {meeting_type}",
            f"- Meeting id: {meeting_id or 'Unknown'}",
            f"- Online meeting id: {online_meeting_id or 'Unknown'}",
            f"- {organizer}",
            f"- Start: {_format_iso_datetime(start_time)}",
            f"- End: {_format_iso_datetime(end_time)}",
            f"- In progress: {status}",
        ]

        await context.send_activity("\n".join(lines))

    @app.on_sign_in_success
    async def _on_sign_in_success(
        context: TurnContext,
        _state: TurnState,
        handler_id: str | None = None,
    ) -> None:
        logger.info(
            "Teams note-taker sign-in succeeded (handler=%s)",
            handler_id or auth_handler_id,
        )
        # await context.send_activity("Signed in successfully.")

    @app.on_sign_in_failure
    async def _on_sign_in_failure(
        context: TurnContext,
        _state: TurnState,
        handler_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        logger.warning(
            "Teams note-taker sign-in failed (handler=%s): %s",
            handler_id or auth_handler_id,
            error_message,
        )
        await context.send_activity("Sign-in failed.")

    @app.activity("installationUpdate")
    async def _on_installation_update(context: TurnContext, _state: TurnState) -> None:
        activity = getattr(context, "activity", None)
        logger.info("[teams note-taker] installation update received: %s", activity)
        action = getattr(activity, "action", None)
        if action == "add":
            await _upsert_teams_user_record(context)
            await _upsert_teams_meeting_record(context, is_bot_installed=True)
            await _handle_install_flow(context, _state)
            if _is_meeting_conversation(context):
                await context.send_activity("Magnet note taker added to the meeting.")
                await _ensure_organizer_delegated_token_cached(  # TODO: remove this?
                    context, auth_handler_id, prompt_on_missing=True
                )
        elif action == "remove":
            await _upsert_teams_meeting_record(context, is_bot_installed=False)

    @app.conversation_update("membersAdded")
    async def _on_members_added(context: TurnContext, _state: TurnState) -> None:
        activity = getattr(context, "activity", None)
        logger.info("[teams note-taker] members added received: %s", activity)
        members = getattr(activity, "members_added", None) or []
        bot_id = normalize_bot_id(
            getattr(getattr(activity, "recipient", None), "id", None)
        )
        bot_added = any(getattr(member, "id", None) == bot_id for member in members)
        if bot_added:
            await _upsert_teams_meeting_record(context, is_bot_installed=True)

    @app.conversation_update("membersRemoved")
    async def _on_members_removed(context: TurnContext, _state: TurnState) -> None:
        activity = getattr(context, "activity", None)
        logger.info("[teams note-taker] members removed received: %s", activity)
        members = getattr(activity, "members_removed", None) or []
        bot_id = normalize_bot_id(
            getattr(getattr(activity, "recipient", None), "id", None)
        )
        bot_removed = any(getattr(member, "id", None) == bot_id for member in members)
        if bot_removed:
            await _upsert_teams_meeting_record(context, is_bot_installed=False)

    @app.activity("message")
    async def _on_message(context: TurnContext, _state: TurnState) -> None:
        text = (getattr(getattr(context, "activity", None), "text", "") or "").strip()
        logger.info("[teams note-taker] message received: %s", text)

        await _upsert_teams_user_record(context)

        if not text:
            return

        normalized_text = text.lower()

        if normalized_text.startswith("/test-proactive-token"):  # TODO: remove this
            conv_ref = context.activity.get_conversation_reference()
            logger.info("[teams note-taker] conv_ref: %s", conv_ref)
            aad_object_id = context.activity.from_property.aad_object_id
            token = await _get_token_proactively(
                adapter=adapter,
                app=app,
                bot_app_id=bot_app_id,
                conv_ref=conv_ref,
                handler_id=auth_handler_id,
                aad_object_id=aad_object_id,
                tenant_id=bot_tenant_id,
            )

            await context.send_activity(
                "✅ token found" if token else "❌ no cached token"
            )
            return

        if normalized_text.startswith("/sign-in"):
            if _is_personal_teams_conversation(context):
                try:
                    already_signed_in = await _has_existing_token(
                        context, auth_handler_id
                    )
                except Exception:
                    already_signed_in = False

                if already_signed_in:
                    await context.send_activity(
                        "You're signed in. Use **/sign-out** to sign out."
                    )
                    return

                try:
                    await app.auth._start_or_continue_sign_in(
                        context, _state, auth_handler_id
                    )
                    # await context.send_activity("Sign-in card sent.")
                except Exception as err:
                    logger.exception("Failed to start sign-in: %s", err)
                    await context.send_activity(
                        f"Couldn't start sign-in: {getattr(err, 'message', str(err))}"
                    )
            else:
                await context.send_activity(
                    "Please use **/signin** in our 1:1 chat to authenticate."
                )
            return

        if _is_meeting_conversation(context):
            allowed = await _ensure_meeting_organizer_and_signed_in(
                context, auth_handler_id
            )
            if not allowed:
                return

        if normalized_text.startswith("/sign-out"):
            try:
                await app.auth.sign_out(context, auth_handler_id)
                await context.send_activity(
                    "You're signed out. Use **/sign-in** to sign in again."
                )
            except Exception as err:
                logger.exception("Failed to sign out: %s", err)
                await context.send_activity(
                    f"Couldn't sign you out right now: {getattr(err, 'message', str(err))}"
                )
            return

        if normalized_text.startswith("/whoami"):
            info = _resolve_user_info(context)
            has_existing_token = await _has_existing_token(context, auth_handler_id)
            lines = [
                "User info:",
                f"- Name: {info.get('name') or 'Unknown'}",
                f"- Id: {info.get('id') or 'n/a'}",
                f"- AAD object id: {info.get('aad_object_id') or 'n/a'}",
                f"- Conversation type: {info.get('conversation_type') or 'unknown'}",
                f"- Signed in: {'yes' if has_existing_token else 'no'}",
            ]
            await context.send_activity("\n".join(lines))
            return

        if normalized_text.startswith("/process-file"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /process-file link_to_file")
                return

            link = parts[1].strip()
            await _send_typing(context)
            await _handle_process_file(context, _state, link)
            return

        if normalized_text.startswith("/process-recording"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /process-recording RECORDING_ID")
                return

            rec_id = parts[1].strip()
            await _send_typing(context)
            await _handle_process_recording(context, _state, rec_id)
            return

        if normalized_text.startswith("/meeting-info"):
            await _send_typing(context)
            await _handle_meeting_info(context, _state)
            return

        if normalized_text.startswith("/recordings-find"):
            await _send_typing(context)
            await _handle_recordings_find(context, _state)
            return

        await context.send_activity("...not implemented yet...")

    @app.activity("event")
    async def _on_event(context: TurnContext, _state: TurnState) -> None:
        name = getattr(getattr(context, "activity", None), "name", None)
        normalized = str(name or "").lower()
        if normalized == "application/vnd.microsoft.meetingstart":
            logger.info("[teams note-taker] meeting start event received.")
            await _subscribe_to_recording_notifications(context)
        elif normalized == "application/vnd.microsoft.meetingend":
            logger.info("[teams note-taker] meeting end event received.")


def build_note_taker_runtime(settings: NoteTakerSettings) -> NoteTakerRuntime:
    auth_config = AgentAuthConfiguration(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        tenant_id=settings.tenant_id,
    )
    auth_config.AUTH_TYPE = AuthTypes.client_secret
    auth_config.SCOPES = SCOPE

    validation_config = AgentAuthConfiguration(
        client_id=settings.client_id,
        issuers=ISSUER,
    )

    token_provider = MsalAuth(auth_config)
    connections = StaticConnections(token_provider)
    adapter = CloudAdapter(
        channel_service_client_factory=RestChannelServiceClientFactory(connections)
    )
    adapter.use(_SignInInvokeMiddleware())

    async def _on_turn_error(context: TurnContext, error: Exception) -> None:
        message = getattr(error, "message", None) or str(error)
        if "BotNotInConversationRoster" in message:
            logger.warning(
                "[teams note-taker] bot not in roster yet; suppressing error send."
            )
            return
        logger.error("[teams note-taker] unhandled error: %s", message)
        try:
            await context.send_activity(
                f"The bot encountered an error or bug: {message}"
            )
        except Exception as send_err:
            logger.warning("[teams note-taker] on_turn_error send failed: %s", send_err)

    adapter.on_turn_error = _on_turn_error

    storage = MemoryStorage()
    auth_handler = AuthHandler(
        name=settings.auth_handler_id,
        abs_oauth_connection_name=settings.auth_handler_id,
        title="Sign in...",
        text="Sign in so I can read your meeting recordings.",
        scopes=NOTE_TAKER_GRAPH_SCOPES,
    )
    auth_handlers = {settings.auth_handler_id: auth_handler}

    authorization = Authorization(
        storage=storage,
        connection_manager=connections,
        auth_handlers=auth_handlers,
        auto_signin=False,  # avoid auto prompts
        use_cache=True,
    )
    app_options = ApplicationOptions(
        storage=storage,
        adapter=adapter,
        start_typing_timer=False,
        authorization_handlers=auth_handlers,
        bot_app_id=settings.client_id,
    )
    agent_app = AgentApplication[TurnState](
        options=app_options,
        connection_manager=connections,
        authorization=authorization,
    )

    _register_note_taker_handlers(
        agent_app,
        settings.auth_handler_id,
        adapter=adapter,
        bot_app_id=settings.client_id,
        bot_tenant_id=settings.tenant_id,
    )

    return NoteTakerRuntime(
        validation_config=validation_config,
        adapter=adapter,
        agent_app=agent_app,
        auth_handler_id=settings.auth_handler_id,
    )


def load_note_taker_runtime_from_env() -> NoteTakerRuntime | None:
    settings = NoteTakerSettings.from_env()
    if settings is None:
        return None

    try:
        runtime = build_note_taker_runtime(settings)
    except Exception:
        logger.exception(
            "Failed to initialize Teams note-taker runtime from environment variables."
        )
        return None

    logger.info(
        "Initialized Teams note-taker bot (client_id=%s, auth_handler_id=%s).",
        settings.client_id,
        settings.auth_handler_id,
    )
    return runtime


async def handle_recordings_ready_notifications(
    runtime: NoteTakerRuntime, payload: dict[str, Any]
) -> None:
    """Process Graph recordings-ready notifications and proactively transcribe the latest recording."""
    notifications = payload.get("value") or []
    if not isinstance(notifications, list):
        logger.debug(
            "[teams note-taker] recordings-ready payload malformed: %s", payload
        )
        return

    bot_app_id = (
        getattr(getattr(runtime, "agent_app", None), "bot_app_id", None)
        or getattr(getattr(runtime, "agent_app", None), "_bot_app_id", None)
        or getattr(getattr(runtime, "validation_config", None), "CLIENT_ID", None)
        or getattr(getattr(runtime, "validation_config", None), "client_id", None)
    )

    for notification in notifications:
        if not isinstance(notification, dict):
            continue
        subscription_id = notification.get("subscriptionId")
        if not subscription_id:
            continue

        meeting_row: TeamsMeeting | None = None
        resource_data = notification.get("resourceData") or {}
        chat_id_hint = unquote(str(resource_data.get("chatId") or "")) or None
        meeting_id_hint = _extract_meeting_id_from_notification(notification)
        organizer_aad = _extract_user_from_resource(notification)
        try:
            async with async_session_maker() as session:
                conditions = [TeamsMeeting.subscription_id == subscription_id]
                if chat_id_hint:
                    conditions.append(TeamsMeeting.chat_id == chat_id_hint)
                if meeting_id_hint:
                    conditions.append(
                        or_(
                            TeamsMeeting.graph_online_meeting_id == meeting_id_hint,
                            TeamsMeeting.meeting_id == meeting_id_hint,
                        )
                    )

                stmt = select(TeamsMeeting).where(or_(*conditions))
                result = await session.execute(stmt)
                meeting_row = result.scalars().first()

                if meeting_row is None:
                    logger.info(
                        "[teams note-taker] no meeting match (sub=%s, chat_hint=%s, meeting_hint=%s)",
                        subscription_id,
                        chat_id_hint,
                        meeting_id_hint,
                    )
        except Exception as err:
            logger.warning(
                "[teams note-taker] failed to load meeting for subscription %s: %s",
                subscription_id,
                getattr(err, "message", str(err)),
            )

        # TEMP? organizer fallback below (this should not be needed)

        if meeting_row is None and meeting_id_hint:
            meeting_row = SimpleNamespace(
                meeting_id=meeting_id_hint,
                graph_online_meeting_id=meeting_id_hint,
                title=None,
                subscription_conversation_reference=None,
            )
            logger.info(
                "[teams note-taker] proceeding without DB meeting row using meeting id hint %s",
                meeting_id_hint,
            )

        conv_ref_payload = (
            getattr(meeting_row, "subscription_conversation_reference", None)
            if meeting_row
            else None
        )
        if not conv_ref_payload and organizer_aad:
            try:
                conv_ref_payload = await _fetch_organizer_conversation_reference(
                    organizer_aad=organizer_aad, bot_app_id=bot_app_id
                )
                if not conv_ref_payload:
                    async with async_session_maker() as session:
                        conv_ref_payload = (
                            await _lookup_conversation_reference_by_user_hint(
                                session,
                                bot_app_id=bot_app_id,
                                user_hint=organizer_aad,
                            )
                        )
                if conv_ref_payload:
                    logger.info(
                        "[teams note-taker] using organizer conversation reference fallback for subscription %s, organizer_aad=%s, bot_app_id=%s",
                        subscription_id,
                        organizer_aad,
                        bot_app_id,
                    )
            except Exception as err:
                logger.debug(
                    "[teams note-taker] organizer conversation lookup failed: %s",
                    getattr(err, "message", str(err)),
                )

        if meeting_row is None or not conv_ref_payload:
            logger.info(
                "[teams note-taker] no usable conversation reference for subscription %s, organizer_aad=%s, bot_app_id=%s; skipping",
                subscription_id,
                organizer_aad,
                bot_app_id,
            )
            continue

        try:
            conv_payload = conv_ref_payload
            if isinstance(conv_payload, dict):
                conv_payload = dict(conv_payload)
                # Normalize common variants from stored references.
                if "agent" in conv_payload and "bot" not in conv_payload:
                    conv_payload["bot"] = conv_payload.get("agent")
                if "bot" in conv_payload and isinstance(conv_payload["bot"], dict):
                    conv_payload["bot"].setdefault("id", conv_payload["bot"].get("id"))
            if not isinstance(conv_payload, ConversationReference):
                conv_ref_obj = ConversationReference.model_validate(conv_payload)
            else:
                conv_ref_obj = conv_payload

            is_agentic_attr = getattr(conv_ref_obj, "is_agentic_request", None)
            if is_agentic_attr is None or not callable(is_agentic_attr):
                try:
                    setattr(conv_ref_obj, "is_agentic_request", lambda: False)
                except Exception:
                    pass
        except Exception as err:
            logger.warning(
                "[teams note-taker] invalid conversation reference for subscription %s: %s",
                subscription_id,
                getattr(err, "message", str(err)),
            )
            continue

        async def _callback(context: TurnContext):
            await _process_recording_notification_for_meeting(
                context=context,
                runtime=runtime,
                meeting_row=meeting_row,
                notification=notification,
            )

        try:
            continuation = Activity.create_event_activity()
            continuation.name = "recordingReadyNotification"
            normalized_ref = (
                ConversationReference.model_validate(conv_ref_obj)
                if not isinstance(conv_ref_obj, ConversationReference)
                else conv_ref_obj
            )
            continuation.apply_conversation_reference(normalized_ref, is_incoming=True)

            # ensure tenant id is present on continuation
            tenant_id = getattr(normalized_ref, "tenant_id", None) or getattr(
                getattr(normalized_ref, "conversation", None), "tenant_id", None
            )
            if tenant_id:
                continuation.channel_data = continuation.channel_data or {}
                continuation.channel_data.setdefault("tenant", {"id": tenant_id})
                conv_obj = getattr(continuation, "conversation", None)
                if conv_obj is not None and getattr(conv_obj, "tenant_id", None) in (
                    None,
                    "",
                ):
                    try:
                        conv_obj.tenant_id = tenant_id
                    except Exception:
                        pass

            await runtime.adapter.continue_conversation(
                bot_app_id,
                continuation,
                _callback,
            )
        except Exception as err:
            logger.warning(
                "[teams note-taker] continue_conversation failed for subscription %s: %s",
                subscription_id,
                getattr(err, "message", str(err)),
            )


async def _process_recording_notification_for_meeting(
    *,
    context: TurnContext,
    runtime: NoteTakerRuntime,
    meeting_row: TeamsMeeting,
    notification: dict[str, Any],
) -> None:
    await context.send_activity("Recording is ready. Fetching the latest recording...")

    handler_id = getattr(runtime, "auth_handler_id", None)
    if not handler_id:
        await context.send_activity("Auth handler is not configured for this bot.")
        return

    delegated_token: str | None = None
    try:
        handler = runtime.agent_app.auth._resolve_handler(handler_id)
        flow, _ = await handler._load_flow(context)
        token_response = await flow.get_user_token()
        delegated_token = getattr(token_response, "token", None)
    except Exception as err:
        logger.warning(
            "[teams note-taker] failed to get delegated token in webhook flow: %s",
            getattr(err, "message", str(err)),
        )

    if not delegated_token:
        await context.send_activity(
            "I need the meeting organizer to sign in (delegated token missing)."
        )
        return

    online_meeting_id = (
        meeting_row.graph_online_meeting_id
        or meeting_row.meeting_id
        or notification.get("resourceData", {}).get("meetingId")
    )
    if not online_meeting_id:
        await context.send_activity("Could not resolve the online meeting id.")
        return

    user_id_hint = _extract_user_from_resource(notification)

    recording_id = None
    try:
        recording_id = (notification.get("resourceData") or {}).get("id")
    except Exception:
        recording_id = None

    logger.info(
        "[teams note-taker] processing recording notification for meeting %s, user_id_hint=%s, recording_id=%s",
        online_meeting_id,
        user_id_hint,
        recording_id,
    )

    try:
        async with create_graph_client_with_token(delegated_token) as graph_client:
            if recording_id:
                base_path = (
                    f"/users/{quote(user_id_hint, safe='')}/onlineMeetings/{quote(online_meeting_id, safe='')}"
                    if user_id_hint
                    else None
                )
                logger.info(
                    "[teams note-taker] base_path=%s",
                    base_path,
                )
                recording = await get_recording_by_id(
                    client=graph_client,
                    online_meeting_id=online_meeting_id,
                    recording_id=recording_id,
                    base_path=base_path,
                )
                logger.info(
                    "[teams note-taker] recording=%s",
                    recording,
                )
                # if recording and not recording.get("contentUrl"):
                #    # Fallback to communications path if user-scoped call lacked contentUrl.
                #    recording = await get_recording_by_id(
                #        client=graph_client,
                #        online_meeting_id=online_meeting_id,
                #        recording_id=recording_id,
                #        base_path=f"/communications/onlineMeetings/{quote(online_meeting_id, safe='')}",
                #    )
                recordings = [recording] if recording else []
            else:  # TODO: remove this
                recordings = await get_meeting_recordings(
                    client=graph_client,
                    online_meeting_id=online_meeting_id,
                    add_size=True,
                    content_token=delegated_token,
                )
    except Exception as err:
        logger.exception(
            "[teams note-taker] failed to fetch recordings for meeting %s",
            online_meeting_id,
        )
        await context.send_activity(
            f"Could not retrieve meeting recordings: {getattr(err, 'message', str(err))}"
        )
        return

    if not recordings:
        await context.send_activity("No recordings found for this meeting.")
        return

    recording = recordings[0]
    # Normalize content URL field from Graph response
    if recording and not recording.get("contentUrl"):
        if recording.get("recordingContentUrl"):
            recording["contentUrl"] = recording.get("recordingContentUrl")
    meeting_info = {
        "id": meeting_row.meeting_id or meeting_row.graph_online_meeting_id,
        "title": meeting_row.title,
    }

    try:
        recording_bytes = await _download_recording_bytes(
            recording, delegated_token, meeting_info
        )
    except Exception as err:
        logger.exception("Failed to download recording during webhook processing")
        await context.send_activity(
            f"I couldn't download the recording: {getattr(err, 'message', str(err))}"
        )
        return

    if not recording_bytes:
        await context.send_activity("Recording did not include a downloadable URL.")
        return

    file_bytes, content_type, name, ext = recording_bytes
    await context.send_activity("Recording downloaded; starting transcription...")

    try:
        status, result = await _start_transcription_from_bytes(
            name=name,
            ext=ext,
            data=file_bytes,
            content_type=content_type,
            language=_DEFAULT_TRANSCRIPTION_LANGUAGE,
            pipeline_id=_DEFAULT_PIPELINE_ID,
        )
    except Exception as err:
        logger.exception("Failed to start transcription for webhook recording")
        await context.send_activity(
            f"I couldn't start transcription: {getattr(err, 'message', str(err))}"
        )
        return

    logger.info(
        "[teams note-taker] transcription result...: %s",
        result,
    )

    job_id = (result or {}).get("id") if isinstance(result, dict) else None
    transcription = (
        (result or {}).get("transcription") if isinstance(result, dict) else None
    )

    await _send_transcription_summary(
        context,
        status,
        job_id,
        transcription,
        conversation_date=_format_recording_date_iso(recording.get("createdDateTime")),
    )
