import asyncio
import mimetypes
import datetime as dt
import os
import base64
from pathlib import Path
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import httpx
from microsoft_agents.activity import Activity, ActionTypes, CardAction, OAuthCard
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

from .config import NOTE_TAKER_GRAPH_SCOPES, ISSUER, SCOPE
from .graph import (
    create_graph_client_with_token,
    get_meeting_recordings,
)
from .static_connections import StaticConnections
from speech_to_text.transcription import service as transcription_service
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


def _format_duration(seconds: int | None) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return "Unknown"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


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
    if not upload_url:
        presigned_urls = (session or {}).get("presigned_urls") or []
        upload_url = presigned_urls[0] if presigned_urls else None

    if not object_key:
        raise RuntimeError("Upload session did not return an object key.")

    logger.info("[teams note-taker] uploading bytes to object: %s", object_key)
    logger.info("[teams note-taker] upload_url: %s", upload_url)

    if not upload_url:
        raise RuntimeError("Upload session missing upload URL.")

    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        response = await client.put(
            upload_url,
            content=data,
            headers={"Content-Type": content_type},
        )
        response.raise_for_status()

    logger.info("[teams note-taker] uploaded bytes to object: %s", object_key)
    logger.info("[teams note-taker] starting transcription from object: %s", object_key)
    logger.info("[teams note-taker] pipeline_id: %s", pipeline_id)
    logger.info("[teams note-taker] language: %s", language)
    logger.info("[teams note-taker] ext: %s", ext_no_dot) 
    logger.info("[teams note-taker] content_type: %s", content_type) 

    job_id = await transcription_service.submit(
        name=name,
        ext=ext_no_dot,
        bytes_=None,
        object_key=object_key,
        content_type=content_type,
        backend=pipeline_id,
        language=language,
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
) -> None:
    if status in {"completed", "transcribed", "diarized"}:
        segs_count = 0
        preview = None
        full_text = None
        if isinstance(transcription, dict):
            segs = transcription.get("segments") or []
            segs_count = len(segs)
            full_text = transcription.get("text") or ""
            if not full_text and segs:
                full_text = " ".join(
                    (s.get("text") or "").strip() for s in segs if isinstance(s, dict)
                ).strip()
            if segs:
                first = segs[:3]
                preview = " ".join(
                    (s.get("text") or "").strip() for s in first if isinstance(s, dict)
                )
                preview = preview.strip() or None
        await context.send_activity(
            f"Transcription completed (job={job_id or 'n/a'}, segments={segs_count})."
        )
        if preview:
            await context.send_activity(f"Preview: {preview}")
        if full_text:
            snippet = full_text[:1000]
            suffix = "." if len(full_text) > len(snippet) else ""
            await context.send_activity(f"Transcript text: {snippet}{suffix}")
        elif segs_count == 0:
            await context.send_activity("No speech was detected in this recording.")
        return

    if status == "failed":
        err_msg = None
        if job_id:
            try:
                err_msg = await transcription_service.get_error(job_id)
            except Exception:
                err_msg = None
        await context.send_activity(
            f"Transcription failed for job {job_id or 'n/a'}: {err_msg or 'unknown error'}"
        )
        return

    await context.send_activity(
        f"Transcription incomplete (status={status}, job={job_id or 'n/a'})."
    )


async def _get_online_meeting_id(context: TurnContext) -> Optional[str]:
    meeting_info = await TeamsInfo.get_meeting_info(context)
    details = getattr(meeting_info, "details", None) or {}
    return getattr(details, "ms_graph_resource_id", None)


def _register_note_taker_handlers(
    app: AgentApplication[TurnState], auth_handler_id: str
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
            date_str, time_str = _format_recording_datetime(rec.get("createdDateTime"))
            size_str = _format_file_size(file_size)

            duration_str = _format_duration(duration) if duration is not None else None

            parts = [f"{idx}. 📅 {date_str} ⏰ {time_str}"]
            if duration_str:
                parts.append(f"⏱️ {duration_str}")
            parts.append(f"💾 {size_str}")

            lines.append("   ".join(parts))

        await context.send_activity("\n\n".join(lines))

    async def _transcribe_bytes_and_notify(
        context: TurnContext,
        *,
        name: str,
        ext: str,
        file_bytes: bytes,
        content_type: str,
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

        job_id = (result or {}).get("id") if isinstance(result, dict) else None
        transcription = (
            (result or {}).get("transcription") if isinstance(result, dict) else None
        )

        await _send_transcription_summary(context, status, job_id, transcription)

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

    async def _ensure_meeting_organizer_and_signed_in(
        context: TurnContext, handler_id: str
    ) -> bool:
        user = _resolve_user_info(context)
        try:
            meeting_info = await TeamsInfo.get_meeting_info(context)
            organizer_obj = getattr(meeting_info, "organizer", None) or {}
            organizer_id = getattr(organizer_obj, "id", None)
            organizer_aad = getattr(organizer_obj, "aadObjectId", None)
        except Exception as err:
            logger.warning(
                "Unable to verify meeting organizer: %s",
                getattr(err, "message", str(err)),
            )
            await context.send_activity(
                "I couldn't verify that you're the meeting organizer. Please try again or message me directly."
            )
            return False

        user_id = user.get("id")
        user_aad = user.get("aad_object_id")
        is_organizer = False
        if user_id and organizer_id and user_id == organizer_id:
            is_organizer = True
        if user_aad and organizer_aad and user_aad == organizer_aad:
            is_organizer = True

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
                )
            else:
                await context.send_activity(
                    "The first recording had no downloadable URL."
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

        lines = [
            "Meeting info:",
            f"- Type: {meeting_type}",
            f"- Meeting id: {meeting_id or 'Unknown'}",
            f"- Online meeting id: {online_meeting_id or 'Unknown'}",
            f"- {organizer}",
            f"- Start: {_format_iso_datetime(start_time)}",
            f"- End: {_format_iso_datetime(end_time)}",
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
            await _handle_install_flow(context, _state)
            if _is_meeting_conversation(context):
                await context.send_activity("Magnet note taker added to the meeting.")

    @app.conversation_update("membersAdded")
    async def _on_members_added(context: TurnContext, _state: TurnState) -> None:
        activity = getattr(context, "activity", None)
        logger.info("[teams note-taker] members added received: %s", activity)

    @app.activity("message")
    async def _on_message(context: TurnContext, _state: TurnState) -> None:
        text = (getattr(getattr(context, "activity", None), "text", "") or "").strip()
        logger.info("[teams note-taker] message received: %s", text)

        if not text:
            return

        normalized_text = text.lower()

        if normalized_text.startswith("/signin"):
            if _is_personal_teams_conversation(context):
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
                    "Please open a 1:1 chat with me and run /signin there to authenticate."
                )
            return

        if _is_meeting_conversation(context):
            allowed = await _ensure_meeting_organizer_and_signed_in(
                context, auth_handler_id
            )
            if not allowed:
                return

        if normalized_text.startswith("/signout"):
            try:
                await app.auth.sign_out(context, auth_handler_id)
                await context.send_activity("You're signed out.")
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
            await context.send_activity("The bot encountered an error or bug.")
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

    _register_note_taker_handlers(agent_app, settings.auth_handler_id)

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
