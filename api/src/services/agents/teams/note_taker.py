import asyncio
import mimetypes
import datetime as dt
import html as html_lib
import json
import os
import base64
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path
from dataclasses import dataclass
from logging import getLogger
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional
from urllib.parse import parse_qs, urlparse, unquote
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
from microsoft_agents.activity import (
    Activity,
    ActionTypes,
    Attachment,
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
from core.db.models.knowledge_graph import KnowledgeGraph
from core.db.models.teams import TeamsMeeting, TeamsUser
from core.db.models.teams.note_taker_settings import (
    NoteTakerSettings as NoteTakerSettingsModel,
)
from sqlalchemy import func, select, or_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from .config import NOTE_TAKER_GRAPH_SCOPES, ISSUER, SCOPE
from .graph import (
    create_recordings_ready_subscription,
    create_graph_client_with_token,
    get_recording_file_size,
    get_meeting_recordings,
    get_recording_by_id,
    list_subscriptions,
    pick_recordings_ready_subscription,
)
from .sf import account_lookup, post_stt_recording
from .static_connections import StaticConnections
from .teams_user_store import upsert_teams_user, normalize_bot_id
from speech_to_text.transcription import service as transcription_service
from services.prompt_templates import execute_prompt_template
from services.knowledge_graph.sources.api_ingest.api_ingest_source import (
    ApiIngestDataSource,
    run_background_ingest,
)
from services.observability import observe
from stores import get_db_client
from routes.admin.recordings import DEFAULT_PIPELINE
from utils import upload_handler

logger = getLogger(__name__)


_URL_RE = re.compile(r"(https?://[^\s<>\"]+)", re.IGNORECASE)


class _AnchorHrefExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def _extract_first_url(text: str) -> str | None:
    if not text:
        return None
    match = _URL_RE.search(text)
    if not match:
        return None
    url = (match.group(1) or "").strip()
    # Strip common trailing punctuation that comes from surrounding markup.
    url = url.rstrip(").,>\"'")
    return url if url.lower().startswith(("http://", "https://")) else None


def _extract_first_url_from_attachments(activity: Any) -> str | None:
    attachments = getattr(activity, "attachments", None) or []
    for attachment in attachments:
        content_url = getattr(attachment, "content_url", None)
        if isinstance(content_url, str):
            url = _extract_first_url(content_url)
            if url:
                return url

        content = getattr(attachment, "content", None)
        if isinstance(content, str) and content:
            try:
                parser = _AnchorHrefExtractor()
                parser.feed(content)
                for href in parser.hrefs:
                    url = _extract_first_url(html_lib.unescape(href).strip())
                    if url:
                        return url
            except Exception:
                # Best-effort parsing; ignore malformed HTML.
                pass
        elif isinstance(content, dict) and content:
            # Best-effort scan of dict values for URL strings.
            for value in content.values():
                if isinstance(value, str):
                    url = _extract_first_url(value)
                    if url:
                        return url

    return None


def _extract_process_file_link(context: TurnContext, text: str) -> str | None:
    # 1) Prefer explicit URL in the command arg (raw link pasting).
    candidate = ""
    parts = (text or "").strip().split(maxsplit=1)
    if parts and parts[0].lower() == "/process-file" and len(parts) > 1:
        candidate = parts[1].strip()

    url = _extract_first_url(candidate) or _extract_first_url(text or "")
    if url:
        return url

    # 2) Teams “formatted links” are often stored in HTML attachments.
    activity = getattr(context, "activity", None)
    return _extract_first_url_from_attachments(activity)


ENV_PREFIX = "TEAMS_NOTE_TAKER_"
_TRANSCRIPTION_TIMEOUT_SECONDS = 900
_TRANSCRIPTION_POLL_SECONDS = 5
_ORGANIZER_SIGN_IN_PROMPT = "I need you to sign in with /sign-in in our 1:1 chat so I can access meeting resources."
_ORGANIZER_PERSONAL_INSTALL_PROMPT = "Please install me."

_DEFAULT_NOTE_TAKER_SETTINGS: dict[str, Any] = {
    "subscription_recordings_ready": False,
    "create_knowledge_graph_embedding": False,
    "knowledge_graph_system_name": "",
    "integration": {
        "salesforce": {
            "send_transcript_to_salesforce": False,
            "salesforce_api_server": "",
            "salesforce_stt_recording_tool": "",
        }
    },
    "chapters": {"enabled": False, "prompt_template": ""},
    "summary": {"enabled": False, "prompt_template": ""},
    "insights": {"enabled": False, "prompt_template": ""},
}


def _merge_note_taker_settings(raw: dict[str, Any] | None) -> dict[str, Any]:
    settings = dict(_DEFAULT_NOTE_TAKER_SETTINGS)
    if not isinstance(raw, dict):
        return settings

    for key in (
        "subscription_recordings_ready",
        "create_knowledge_graph_embedding",
        "knowledge_graph_system_name",
        "integration",
    ):
        if key in raw:
            settings[key] = raw[key]

    for section in ("chapters", "summary", "insights"):
        base_section = dict(settings[section])
        section_raw = raw.get(section)
        if isinstance(section_raw, dict):
            for key in base_section.keys():
                if key in section_raw:
                    base_section[key] = section_raw[key]
        settings[section] = base_section

    return settings


async def _require_meeting_note_taker_settings_system_name(
    context: TurnContext, *, meeting_id: str
) -> str:
    _account_id, _account_name, settings_system_name = await _get_meeting_account_info(
        context, meeting_id
    )
    if not settings_system_name:
        raise ValueError(
            "No note taker config is set for this meeting (missing note_taker_settings_system_name on teams_meeting)."
        )
    return str(settings_system_name)


async def _load_note_taker_settings_by_system_name(
    system_name: str,
) -> dict[str, Any]:
    if not system_name:
        raise ValueError("Missing note taker settings system name.")

    async with async_session_maker() as session:
        stmt = select(NoteTakerSettingsModel.config).where(
            NoteTakerSettingsModel.system_name == system_name
        )
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

    if config is None:
        raise LookupError(
            f"Note taker settings record not found (system_name={system_name})."
        )

    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError:
            config = None

    return _merge_note_taker_settings(config if isinstance(config, dict) else None)


async def _load_note_taker_settings_for_context(context: TurnContext) -> dict[str, Any]:
    if not _is_meeting_conversation(context):
        raise ValueError("Note taker settings can only be loaded in a meeting context.")

    meeting = _resolve_meeting_details(context)
    logger.info("[teams note-taker] meeting: %s", meeting)
    meeting_id = meeting.get("id")
    if not meeting_id:
        raise ValueError("Could not resolve meeting id from Teams channel data.")

    settings_system_name = await _require_meeting_note_taker_settings_system_name(
        context, meeting_id=str(meeting_id)
    )
    return await _load_note_taker_settings_by_system_name(settings_system_name)


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


def _format_recording_date_compact(iso_datetime: str | None) -> str | None:
    if not iso_datetime:
        return None
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    except Exception:
        return None
    return dt_obj.strftime("%Y%m%d")


async def _get_meeting_account_info(
    context: TurnContext, meeting_id: str | None
) -> tuple[str | None, str | None, str | None]:
    if not meeting_id:
        return (None, None, None)

    recipient = getattr(getattr(context, "activity", None), "recipient", None)
    bot_id = normalize_bot_id(getattr(recipient, "id", None))
    if not bot_id:
        return (None, None, None)

    try:
        async with async_session_maker() as session:
            stmt = select(
                TeamsMeeting.account_id,
                TeamsMeeting.account_name,
                TeamsMeeting.note_taker_settings_system_name,
            ).where(
                TeamsMeeting.meeting_id == meeting_id, TeamsMeeting.bot_id == bot_id
            )
            result = await session.execute(stmt)
            row = result.one_or_none()
            if not row:
                return (None, None, None)
            return row[0], row[1], row[2]
    except Exception as err:
        logger.debug("Failed to load meeting account id: %s", err)
        return (None, None, None)


async def _get_meeting_account_id(
    context: TurnContext, meeting_id: str | None
) -> str | None:
    account_id, _account_name, _settings_system_name = await _get_meeting_account_info(
        context, meeting_id
    )
    return account_id


async def _send_stt_recording_to_salesforce(
    context: TurnContext,
    *,
    job_id: str | None,
    conversation_date: str | None,
    source_file_name: str,
    source_file_type: str,
    account_id: str | None,
    settings_system_name: str | None = None,
) -> None:
    if not job_id:
        return

    try:
        settings = (
            await _load_note_taker_settings_by_system_name(settings_system_name)
            if settings_system_name
            else await _load_note_taker_settings_for_context(context)
        )
    except Exception as err:
        logger.warning(
            "Salesforce sync skipped: failed to load note taker settings: %s",
            getattr(err, "message", str(err)),
        )
        return
    salesforce_settings = (settings.get("integration") or {}).get("salesforce") or {}
    if not salesforce_settings.get("send_transcript_to_salesforce"):
        await context.send_activity(
            "Salesforce sync skipped: sending transcripts to Salesforce is disabled in settings."
        )
        return

    if not account_id:
        await context.send_activity(
            "Salesforce sync skipped: account id is not set for this meeting."
        )
        return

    if not conversation_date:
        conversation_date = dt.datetime.now(dt.timezone.utc).date().isoformat()

    salesforce_api_server = salesforce_settings.get("salesforce_api_server") or None
    salesforce_stt_recording_tool = (
        salesforce_settings.get("salesforce_stt_recording_tool") or None
    )
    if not salesforce_api_server or not salesforce_stt_recording_tool:
        await context.send_activity(
            "Salesforce sync skipped: API server or STT recording tool is not configured in settings."
        )
        return

    payload = {
        "external_job_id": job_id,
        "conversation_date": conversation_date,
        "source_file_name": source_file_name,
        "source_file_type": source_file_type,
        "account_id": account_id,
    }

    payload_json = json.dumps(payload, indent=2, ensure_ascii=True)
    await _send_expandable_section(
        context,
        title="Salesforce payload sent.",
        content=payload_json,
        preserve_newlines=True,
    )

    try:
        result = await post_stt_recording(
            payload,
            server=salesforce_api_server,
            tool=salesforce_stt_recording_tool,
        )
    except Exception as err:
        logger.exception("Salesforce sttRecording failed for job %s", job_id)
        await _send_expandable_section(
            context,
            title="Salesforce response: failed.",
            content=getattr(err, "message", str(err)),
            preserve_newlines=True,
        )
        return

    if isinstance(result, (dict, list)):
        response_json = json.dumps(result, indent=2, ensure_ascii=True)
        await _send_expandable_section(
            context,
            title="Salesforce response: success.",
            content=response_json,
            preserve_newlines=True,
        )
        return

    await _send_expandable_section(
        context,
        title="Salesforce response: success.",
        content=str(result),
        preserve_newlines=True,
    )


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


async def _send_expandable_section(
    context: TurnContext,
    *,
    title: str,
    content: str,
    preserve_newlines: bool = False,
) -> None:
    details_block: dict[str, Any]
    if preserve_newlines:
        lines = [line for line in content.splitlines() if line.strip() != ""]
        if not lines:
            lines = [content]
        details_block = {
            "type": "Container",
            "id": "details",
            "isVisible": False,
            "items": [
                {
                    "type": "TextBlock",
                    "text": line,
                    "wrap": True,
                    "spacing": "Small",
                }
                for line in lines
            ],
        }
    else:
        details_block = {
            "type": "TextBlock",
            "id": "details",
            "text": content,
            "wrap": True,
            "isVisible": False,
            "spacing": "Small",
        }
    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            },
            details_block,
            {
                "type": "ActionSet",
                "id": "show-actions",
                "actions": [
                    {
                        "type": "Action.ToggleVisibility",
                        "title": "Show details",
                        "targetElements": [
                            "details",
                            "show-actions",
                            "hide-actions",
                        ],
                    }
                ],
            },
            {
                "type": "ActionSet",
                "id": "hide-actions",
                "isVisible": False,
                "actions": [
                    {
                        "type": "Action.ToggleVisibility",
                        "title": "🙈 Hide details",
                        "targetElements": [
                            "details",
                            "show-actions",
                            "hide-actions",
                        ],
                    }
                ],
            },
        ],
        "msteams": {"width": "Full"},
    }
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card,
    )
    activity = Activity(type="message", attachments=[attachment])
    await context.send_activity(activity)


async def _download_file_from_link(
    link: str, token: str | None, meeting: Dict[str, Any] | None = None
) -> tuple[str, dict[str, str], Callable[[str, str | None, str], tuple[str, str]]]:
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
    # TODO: before sending the token ensure it is teams.microsoft.com or sharepint.com
    if token:
        headers["Authorization"] = f"Bearer {token}"

    download_url = link
    # If it's a SharePoint/OneDrive URL, go via Graph /shares
    # TODO: include sharepoint-df.com and 1drv.ms
    if parsed.netloc.endswith("sharepoint.com") or "d.docs.live.net" in parsed.netloc:
        raw_url = link
        # base64url encode WITHOUT padding
        share_id = "u!" + base64.urlsafe_b64encode(raw_url.encode("utf-8")).decode(
            "ascii"
        ).rstrip("=")
        graph_download_url = (
            f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
        )
        download_url = graph_download_url

    def _name_resolver(
        content_type: str, content_disposition: str | None, final_url: str
    ) -> tuple[str, str]:
        filename = _parse_content_disposition_filename(content_disposition)
        if not filename:
            filename = _guess_filename_from_link(final_url or link)

        path = Path(filename)
        ext = path.suffix
        if not ext:
            guessed_ext = mimetypes.guess_extension(content_type) or ".bin"
            ext = guessed_ext

        meeting_part = _get_meeting_id_part(meeting)
        source_key = final_url or link
        item_hash = hashlib.sha1(source_key.encode("utf-8")).hexdigest()[:12]
        date_part = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
        final_name = _build_note_taker_filename(
            kind="file",
            meeting_id=meeting_part,
            item_id=item_hash,
            date_part=date_part,
            ext=ext,
        )
        return Path(final_name).stem, Path(final_name).suffix or ext

    return download_url, headers, _name_resolver


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
        index_elements=[TeamsMeeting.chat_id, TeamsMeeting.bot_id],
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
    meeting_part = _get_meeting_id_part(meeting) or "meeting"
    rec_part = recording.get("id") or recording.get("recordingId") or "recording"
    date_part = _format_recording_date_compact(recording.get("createdDateTime"))
    ext = Path(urlparse(content_url).path).suffix or ".mp4"
    return _build_note_taker_filename(
        kind="recording",
        meeting_id=meeting_part,
        item_id=rec_part,
        date_part=date_part,
        ext=ext,
    )


def _normalize_filename_part(value: str) -> str:
    ascii_value = value.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-")
    return cleaned or "item"


def _truncate_filename(base: str, ext: str, max_len: int = 255) -> str:
    ext = ext if ext.startswith(".") else f".{ext}" if ext else ""
    max_base_len = max_len - len(ext)
    if max_base_len <= 0:
        return ext[:max_len]
    if len(base) > max_base_len:
        base = base[:max_base_len].rstrip("-")
    return f"{base}{ext}"


def _build_note_taker_filename(
    *,
    kind: str,
    meeting_id: str | None,
    item_id: str | None,
    date_part: str | None,
    ext: str,
) -> str:
    parts = [
        "note-taker",
        kind,
        meeting_id or "meeting",
        item_id or "item",
        date_part or "",
    ]
    normalized = [_normalize_filename_part(part) for part in parts if part]
    base = "-".join(normalized)
    return _truncate_filename(base, ext)


def _get_meeting_id_part(meeting: Dict[str, Any] | None) -> str | None:
    if not meeting:
        return None
    return (
        meeting.get("id")
        or meeting.get("conversationId")
        or meeting.get("meetingId")
        or meeting.get("meeting_id")
        or meeting.get("chat_id")
    )


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
    meeting_part = _get_meeting_id_part(meeting) or "meeting"
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


def _parse_content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        length = int(value)
    except ValueError:
        return None
    return length if length > 0 else None


async def _probe_remote_file_metadata(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str],
) -> tuple[int | None, str | None, str | None, str]:
    """
    Best-effort probe for size/content headers without downloading the full file.
    Returns: (size_bytes, content_type, content_disposition, final_url)
    """
    # 1) HEAD (preferred if supported)
    try:
        head_resp = await client.head(url, headers=headers)
        if head_resp.status_code < 400:
            size = _parse_content_length(head_resp.headers.get("Content-Length"))
            content_type = head_resp.headers.get("Content-Type")
            content_disposition = head_resp.headers.get("Content-Disposition")
            final_url = str(head_resp.url) if head_resp.url else url
            return size, content_type, content_disposition, final_url
    except httpx.HTTPError:
        pass

    # 2) Range request to retrieve total size via Content-Range.
    range_headers = {**headers, "Range": "bytes=0-0"}
    try:
        async with client.stream("GET", url, headers=range_headers) as resp:
            if resp.status_code >= 400:
                resp.raise_for_status()
            content_range = resp.headers.get("Content-Range")
            total_size = None
            if content_range and "/" in content_range:
                raw_total = content_range.split("/")[-1]
                if raw_total.isdigit():
                    total_size = int(raw_total)
            size = total_size or _parse_content_length(
                resp.headers.get("Content-Length")
            )
            content_type = resp.headers.get("Content-Type")
            content_disposition = resp.headers.get("Content-Disposition")
            final_url = str(resp.url) if resp.url else url
            return size, content_type, content_disposition, final_url
    except httpx.HTTPError:
        pass

    return None, None, None, url


async def _upload_part(
    client: httpx.AsyncClient,
    url: str,
    data: bytes,
    headers: dict[str, str],
) -> str:
    part_headers = dict(headers)
    part_headers["Content-Length"] = str(len(data))
    response = await client.put(url, content=data, headers=part_headers)
    response.raise_for_status()
    etag = response.headers.get("ETag") or response.headers.get("etag") or ""
    return etag.strip('"')


async def _complete_multipart_upload(
    client: httpx.AsyncClient,
    complete_url: str,
    parts: list[dict[str, Any]],
) -> None:
    response = await client.post(complete_url, json={"parts": parts})
    response.raise_for_status()


async def _upload_stream_to_object(
    *,
    stream: AsyncIterator[bytes],
    size: int,
    content_type: str,
    filename: str,
) -> str:
    session = await upload_handler.make_multipart_session(
        filename=filename,
        size=size,
        content_type=content_type,
    )

    object_key = (session or {}).get("object_key")
    upload_url = (session or {}).get("upload_url") or (session or {}).get("url")
    upload_headers: dict[str, str] = (session or {}).get("upload_headers") or {}
    presigned_urls = (session or {}).get("presigned_urls") or []
    part_size_raw = (session or {}).get("part_size")
    try:
        part_size = int(part_size_raw) if part_size_raw else None
    except (TypeError, ValueError):
        part_size = None
    complete_url = (session or {}).get("complete_url")

    if not object_key:
        raise RuntimeError("Upload session did not return an object key.")

    logger.info("[teams note-taker] streaming upload to object: %s", object_key)

    timeout = httpx.Timeout(connect=30.0, read=600.0, write=600.0, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        use_multipart = False
        if presigned_urls:
            if len(presigned_urls) == 1 and not part_size and not complete_url:
                upload_url = upload_url or presigned_urls[0]
            else:
                use_multipart = True

        if use_multipart:
            if not part_size:
                raise RuntimeError("Multipart upload session missing part size.")
            if not complete_url:
                raise RuntimeError("Multipart upload session missing completion URL.")

            parts: list[dict[str, Any]] = []
            buffer = bytearray()
            part_index = 0

            async for chunk in stream:
                if not chunk:
                    continue
                buffer.extend(chunk)
                while len(buffer) >= part_size:
                    if part_index >= len(presigned_urls):
                        raise RuntimeError(
                            "Multipart upload session provided insufficient part URLs."
                        )
                    data = bytes(buffer[:part_size])
                    del buffer[:part_size]
                    etag = await _upload_part(
                        client, presigned_urls[part_index], data, upload_headers
                    )
                    parts.append({"part_number": part_index + 1, "etag": etag})
                    part_index += 1

            if buffer:
                if part_index >= len(presigned_urls):
                    raise RuntimeError(
                        "Multipart upload session provided insufficient part URLs."
                    )
                etag = await _upload_part(
                    client, presigned_urls[part_index], bytes(buffer), upload_headers
                )
                parts.append({"part_number": part_index + 1, "etag": etag})
                part_index += 1

            if part_index != len(presigned_urls):
                raise RuntimeError(
                    "Multipart upload session returned unexpected part URLs."
                )

            await _complete_multipart_upload(client, complete_url, parts)
            return object_key

        if not upload_url:
            raise RuntimeError("Upload session missing upload URL.")

        upload_headers = {
            "Content-Type": content_type,
            "Content-Length": str(size),
            **upload_headers,
        }

        response = await client.put(upload_url, content=stream, headers=upload_headers)
        response.raise_for_status()

    return object_key


async def _start_transcription_from_object_key(
    *,
    name: str,
    ext: str,
    object_key: str,
    content_type: str,
    pipeline_id: str,
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


async def _send_typing(context: TurnContext) -> None:
    try:
        await context.send_activity(Activity(type="typing"))
    except Exception as err:
        logger.debug(
            "Failed to send typing indicator: %s",
            getattr(err, "message", str(err)),
        )


async def _transcribe_stream_and_notify(
    context: TurnContext,
    *,
    download_url: str,
    headers: dict[str, str],
    name_resolver: Callable[[str, str | None, str], tuple[str, str]],
    conversation_date: str | None = None,
    known_size: int | None = None,
    settings_system_name: str | None = None,
    on_submit: Callable[[str], Awaitable[None]] | None = None,
    on_submit_factory: Callable[
        [str, str, str], Awaitable[Callable[[str], Awaitable[None]] | None]
    ]
    | None = None,
) -> None:
    await _send_typing(context)
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

            if on_submit is None and on_submit_factory is not None:
                on_submit = await on_submit_factory(name, ext, content_type)

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
            pipeline_id=DEFAULT_PIPELINE,
            on_submit=on_submit,
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
        settings_system_name=settings_system_name,
    )


async def _send_transcription_summary(
    context: TurnContext,
    status: str,
    job_id: str | None,
    transcription: dict | None,
    conversation_date: str | None = None,
    settings_system_name: str | None = None,
) -> None:
    duration = None
    transcript_payload = transcription
    if isinstance(transcription, dict):
        duration = transcription.get("duration")
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
            max_chars = 4000
            snippet = full_text[:max_chars]
            suffix = "..." if len(full_text) > len(snippet) else ""
            await _send_expandable_section(
                context,
                title="Transcript",
                content=f"{snippet}{suffix}",
                preserve_newlines=True,
            )
        elif segs_count == 0:
            await context.send_activity("No speech was detected in this recording.")

        if full_text:
            try:
                settings = (
                    await _load_note_taker_settings_by_system_name(settings_system_name)
                    if settings_system_name
                    else await _load_note_taker_settings_for_context(context)
                )
            except Exception as err:
                logger.warning(
                    "Skipping summaries/embedding: cannot load note taker settings: %s",
                    getattr(err, "message", str(err)),
                )
                return

            templates: list[tuple[str, str, str]] = []
            for key, title in (
                ("summary", "Summary"),
                ("chapters", "Chapters"),
                ("insights", "Insights"),
            ):
                section = settings.get(key) if isinstance(settings, dict) else None
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
                participants=participants,
                conversation_date=conversation_date,
            )

            knowledge_graph_sections: dict[str, str] = {}
            for (system_name, title, key), result in zip(templates, results):
                if isinstance(result, Exception):
                    logger.warning(
                        "Prompt template %s failed for transcription job %s: %s",
                        system_name,
                        job_id,
                        getattr(result, "message", str(result)),
                    )
                    await context.send_activity(f"{title} generation failed.")
                    continue

                content = getattr(result, "content", None)
                if content is None:
                    content = str(result)
                knowledge_graph_sections[key] = str(content)
                await _send_expandable_section(
                    context,
                    title=f"Meeting {title.lower()}",
                    content=str(content),
                )
            knowledge_graph_name = settings.get("knowledge_graph_system_name")
            if (
                settings.get("create_knowledge_graph_embedding")
                and knowledge_graph_name
            ):
                ingested = await _ingest_knowledge_graph_sections(
                    graph_system_name=knowledge_graph_name,
                    meeting=_resolve_meeting_details(context),
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
    """
    Execute prompt templates for a transcription.

    Returns a list aligned with `template_system_names`. Each item is either the
    template execution result or an Exception (when `return_exceptions=True`).
    """

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

    def _build_note_taker_welcome_card(bot_name: str | None) -> dict:
        commands = [
            "**/welcome** - Show this help.",
            "**/sign-in** - Sign in to allow access to meeting recordings (1:1 chat).",
            "**/sign-out** - Sign out and revoke access.",
            "**/whoami** - (to be removed) Show your Teams identity and sign-in status.",
            "**/config-list** - List available note taker configs.",
            "**/config-set CONFIG_SYSTEM_NAME** - Assign a note taker config to this meeting.",
            "**/sf-account-lookup (to be removed) ACCOUNT_NAME** - Lookup a Salesforce account.",
            "**/sf-account-set ACCOUNT_NAME** - Set the Salesforce account for this meeting.",
            "**/recordings-list** - List meeting recordings.",
            "**/recordings-find** - (to be removed) List meeting recordings and transcribe the latest.",
            "**/process-transcript-job TRANSCRIPTION_JOB_ID** - Process an existing transcription job.",
            "**/process-recording RECORDING_ID** - Download and transcribe a specific recording.",
            "**/process-file LINK** - (to be removed) Download and transcribe an audio/video file.",
            "**/meeting-info** - Show current meeting details.",
            "**/test-proactive-token** - (to be removed) Check for a cached delegated token.",
        ]

        body = [
            {
                "type": "TextBlock",
                "text": "Welcome to Magnet note taker",
                "weight": "Bolder",
                "size": "Large",
            },
        ]
        if bot_name:
            body.append(
                {
                    "type": "TextBlock",
                    "text": f"I am your {bot_name}.",
                    "wrap": True,
                    "spacing": "Small",
                }
            )
        body.extend(
            [
                {
                    "type": "TextBlock",
                    "text": (
                        "I capture meeting recordings and generate transcripts, summaries, chapters, and insights."
                    ),
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": "Commands",
                    "weight": "Bolder",
                    "spacing": "Medium",
                },
            ]
        )
        for command in commands:
            body.append(
                {
                    "type": "TextBlock",
                    "text": f"- {command}",
                    "wrap": True,
                    "spacing": "Small",
                }
            )

        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": body,
            "msteams": {"width": "Full"},
        }

    async def _send_welcome_card(context: TurnContext) -> None:
        bot_name = getattr(
            getattr(getattr(context, "activity", None), "recipient", None),
            "name",
            None,
        )
        card = _build_note_taker_welcome_card(bot_name)
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        activity = Activity(type="message", attachments=[attachment])
        await context.send_activity(activity)

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

    async def _build_salesforce_submit_callback(
        context: TurnContext,
        *,
        conversation_date: str | None,
        source_file_name: str,
        source_file_type: str,
    ) -> Callable[[str], Awaitable[None]] | None:
        if not _is_meeting_conversation(context):
            return None

        meeting_context = _resolve_meeting_details(context)
        account_id = await _get_meeting_account_id(context, meeting_context.get("id"))

        async def _notify_salesforce(submit_job_id: str) -> None:
            await _send_stt_recording_to_salesforce(
                context,
                job_id=submit_job_id,
                conversation_date=conversation_date,
                source_file_name=source_file_name,
                source_file_type=source_file_type,
                account_id=account_id,
            )

        return _notify_salesforce

    async def _transcribe_stream_and_notify(
        context: TurnContext,
        *,
        download_url: str,
        headers: dict[str, str],
        name_resolver: Callable[[str, str | None, str], tuple[str, str]],
        conversation_date: str | None = None,
        known_size: int | None = None,
        on_submit: Callable[[str], Awaitable[None]] | None = None,
        on_submit_factory: Callable[
            [str, str, str], Awaitable[Callable[[str], Awaitable[None]] | None]
        ]
        | None = None,
    ) -> None:
        await _send_typing(context)
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
                content_disposition = response.headers.get("Content-Disposition")
                if not content_disposition:
                    content_disposition = probed_disposition
                if not final_url and probed_final_url:
                    final_url = probed_final_url
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

                if on_submit is None:
                    if on_submit_factory is not None:
                        on_submit = await on_submit_factory(name, ext, content_type)
                    else:
                        on_submit = await _build_salesforce_submit_callback(
                            context,
                            conversation_date=conversation_date,
                            source_file_name=f"{name}{ext}",
                            source_file_type=content_type,
                        )

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
                pipeline_id=DEFAULT_PIPELINE,
                on_submit=on_submit,
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

    async def _process_transcription_job_and_notify(
        context: TurnContext,
        *,
        job_id: str,
        conversation_date: str | None = None,
    ) -> None:
        await _send_typing(context)
        meeting = _resolve_meeting_details(context)
        meeting_part = _get_meeting_id_part(meeting)
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
        on_submit = await _build_salesforce_submit_callback(
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
            status or "unknown",
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
        context: TurnContext,
        *,
        organizer_id: str | None,
        organizer_aad: str | None,
        prompt_text: str,
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
            text=f"{mention_text} {prompt_text}",
            text_format=TextFormatTypes.xml,
            entities=[mention],
        )

    async def _send_organizer_sign_in_prompt(
        context: TurnContext, *, organizer_id: str | None, organizer_aad: str | None
    ) -> None:
        activity = await _build_organizer_mention_activity(
            context,
            organizer_id=organizer_id,
            organizer_aad=organizer_aad,
            prompt_text=_ORGANIZER_SIGN_IN_PROMPT,
        )
        if activity:
            await context.send_activity(activity)
            return
        await context.send_activity(_ORGANIZER_SIGN_IN_PROMPT)

    async def _send_organizer_personal_install_prompt(
        context: TurnContext, *, organizer_id: str | None, organizer_aad: str | None
    ) -> None:
        activity = await _build_organizer_mention_activity(
            context,
            organizer_id=organizer_id,
            organizer_aad=organizer_aad,
            prompt_text=_ORGANIZER_PERSONAL_INSTALL_PROMPT,
        )
        if activity:
            await context.send_activity(activity)
            return
        await context.send_activity(_ORGANIZER_PERSONAL_INSTALL_PROMPT)

    async def _organizer_has_personal_scope_installation(
        *, organizer_id: str | None, organizer_aad: str | None, bot_id: str | None
    ) -> bool:
        if not bot_id or (not organizer_id and not organizer_aad):
            return False
        stmt = (
            select(TeamsUser)
            .where(TeamsUser.scope == "personal", TeamsUser.bot_id == bot_id)
            .where(
                or_(
                    TeamsUser.aad_object_id == organizer_aad,
                    TeamsUser.teams_user_id == organizer_id,
                )
            )
            .limit(1)
        )
        try:
            async with async_session_maker() as session:
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
        except Exception as exc:
            logger.debug(
                "Failed to check organizer personal install state: %s",
                getattr(exc, "message", str(exc)),
            )
            return False

    async def _prompt_organizer_personal_install_if_missing(
        context: TurnContext,
    ) -> None:
        if not _is_meeting_conversation(context):
            return
        try:
            organizer = await _get_meeting_organizer_identity(context)
        except Exception as err:
            logger.debug(
                "Unable to resolve meeting organizer for personal install prompt: %s",
                getattr(err, "message", str(err)),
            )
            return

        organizer_id = organizer.get("id")
        organizer_aad = organizer.get("aad_object_id")
        bot_id = normalize_bot_id(
            getattr(
                getattr(getattr(context, "activity", None), "recipient", None),
                "id",
                None,
            )
        )
        if await _organizer_has_personal_scope_installation(
            organizer_id=organizer_id,
            organizer_aad=organizer_aad,
            bot_id=bot_id,
        ):
            return
        await _send_organizer_personal_install_prompt(
            context, organizer_id=organizer_id, organizer_aad=organizer_aad
        )

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

        await _send_welcome_card(context)

        try:
            already_signed_in = await _has_existing_token(context, auth_handler_id)
        except Exception:
            already_signed_in = False

        if already_signed_in:
            return

        await context.send_activity(
            "Thanks for installing me. Please sign in so I can access your meeting recordings."
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

        await _handle_recordings_list(
            context,
            state,
            recordings=recordings,
            meeting=meeting,
            delegated_token=delegated_token,
            transcribe_latest=True,
        )

    async def _handle_recordings_list(
        context: TurnContext,
        state: Optional[TurnState],
        recordings: list | None = None,
        meeting: dict[str, Any] | None = None,
        delegated_token: str | None = None,
        transcribe_latest: bool = False,
    ) -> None:
        meeting = meeting or _resolve_meeting_details(context)
        if recordings is None:
            if not (meeting.get("id") or meeting.get("conversationId")):
                logger.warning("No meeting id found for recordings-list command.")
                return

            await _send_typing(context)

            try:
                online_meeting_id = await _get_online_meeting_id(context)
                if not online_meeting_id:
                    await context.send_activity(
                        "No online meeting id found for this meeting."
                    )
                    return

                if not delegated_token:
                    delegated_token = await _get_delegated_token(
                        context,
                        auth_handler_id,
                        "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
                    )
                    if not delegated_token:
                        return

                async with create_graph_client_with_token(
                    delegated_token
                ) as graph_client:
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

        if not delegated_token:
            delegated_token = await _get_delegated_token(
                context,
                auth_handler_id,
                "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
            )
            if not delegated_token:
                return

        await _send_recordings_summary(context, recordings, delegated_token)
        if transcribe_latest and recordings:
            await context.send_activity("Streaming the latest recording now...")
            await _send_typing(context)
            content_url = recordings[0].get("contentUrl") or recordings[0].get(
                "recordingContentUrl"
            )
            if not content_url:
                await context.send_activity(
                    "The first recording had no downloadable URL."
                )
                return

            filename = _build_recording_filename(meeting, recordings[0], content_url)
            name = Path(filename).stem
            ext = Path(filename).suffix

            await context.send_activity("Streaming the recording for transcription...")
            await _send_typing(context)

            headers = {"Authorization": f"Bearer {delegated_token}"}

            await _transcribe_stream_and_notify(
                context,
                download_url=content_url,
                headers=headers,
                name_resolver=lambda *_: (name, ext),
                known_size=recordings[0].get("size")
                or await get_recording_file_size(content_url, delegated_token),
                conversation_date=_format_recording_date_iso(
                    recordings[0].get("createdDateTime")
                ),
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

        content_url = recording.get("contentUrl")
        if not content_url:
            await context.send_activity("Recording did not include a downloadable URL.")
            return

        filename = _build_recording_filename(meeting, recording, content_url)
        name = Path(filename).stem
        ext = Path(filename).suffix

        await context.send_activity("Streaming the recording for transcription...")
        await _send_typing(context)

        headers = {"Authorization": f"Bearer {delegated_token}"}

        await _transcribe_stream_and_notify(
            context,
            download_url=content_url,
            headers=headers,
            name_resolver=lambda *_: (name, ext),
            known_size=recording.get("size")
            or await get_recording_file_size(content_url, delegated_token),
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

        meeting = _resolve_meeting_details(context)
        try:
            download_url, headers, name_resolver = await _download_file_from_link(
                link, delegated_token, meeting=meeting
            )
        except Exception as err:
            logger.exception("Failed to resolve file download link")
            await context.send_activity(
                f"I couldn't resolve that link: {getattr(err, 'message', str(err))}"
            )
            return

        await context.send_activity("Streaming the file for transcription...")

        await _transcribe_stream_and_notify(
            context,
            download_url=download_url,
            headers=headers,
            name_resolver=name_resolver,
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
            #   "(TEMPORARY) I completed getting your delegated token."
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
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))

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

        lifecycle_webhook = _resolve_recordings_lifecycle_webhook_url()

        subscription_id = None
        expiration_dt: dt.datetime | None = None
        try:
            payload = await create_recordings_ready_subscription(
                token=delegated_token,
                online_meeting_id=online_meeting_id,
                notification_url=webhook_url,
                lifecycle_notification_url=lifecycle_webhook,
                expiration=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=4),
            )
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
            error_message = getattr(err, "message", str(err))
            if isinstance(err, httpx.HTTPStatusError):
                try:
                    body = err.response.json() if err.response is not None else {}
                except Exception:
                    body = {}
                if isinstance(body, dict):
                    reason = (
                        body.get("error", {}).get("message")
                        if isinstance(body, dict)
                        else None
                    )
                    if reason:
                        error_message = f"{error_message} (reason: {reason})"
            try:
                async with async_session_maker() as session:
                    try:
                        await session.execute(
                            pg_insert(TeamsMeeting)
                            .values(
                                chat_id=chat_id,
                                bot_id=bot_id,
                                graph_online_meeting_id=online_meeting_id,
                                subscription_last_error=getattr(
                                    err, "message", str(err)
                                ),
                                last_seen_at=dt.datetime.now(dt.timezone.utc),
                            )
                            .on_conflict_do_update(
                                index_elements=[
                                    TeamsMeeting.chat_id,
                                    TeamsMeeting.bot_id,
                                ],
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
            await context.send_activity(
                f"Recording subscription failed: {error_message}"
            )
            return

        if not chat_id or not subscription_id:
            await context.send_activity(
                "Recording subscription not set (missing chat or subscription id)."
            )
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
                        bot_id=bot_id,
                        graph_online_meeting_id=online_meeting_id,
                        subscription_id=subscription_id,
                        subscription_expires_at=expiration_dt,
                        subscription_is_active=True,
                        subscription_last_error=None,
                        subscription_conversation_reference=conv_ref,
                        last_seen_at=now,
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[TeamsMeeting.chat_id, TeamsMeeting.bot_id],
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
            return

        duration_note = "unknown"
        if expiration_dt:
            remaining_seconds = max(
                0.0, (expiration_dt - now).total_seconds() if now else 0.0
            )
            duration_note = _format_duration(remaining_seconds)

        await context.send_activity(
            f"Recording subscription set (id={subscription_id}, duration={duration_note})."
        )

    async def _get_recordings_ready_subscription_status(
        context: TurnContext, online_meeting_id: str | None
    ) -> str:
        if not online_meeting_id:
            return "unknown (missing online meeting id)"

        delegated_token = await _get_organizer_delegated_token_from_cache(context)
        if not delegated_token:
            return "unknown (organizer delegated token missing)"

        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                subscriptions = await list_subscriptions(graph_client)
            subscription = pick_recordings_ready_subscription(
                subscriptions, online_meeting_id=online_meeting_id
            )
        except Exception as err:
            logger.warning(
                "[teams note-taker] failed to query recording subscriptions: %s",
                getattr(err, "message", str(err)),
            )
            return "unknown (graph query failed)"

        if not subscription:
            return "not found"

        exp_raw = subscription.get("expirationDateTime")
        exp_label = _format_iso_datetime(exp_raw)

        try:
            exp_dt = dt.datetime.fromisoformat(exp_raw.replace("Z", "+00:00"))
        except Exception:
            exp_dt = None

        subscription_id = subscription.get("id")
        id_note = f"id={subscription_id}, " if subscription_id else ""

        if exp_dt and exp_dt <= dt.datetime.now(dt.timezone.utc):
            return f"expired ({id_note}at {exp_label})"

        return f"set ({id_note}expires {exp_label})"

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

    async def _handle_sf_account_lookup(
        context: TurnContext, account_name: str
    ) -> None:
        if not account_name:
            await context.send_activity("Usage: /sf-account-lookup ACCOUNT_NAME")
            return

        await _send_typing(context)

        try:
            settings = await _load_note_taker_settings_for_context(context)
            salesforce_settings = (settings.get("integration") or {}).get(
                "salesforce"
            ) or {}
            salesforce_api_server = (
                salesforce_settings.get("salesforce_api_server") or None
            )
            result = await account_lookup(
                account_name,
                server=salesforce_api_server,
            )
        except Exception as err:
            logger.exception(
                "Salesforce account lookup failed for %s",
                account_name,
            )
            await context.send_activity(
                f"Salesforce account lookup failed: {getattr(err, 'message', str(err))}"
            )
            return

        if isinstance(result, list):
            count = len(result)
            first_account_id = None
            first_account_name = None
            if result and isinstance(result[0], dict):
                first_account_id = result[0].get("accountId")
                first_account_name = (
                    result[0].get("accountName")
                    or result[0].get("name")
                    or result[0].get("Name")
                )
            lines = [
                f"Results: {count}",
                f"First accountId: {first_account_id or 'n/a'}",
                f"First accountName: {first_account_name or 'n/a'}",
            ]
            await context.send_activity("\n".join(lines))
            return

        if isinstance(result, dict):
            payload = json.dumps(result, indent=2, ensure_ascii=True)
            await context.send_activity(f"```json\n{payload}\n```")
            return

        await context.send_activity(str(result))

    async def _handle_sf_account_set(context: TurnContext, account_name: str) -> None:
        if not account_name:
            await context.send_activity("Usage: /sf-account-set ACCOUNT_NAME")
            return

        if not _is_meeting_conversation(context):
            await context.send_activity("This command works only in meeting chats.")
            return

        await _send_typing(context)

        try:
            settings = await _load_note_taker_settings_for_context(context)
            salesforce_settings = (settings.get("integration") or {}).get(
                "salesforce"
            ) or {}
            salesforce_api_server = (
                salesforce_settings.get("salesforce_api_server") or None
            )
            result = await account_lookup(
                account_name,
                server=salesforce_api_server,
            )
        except Exception as err:
            logger.exception(
                "Salesforce account lookup failed for %s",
                account_name,
            )
            await context.send_activity(
                f"Salesforce account lookup failed: {getattr(err, 'message', str(err))}"
            )
            return

        if not isinstance(result, list) or not result:
            await context.send_activity("No Salesforce accounts found to set.")
            return

        first = result[0] if isinstance(result[0], dict) else {}
        account_id = first.get("accountId") if isinstance(first, dict) else None
        account_name_value = None
        if isinstance(first, dict):
            account_name_value = (
                first.get("accountName") or first.get("name") or first.get("Name")
            )
        if not account_name_value:
            account_name_value = account_name
        if not account_id:
            await context.send_activity(
                "Salesforce account lookup did not return an accountId."
            )
            return

        meeting_context = _resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not meeting_id or not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve meeting, chat, or bot id for this conversation."
            )
            return

        now = dt.datetime.now(dt.timezone.utc)
        stmt = (
            update(TeamsMeeting)
            .where(
                TeamsMeeting.chat_id == chat_id,
                TeamsMeeting.bot_id == bot_id,
            )
            .values(
                account_id=account_id,
                account_name=account_name_value,
                last_seen_at=now,
                updated_at=func.now(),
            )
        )

        try:
            async with async_session_maker() as session:
                try:
                    result = await session.execute(stmt)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        except Exception as err:
            logger.exception(
                "Failed to update Teams meeting for account set (meeting_id=%s, bot_id=%s)",
                meeting_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save account for this meeting: {getattr(err, 'message', str(err))}"
            )
            return

        if getattr(result, "rowcount", 0) == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return

        account_label = account_name_value or "Unknown"
        await context.send_activity(
            f"Saved Salesforce account {account_label} (id {account_id}) for this meeting."
        )

    async def _handle_note_taker_config_list(context: TurnContext) -> None:
        """List available note taker configs stored in DB."""
        await _send_typing(context)

        try:
            async with async_session_maker() as session:
                stmt = select(
                    NoteTakerSettingsModel.id,
                    NoteTakerSettingsModel.name,
                    NoteTakerSettingsModel.system_name,
                    NoteTakerSettingsModel.description,
                ).order_by(NoteTakerSettingsModel.created_at.asc())
                result = await session.execute(stmt)
                rows = result.all()
        except Exception as err:
            logger.exception("Failed to list note taker configs")
            await context.send_activity(
                f"Failed to list note taker configs: {getattr(err, 'message', str(err))}"
            )
            return

        if not rows:
            await context.send_activity(
                "No note taker configs found. Create one in the admin UI first."
            )
            return

        lines = ["Available note taker configs:"]
        for row in rows[:30]:
            config_id, name, system_name, description = row
            label = name or system_name or str(config_id)
            desc_part = f" — {description}" if description else ""
            lines.append(
                f"- {label}{desc_part} (system_name: {system_name}, id: {config_id})"
            )

        if len(rows) > 30:
            lines.append(f"...and {len(rows) - 30} more")
        lines.append("Use: /config-set CONFIG_SYSTEM_NAME (in a meeting chat)")
        await context.send_activity("\n".join(lines))

    async def _handle_note_taker_config_set(
        context: TurnContext, config_system_name: str
    ) -> None:
        if not config_system_name:
            await context.send_activity("Usage: /config-set CONFIG_SYSTEM_NAME")
            return

        if not _is_meeting_conversation(context):
            await context.send_activity("This command works only in meeting chats.")
            return

        await _send_typing(context)

        try:
            async with async_session_maker() as session:
                stmt = select(NoteTakerSettingsModel).where(
                    NoteTakerSettingsModel.system_name == config_system_name
                )
                config_row = (await session.execute(stmt)).scalars().first()
        except Exception as err:
            logger.exception(
                "Failed to resolve note taker config %s", config_system_name
            )
            await context.send_activity(
                f"Failed to resolve note taker config: {getattr(err, 'message', str(err))}"
            )
            return

        if config_row is None:
            await context.send_activity(
                "Note taker config not found. Run /config-list to see available configs."
            )
            return

        meeting_context = _resolve_meeting_details(context)
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve chat or bot id for this conversation."
            )
            return

        now = dt.datetime.now(dt.timezone.utc)
        stmt = (
            update(TeamsMeeting)
            .where(
                TeamsMeeting.chat_id == chat_id,
                TeamsMeeting.bot_id == bot_id,
            )
            .values(
                note_taker_settings_system_name=config_row.system_name,
                last_seen_at=now,
                updated_at=func.now(),
            )
        )

        try:
            async with async_session_maker() as session:
                try:
                    result = await session.execute(stmt)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        except Exception as err:
            logger.exception(
                "Failed to update Teams meeting for note taker config set (chat_id=%s, bot_id=%s)",
                chat_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save note taker config for this meeting: {getattr(err, 'message', str(err))}"
            )
            return

        if getattr(result, "rowcount", 0) == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return

        await context.send_activity(
            (
                f"Saved note taker config {config_row.name or config_row.system_name} "
                f"(system_name: {config_row.system_name}) for this meeting. "
                "If your config includes sending transcript to Salesforce, ensure you set SF account "
                "using **/sf-account-set ACCOUNT_NAME**"
            )
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

        organizer_name = None
        organizer_email = None
        try:
            member = await TeamsInfo.get_member(context, organizer_id)
            organizer_name = getattr(member, "name", None)
            organizer_email = getattr(member, "email", None) or getattr(
                member, "user_principal_name", None
            )
        except Exception:
            pass

        organizer = f"Organizer: {organizer_name} ({organizer_email}) [id: {organizer_id}, aadObjectId: {organizer_aad}]"

        (
            account_id,
            account_name,
            note_taker_settings_system_name,
        ) = await _get_meeting_account_info(context, meeting_id)

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
        subscription_status = await _get_recordings_ready_subscription_status(
            context, online_meeting_id
        )

        try:
            organizer_token_available = await _ensure_organizer_delegated_token_cached(
                context,
                auth_handler_id,
                prompt_on_missing=False,
            )
        except Exception as err:
            logger.debug("Organizer token availability check failed: %s", err)
            organizer_token_available = None

        lines = [
            "Meeting info:",
            f"- Type: {meeting_type}",
            f"- Meeting id: {meeting_id or 'Unknown'}",
            f"- Online meeting id: {online_meeting_id or 'Unknown'}",
            f"- Salesforce account: {(account_name or 'Unknown')} (id: {(account_id or 'Unknown')})",
            f"- Note Taker config: {note_taker_settings_system_name or 'Unknown'}",
            f"- {organizer}",
            f"- Organizer token available: {'yes' if organizer_token_available is True else 'no' if organizer_token_available is False else 'unknown'}",
            f"- Start: {_format_iso_datetime(start_time)}",
            f"- End: {_format_iso_datetime(end_time)}",
            f"- In progress: {status}",
            f"- Recordings-ready subscription: {subscription_status}",
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
                await context.send_activity(
                    "Magnet note taker added to the meeting. "
                    "Please ensure the meeting has the config set using "
                    "**/config-set CONFIG_SYSTEM_NAME**. "
                    "Use **/meeting-info** to check the meeting details."
                )
                # TODO: refactor it
                await _prompt_organizer_personal_install_if_missing(context)
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
        logger.info(
            "[teams note-taker] context details: activity=%s, conversation=%s, from=%s, recipient=%s, channel_id=%s",
            getattr(context, "activity", None),
            getattr(getattr(context, "activity", None), "conversation", None),
            getattr(getattr(context, "activity", None), "from_property", None),
            getattr(getattr(context, "activity", None), "recipient", None),
            getattr(getattr(context, "activity", None), "channel_id", None),
        )

        await _upsert_teams_user_record(context)

        if not text:
            return

        normalized_text = text.lower()

        if normalized_text.startswith("/test-proactive-token"):
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

        if normalized_text.startswith("/welcome"):
            await _send_welcome_card(context)
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
                    "Please use **/sign-in** in our 1:1 chat to authenticate."
                )
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

        if normalized_text.startswith("/recordings-list"):
            await _send_typing(context)
            await _handle_recordings_list(context, _state)
            return

        if normalized_text.startswith("/meeting-info"):
            await _send_typing(context)
            await _handle_meeting_info(context, _state)
            return

        # Organizer gate
        if _is_meeting_conversation(context):
            allowed = await _ensure_meeting_organizer_and_signed_in(
                context, auth_handler_id
            )
            if not allowed:
                return

        if normalized_text.startswith("/sf-account-lookup"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /sf-account-lookup ACCOUNT_NAME")
                return
            account_name = parts[1].strip()
            await _handle_sf_account_lookup(context, account_name)
            return

        if normalized_text.startswith("/sf-account-set"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /sf-account-set ACCOUNT_NAME")
                return
            account_name = parts[1].strip()
            await _handle_sf_account_set(context, account_name)
            return

        if normalized_text.startswith("/config-list"):
            await _handle_note_taker_config_list(context)
            return

        if normalized_text.startswith("/config-set"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /config-set CONFIG_SYSTEM_NAME")
                return

            config_id_or_system_name = parts[1].strip()
            await _handle_note_taker_config_set(context, config_id_or_system_name)
            return

        if normalized_text.startswith("/process-file"):
            logger.info(
                "[teams note-taker] process-file normalized_text: %s", normalized_text
            )
            link = _extract_process_file_link(context, text)
            logger.info("[teams note-taker] process-file extracted_link: %s", link)
            if not link:
                await context.send_activity(
                    "Usage: /process-file link_to_file (you can also paste a formatted link)"
                )
                return

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

        if normalized_text.startswith("/recordings-find"):
            await _send_typing(context)
            await _handle_recordings_find(context, _state)
            return

        if normalized_text.startswith("/process-transcript-job"):
            parts = normalized_text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity(
                    "Usage: /process-transcript-job TRANSCRIPTION_JOB_ID"
                )
                return
            job_id = parts[1].strip()
            await _process_transcription_job_and_notify(context, job_id=job_id)
            return

        await context.send_activity("...not implemented yet...")

    @app.activity("event")
    async def _on_event(context: TurnContext, _state: TurnState) -> None:
        name = getattr(getattr(context, "activity", None), "name", None)
        normalized = str(name or "").lower()
        if normalized == "application/vnd.microsoft.meetingstart":
            logger.info("[teams note-taker] meeting start event received.")
            settings = await _load_note_taker_settings_for_context(context)
            if settings.get("subscription_recordings_ready"):
                await _subscribe_to_recording_notifications(context)
            else:
                await context.send_activity(
                    "Recordings-ready subscription is disabled in settings; skipping subscription."
                )
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
                # base_path = (
                #     f"/users/{quote(user_id_hint, safe='')}/onlineMeetings/{quote(online_meeting_id, safe='')}"
                #     if user_id_hint
                #     else None
                # )
                recording = await get_recording_by_id(
                    client=graph_client,
                    online_meeting_id=online_meeting_id,
                    recording_id=recording_id,
                    # base_path=base_path,
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
                #        # base_path=f"/communications/onlineMeetings/{quote(online_meeting_id, safe='')}",
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
    }

    content_url = recording.get("contentUrl")
    if not content_url:
        await context.send_activity("Recording did not include a downloadable URL.")
        return

    filename = _build_recording_filename(meeting_info, recording, content_url)
    name = Path(filename).stem
    ext = Path(filename).suffix

    async def _build_on_submit(
        resolved_name: str, resolved_ext: str, content_type: str
    ) -> Callable[[str], Awaitable[None]] | None:
        if not _is_meeting_conversation(context):
            return None
        account_id = getattr(meeting_row, "account_id", None)

        async def _notify_salesforce(submit_job_id: str) -> None:
            await _send_stt_recording_to_salesforce(
                context,
                job_id=submit_job_id,
                conversation_date=_format_recording_date_iso(
                    recording.get("createdDateTime")
                ),
                source_file_name=f"{resolved_name}{resolved_ext}",
                source_file_type=content_type,
                account_id=account_id,
                settings_system_name=getattr(
                    meeting_row, "note_taker_settings_system_name", None
                ),
            )

        return _notify_salesforce

    await context.send_activity("Streaming the recording for transcription...")

    headers = {"Authorization": f"Bearer {delegated_token}"}

    await _transcribe_stream_and_notify(
        context,
        download_url=content_url,
        headers=headers,
        name_resolver=lambda *_: (name, ext),
        known_size=await get_recording_file_size(content_url, delegated_token),
        settings_system_name=getattr(
            meeting_row, "note_taker_settings_system_name", None
        ),
        conversation_date=_format_recording_date_iso(recording.get("createdDateTime")),
        on_submit_factory=_build_on_submit,
    )

    return
