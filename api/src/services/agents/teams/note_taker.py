import os
import asyncio
import datetime as dt
from pathlib import Path
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from microsoft_agents.activity import Activity
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
from microsoft_agents.hosting.core.rest_channel_service_client_factory import (
    RestChannelServiceClientFactory,
)
from microsoft_agents.hosting.core.storage import MemoryStorage

from .config import ISSUER, SCOPE
from .graph import (
    create_graph_client_with_token,
    fetch_meeting_recordings,
)
from .static_connections import StaticConnections
from speech_to_text.transcription import service as transcription_service
from stores import get_db_client

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


def _is_personal_teams_conversation(context: TurnContext) -> bool:
    activity = getattr(context, "activity", None)
    conversation = getattr(activity, "conversation", None)
    conversation_type = getattr(conversation, "conversation_type", None)
    return conversation_type == "personal"


def _is_meeting_conversation(context: TurnContext) -> bool:
    activity = getattr(context, "activity", None)
    conversation = getattr(activity, "conversation", None)
    conversation_type = getattr(conversation, "conversation_type", None)
    return conversation_type == "meeting"


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
    channel_data = getattr(activity, "channel_data", None) or {}

    if not isinstance(channel_data, dict):
        channel_data = vars(channel_data) if hasattr(channel_data, "__dict__") else {}

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

    job_id = await transcription_service.submit(
        name=name,
        ext=ext.lstrip("."),
        bytes_=data,
        object_key=None,
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


def _register_note_taker_handlers(
    app: AgentApplication[TurnState], auth_handler_id: str
) -> None:
    async def _is_signed_in(context: TurnContext, handler_id: str) -> bool:
        try:
            token_response = await app.auth.get_token(context, handler_id)
        except Exception as err:
            logger.warning("Failed to get token: %s", getattr(err, "message", str(err)))
            return False

        token = getattr(token_response, "token", None) if token_response else None
        return bool(token)

    async def _get_delegated_token(
        context: TurnContext,
        handler_id: str,
        failure_message: str,
    ) -> str | None:
        try:
            token_response = await app.auth.get_token(context, handler_id)
            token_value = (
                getattr(token_response, "token", None) if token_response else None
            )

            if token_value:
                return token_value

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

        await context.send_activity(f"📹 Found {len(recordings)} recording(s):")

        lines = []
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

        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                recordings = await fetch_meeting_recordings(
                    client=graph_client,
                    join_url=meeting.get("joinUrl"),
                    chat_id=meeting.get("conversationId"),
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

                language = _DEFAULT_TRANSCRIPTION_LANGUAGE
                pipeline_id = _DEFAULT_PIPELINE_ID
                try:
                    status, result = await _start_transcription_from_bytes(
                        name=name,
                        ext=ext,
                        data=file_bytes,
                        content_type=content_type,
                        language=language,
                        pipeline_id=pipeline_id,
                    )
                except Exception as err:
                    logger.exception(
                        "Failed to start transcription for streamed recording"
                    )
                    await context.send_activity(
                        f"I couldn't start transcription: {getattr(err, 'message', str(err))}"
                    )
                    return

                job_id = (result or {}).get("id") if isinstance(result, dict) else None
                transcription = (
                    (result or {}).get("transcription")
                    if isinstance(result, dict)
                    else None
                )

                await _send_transcription_summary(
                    context, status, job_id, transcription
                )
            else:
                await context.send_activity(
                    "The first recording had no downloadable URL."
                )

    @app.on_sign_in_success
    async def _on_sign_in_success(
        context: TurnContext, _state: TurnState, handler_id: str | None
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
        handler_id: str | None,
        error_message: str | None,
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
        action = getattr(activity, "action", None)
        if action == "add":
            if _is_personal_teams_conversation(context):
                await context.send_activity(
                    "Thanks for installing the Magnet note taker bot."
                )
            elif _is_meeting_conversation(context):
                await context.send_activity("Magnet note taker added to the meeting.")

    @app.activity("message", auth_handlers=[auth_handler_id])
    async def _on_message(context: TurnContext, _state: TurnState) -> None:
        text = (getattr(getattr(context, "activity", None), "text", "") or "").strip()
        logger.info("[teams note-taker] message received: %s", text)

        if not text:
            return

        normalized_text = text.lower()

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
            signed_in = await _is_signed_in(context, auth_handler_id)
            await context.send_activity(
                (
                    f"You are {info.get('name') or 'Unknown user'} "
                    f"(id: {info.get('id') or 'n/a'}, aadObjectId: {info.get('aad_object_id') or 'n/a'}). "
                    f"Conversation type: {info.get('conversation_type') or 'unknown'}. "
                    f"Signed in: {'yes' if signed_in else 'no'}."
                )
            )
            return

        if normalized_text.startswith("/recordings-find"):
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
    adapter.use(_SignInInvokeMiddleware())  # TODO: fix oauth flow?

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
        title="Sign in",
        text="Sign in so I can read your meeting recordings.",
        scopes=SCOPE,
    )
    auth_handlers = {settings.auth_handler_id: auth_handler}

    authorization = Authorization(
        storage=storage,
        connection_manager=connections,
        auth_handlers=auth_handlers,
        auto_signin=True,
        use_cache=True,
    )
    app_options = ApplicationOptions(
        storage=storage,
        adapter=adapter,
        start_typing_timer=True,
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
