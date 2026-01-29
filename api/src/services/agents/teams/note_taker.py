import json
import os
from pathlib import Path
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import unquote
from types import SimpleNamespace

from microsoft_agents.activity import (
    Activity,
    ActionTypes,
    Attachment,
    CardAction,
    ConversationReference,
    OAuthCard,
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
from core.db.models.teams import TeamsMeeting
from core.db.models.teams.note_taker_settings import (
    NoteTakerSettings as NoteTakerSettingsModel,
)
from sqlalchemy import and_, select, or_
from .config import NOTE_TAKER_GRAPH_SCOPES, ISSUER, SCOPE
from .graph import (
    create_graph_client_with_token,
    extract_meeting_id_from_notification,
    extract_user_from_resource,
    get_recording_file_size,
    get_meeting_recordings,
    get_recording_by_id,
)
from .note_taker_salesforce import (
    send_stt_recording_to_salesforce as sf_send_stt_recording_to_salesforce,
)
from .note_taker_meeting import ensure_meeting_title
from .static_connections import StaticConnections
from .teams_user_store import upsert_teams_user, normalize_bot_id
from . import note_taker_store
from .note_taker_transcription import run_transcription_pipeline
from .note_taker_utils import (
    _build_recording_filename,
    _extract_first_url,
    _extract_first_url_from_attachments,
    _format_recording_date_iso,
    _format_recording_datetime_utc_label,
    _merge_note_taker_settings,
)

logger = getLogger(__name__)


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
_ORGANIZER_SIGN_IN_PROMPT = "I need you to sign in with /sign-in in our 1:1 chat so I can access meeting resources."
_ORGANIZER_PERSONAL_INSTALL_PROMPT = "Please install me."


async def _require_meeting_note_taker_settings_system_name(
    context: TurnContext, *, meeting_id: str
) -> str:
    (
        _account_id,
        _account_name,
        settings_system_name,
    ) = await note_taker_store.get_meeting_account_info(context, meeting_id)
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

    await sf_send_stt_recording_to_salesforce(
        context=context,
        settings=settings,
        job_id=job_id,
        conversation_date=conversation_date,
        source_file_name=source_file_name,
        source_file_type=source_file_type,
        account_id=account_id,
        send_expandable_section=_send_expandable_section,
    )


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
    conversation_time: str | None = None,
    known_size: int | None = None,
    settings_system_name: str | None = None,
    meeting_context: dict[str, Any] | None = None,
    on_submit: Callable[[str], Awaitable[None]] | None = None,
    on_submit_factory: Callable[
        [str, str, str], Awaitable[Callable[[str], Awaitable[None]] | None]
    ]
    | None = None,
) -> None:
    await run_transcription_pipeline(
        context,
        kind="stream",
        send_typing=_send_typing,
        send_expandable_section=_send_expandable_section,
        load_settings_by_system_name=_load_note_taker_settings_by_system_name,
        load_settings_for_context=_load_note_taker_settings_for_context,
        resolve_meeting_details=_resolve_meeting_details,
        download_url=download_url,
        headers=headers,
        name_resolver=name_resolver,
        known_size=known_size,
        on_submit=on_submit,
        on_submit_factory=on_submit_factory,
        conversation_date=conversation_date,
        conversation_time=conversation_time,
        settings_system_name=settings_system_name,
        meeting_context=meeting_context,
    )


async def _get_online_meeting_id(context: TurnContext) -> Optional[str]:
    meeting_info = await TeamsInfo.get_meeting_info(context)
    details = getattr(meeting_info, "details", None) or {}
    return getattr(details, "ms_graph_resource_id", None)


def _register_note_taker_handlers(
    app: AgentApplication[TurnState],
    auth_handler_id: str,
    *,
    adapter: CloudAdapter,
    bot_app_id: str,
    bot_tenant_id: str,
) -> None:
    from .note_taker_handlers import (
        register_conversation_updates,
        register_events,
        register_installation,
        register_messages,
    )
    from .note_taker_handlers.state import NoteTakerHandlerDeps, NoteTakerHandlerState

    deps = NoteTakerHandlerDeps(
        adapter=adapter,
        app=app,
        auth_handler_id=auth_handler_id,
        bot_app_id=bot_app_id,
        bot_tenant_id=bot_tenant_id,
        is_meeting_conversation=_is_meeting_conversation,
        is_personal_conversation=_is_personal_teams_conversation,
        resolve_meeting_details=_resolve_meeting_details,
        resolve_user_info=_resolve_user_info,
        get_online_meeting_id=_get_online_meeting_id,
        send_typing=_send_typing,
        send_expandable_section=_send_expandable_section,
        load_settings_by_system_name=_load_note_taker_settings_by_system_name,
        load_settings_for_context=_load_note_taker_settings_for_context,
        extract_process_file_link=_extract_process_file_link,
        transcribe_stream_and_notify=_transcribe_stream_and_notify,
        send_stt_recording_to_salesforce=_send_stt_recording_to_salesforce,
        upsert_teams_user_record=_upsert_teams_user_record,
    )
    state = NoteTakerHandlerState(deps)

    register_installation(app, state)
    register_conversation_updates(app, state)
    register_messages(app, state)
    register_events(app, state)


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
    normalized_bot_id = normalize_bot_id(bot_app_id)

    for notification in notifications:
        if not isinstance(notification, dict):
            continue
        subscription_id = notification.get("subscriptionId")
        if not subscription_id:
            continue

        meeting_row: TeamsMeeting | None = None
        resource_data = notification.get("resourceData") or {}
        chat_id_hint = unquote(str(resource_data.get("chatId") or "")) or None
        meeting_id_hint = extract_meeting_id_from_notification(notification)
        organizer_aad = extract_user_from_resource(notification)
        try:
            async with async_session_maker() as session:
                conditions = [TeamsMeeting.subscription_id == subscription_id]
                conditions.append(
                    and_(
                        TeamsMeeting.graph_online_meeting_id == meeting_id_hint,
                        TeamsMeeting.bot_id == normalized_bot_id,
                    )
                )
                stmt = (
                    select(TeamsMeeting)
                    .where(or_(*conditions))
                    .order_by(TeamsMeeting.updated_at.desc())
                )
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
                conv_ref_payload = (
                    await note_taker_store.fetch_organizer_conversation_reference(
                        organizer_aad=organizer_aad, bot_app_id=bot_app_id
                    )
                )
                if not conv_ref_payload:
                    async with async_session_maker() as session:
                        conv_ref_payload = await note_taker_store.lookup_conversation_reference_by_user_hint(
                            session,
                            bot_app_id=bot_app_id,
                            user_hint=organizer_aad,
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

    user_id_hint = extract_user_from_resource(notification)

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
    await ensure_meeting_title(
        context,
        meeting_info,
        online_meeting_id=online_meeting_id,
        delegated_token=delegated_token,
    )

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
        meeting_context=meeting_info,
        conversation_date=_format_recording_date_iso(recording.get("createdDateTime")),
        conversation_time=_format_recording_datetime_utc_label(
            recording.get("createdDateTime")
        ),
        on_submit_factory=_build_on_submit,
    )

    return
