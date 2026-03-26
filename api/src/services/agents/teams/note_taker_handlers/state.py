from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional
from sqlalchemy import select, update, func, desc
import json

from microsoft_agents.activity import Activity, Attachment, ConversationReference
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from microsoft_agents.hosting.teams import TeamsInfo

from .. import note_taker_store
from ..note_taker_meeting import ensure_meeting_title
from ..teams_user_store import normalize_bot_id

from core.db.session import async_session_maker
from core.db.models.teams import TeamsMeeting
from core.db.models.transcription.transcription import Transcription
from core.db.models.teams.note_taker_settings import (
    NoteTakerSettings as NoteTakerSettingsModel,
)
from ..note_taker_salesforce import (
    config_requires_salesforce as sf_config_requires_salesforce,
    account_lookup,
    get_salesforce_api_server,
    pick_first_account_id_and_name,
    update_meeting_salesforce_account,
)
from ..note_taker_files import _download_file_from_link
from ..note_taker_cards import (
    create_note_taker_welcome_card,
    create_note_taker_config_picker_card,
    create_my_meetings_card,
    create_user_recordings_card,
)
from ..graph import (
    create_graph_client_with_token,
    get_meeting_recordings,
    get_online_meeting_title,
    get_recording_by_id,
    get_recording_file_size,
    list_subscriptions,
    list_user_meetings_with_recordings,
    pick_recordings_ready_subscription,
    create_and_persist_recordings_ready_subscription,
    resolve_recordings_lifecycle_webhook_url,
    resolve_recordings_ready_webhook_url,
)
from ..note_taker_utils import (
    _format_recording_date_iso,
    _format_recording_datetime_utc_label,
    _build_recording_filename,
    _format_duration,
    _format_file_size,
    _format_recording_datetime,
    _format_iso_datetime,
    extract_teams_file_attachment_url,
)
from ..note_taker_people import ManualParticipantStore, personal_config_store
from ..note_taker_transcription import (
    run_transcription_pipeline,
    run_postprocessing_pipeline,
)
from speech_to_text.transcription import service as transcription_service

# Singleton participant store — lives for the duration of the process.
_manual_participant_store = ManualParticipantStore()


@dataclass(frozen=True, slots=True)
class NoteTakerHandlerDeps:
    adapter: CloudAdapter
    app: AgentApplication[TurnState]
    auth_handler_id: str
    bot_app_id: str
    bot_tenant_id: str
    is_meeting_conversation: Callable[[TurnContext], bool]
    is_personal_conversation: Callable[[TurnContext], bool]
    resolve_meeting_details: Callable[[TurnContext], dict[str, Any]]
    resolve_user_info: Callable[[TurnContext], dict[str, Any]]
    get_online_meeting_id: Callable[[TurnContext], Awaitable[Optional[str]]]

    send_typing: Callable[[TurnContext], Awaitable[None]]
    send_expandable_section: Callable[..., Awaitable[None]]
    load_settings_by_system_name: Callable[[str], Awaitable[dict[str, Any]]]
    load_settings_for_context: Callable[[TurnContext], Awaitable[dict[str, Any]]]

    extract_process_file_link: Callable[[TurnContext, str], str | None]
    transcribe_stream_and_notify: Callable[..., Awaitable[None]]
    send_stt_recording_to_salesforce: Callable[..., Awaitable[None]]
    upsert_teams_user_record: Callable[[TurnContext], Awaitable[None]]

    provider_system_name: str = ""


class NoteTakerHandlerState:
    def __init__(self, deps: NoteTakerHandlerDeps) -> None:
        self.deps = deps
        self._logger = getLogger(__name__)

    async def _load_config_picker_metadata(
        self, config_system_name: str | None
    ) -> tuple[bool, str]:
        """
        Resolve optional flags for the /config card (salesforce-enabled + keyterms).
        """
        system_name = str(config_system_name or "").strip()
        if not system_name:
            return False, ""
        try:
            settings = await self.deps.load_settings_by_system_name(system_name)
            salesforce_enabled = sf_config_requires_salesforce(settings)
            keyterms = str(settings.get("keyterms") or "")
            return salesforce_enabled, keyterms
        except Exception:
            return False, ""

    async def _maybe_send_typing(self, context: TurnContext, enabled: bool) -> None:
        if not enabled:
            return
        await self.deps.send_typing(context)

    async def on_sign_in_success(
        self,
        context: TurnContext,
        turn_state: TurnState,
        *,
        handler_id: str | None = None,
    ) -> None:
        self._logger.info(
            "Teams note-taker sign-in succeeded (handler=%s)",
            handler_id or self.deps.auth_handler_id,
        )

    async def on_sign_in_failure(
        self,
        context: TurnContext,
        turn_state: TurnState,
        *,
        handler_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._logger.warning(
            "Teams note-taker sign-in failed (handler=%s): %s",
            handler_id or self.deps.auth_handler_id,
            error_message,
        )
        await context.send_activity("Sign-in failed.")

    async def on_installation_update(
        self, context: TurnContext, turn_state: TurnState
    ) -> None:
        await self._handle_installation_update(context, turn_state)

    async def on_members_added(
        self, context: TurnContext, turn_state: TurnState
    ) -> None:
        await self._handle_members_added(context, turn_state)

    async def on_members_removed(
        self, context: TurnContext, turn_state: TurnState
    ) -> None:
        await self._handle_members_removed(context, turn_state)

    async def on_message(self, context: TurnContext, turn_state: TurnState) -> None:
        await self._handle_message(context, turn_state)

    async def on_event(self, context: TurnContext, turn_state: TurnState) -> None:
        await self._handle_event(context, turn_state)

    async def _send_welcome_card(self, context: TurnContext) -> None:
        bot_name = getattr(
            getattr(getattr(context, "activity", None), "recipient", None),
            "name",
            None,
        )
        is_personal = self.deps.is_personal_conversation(context)
        card = create_note_taker_welcome_card(bot_name, is_personal=is_personal)
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        activity = Activity(type="message", attachments=[attachment])
        await context.send_activity(activity)

    async def _has_existing_token(self, context: TurnContext, handler_id: str) -> bool:
        try:
            handler = self.deps.app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            return bool(getattr(token_response, "token", None))
        except Exception as err:
            self._logger.debug(
                "Token precheck failed (handler=%s): %s",
                handler_id,
                getattr(err, "message", str(err)),
            )
            return False

    async def _send_recordings_summary(
        self,
        context: TurnContext,
        recordings: list,
    ) -> None:
        if not recordings:
            await context.send_activity("No recordings found.")
            return

        lines: list[str] = [f"📹 Found {len(recordings)} recording(s):"]

        for idx, rec in enumerate(recordings, start=1):
            file_size = rec.get("size")
            duration = rec.get("duration")
            rec_id = rec.get("id") or "n/a"
            date_str, time_str = _format_recording_datetime(rec.get("createdDateTime"))
            size_str = _format_file_size(file_size)
            duration_str = _format_duration(duration) if duration is not None else None

            parts: list[str] = [f"{idx}. 📅 {date_str} ⏰ {time_str}"]
            if duration_str:
                parts.append(f"⏱️ {duration_str}")
            parts.append(f"💾 {size_str}")
            parts.append(f"id={rec_id}")

            lines.append("   ".join(parts))

        await context.send_activity("\n\n".join(lines))

    async def _handle_event(self, context: TurnContext, _state: TurnState) -> None:
        name = getattr(getattr(context, "activity", None), "name", None)
        normalized = str(name or "").lower()
        if normalized == "application/vnd.microsoft.meetingstart":
            self._logger.info("[teams note-taker] meeting start event received.")
            settings = await self.deps.load_settings_for_context(context)
            if settings.get("subscription_recordings_ready"):
                await self._subscribe_to_recording_notifications(context)
            else:
                await context.send_activity(
                    "Recordings-ready subscription is disabled in settings; skipping subscription."
                )
        elif normalized == "application/vnd.microsoft.meetingend":
            self._logger.info("[teams note-taker] meeting end event received.")

    async def _get_delegated_token(
        self,
        context: TurnContext,
        handler_id: str,
        failure_message: str,
    ) -> str | None:
        try:
            handler = self.deps.app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            return getattr(token_response, "token", None)
        except Exception as err:
            self._logger.error(
                "Auth failed handler_id=%s message=%s",
                handler_id,
                getattr(err, "message", str(err)),
            )
        await context.send_activity(failure_message)
        return None

    async def _is_meeting_organizer(self, context: TurnContext) -> bool:
        user = self.deps.resolve_user_info(context)
        organizer = await self._get_meeting_organizer_identity(context)
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
        self, context: TurnContext, handler_id: str
    ) -> bool:
        try:
            is_organizer = await self._is_meeting_organizer(context)
        except Exception as err:
            self._logger.warning(
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

        signed_in = await self._has_existing_token(context, handler_id)
        if not signed_in:
            await context.send_activity(
                "Please authenticate with me in our cozy 1:1 chat before using meeting commands."
            )
            return False

        return True

    async def _handle_install_flow(
        self, context: TurnContext, state: TurnState
    ) -> None:
        if not self.deps.is_personal_conversation(context):
            return

        await self._send_welcome_card(context)

        try:
            already_signed_in = await self._has_existing_token(
                context, self.deps.auth_handler_id
            )
        except Exception:
            already_signed_in = False

        if already_signed_in:
            return

        await context.send_activity(
            "Thanks for installing me. Please sign in so I can access your meeting recordings."
        )
        try:
            await self.deps.app.auth._start_or_continue_sign_in(
                context, state, self.deps.auth_handler_id
            )
        except Exception as err:
            self._logger.warning(
                "Failed to start sign-in on installation: %s",
                getattr(err, "message", str(err)),
            )

    async def _handle_installation_update(
        self, context: TurnContext, state: TurnState
    ) -> None:
        activity = getattr(context, "activity", None)
        self._logger.info(
            "[teams note-taker] installation update received: %s", activity
        )
        action = getattr(activity, "action", None)
        if action == "add":
            await self.deps.upsert_teams_user_record(context)
            await note_taker_store.upsert_teams_meeting_record(
                context, is_bot_installed=True
            )
            await self._handle_install_flow(context, state)
            if self.deps.is_meeting_conversation(context):
                await self._handle_note_taker_config_set_picker(context)
        elif action == "remove":
            await note_taker_store.upsert_teams_meeting_record(
                context, is_bot_installed=False
            )

    async def _handle_members_added(
        self, context: TurnContext, _state: TurnState
    ) -> None:
        activity = getattr(context, "activity", None)
        self._logger.info("[teams note-taker] members added received: %s", activity)
        members = getattr(activity, "members_added", None) or []
        bot_id = normalize_bot_id(
            getattr(getattr(activity, "recipient", None), "id", None)
        )
        bot_added = any(getattr(member, "id", None) == bot_id for member in members)
        if bot_added:
            await note_taker_store.upsert_teams_meeting_record(
                context, is_bot_installed=True
            )
            if self.deps.is_meeting_conversation(context):
                await self._handle_note_taker_config_set_picker(context)

    async def _handle_members_removed(
        self, context: TurnContext, _state: TurnState
    ) -> None:
        activity = getattr(context, "activity", None)
        self._logger.info("[teams note-taker] members removed received: %s", activity)
        members = getattr(activity, "members_removed", None) or []
        bot_id = normalize_bot_id(
            getattr(getattr(activity, "recipient", None), "id", None)
        )
        bot_removed = any(getattr(member, "id", None) == bot_id for member in members)
        if bot_removed:
            await note_taker_store.upsert_teams_meeting_record(
                context, is_bot_installed=False
            )

    async def _build_salesforce_submit_callback(
        self,
        context: TurnContext,
        *,
        conversation_date: str | None,
        source_file_name: str,
        source_file_type: str,
    ) -> Callable[[str], Awaitable[None]] | None:
        if not self.deps.is_meeting_conversation(context):
            return None

        meeting_context = self.deps.resolve_meeting_details(context)
        account_id = await note_taker_store.get_meeting_account_id(
            context, meeting_context.get("id")
        )

        async def _notify_salesforce(submit_job_id: str) -> None:
            await self.deps.send_stt_recording_to_salesforce(
                context,
                job_id=submit_job_id,
                conversation_date=conversation_date,
                source_file_name=source_file_name,
                source_file_type=source_file_type,
                account_id=account_id,
            )

        return _notify_salesforce

    def _make_salesforce_on_submit_factory(
        self,
        context: TurnContext,
        *,
        conversation_date: str | None,
    ) -> Callable[[str, str, str], Awaitable[Callable[[str], Awaitable[None]] | None]]:
        async def _factory(
            name: str, ext: str, content_type: str
        ) -> Callable[[str], Awaitable[None]] | None:
            return await self._build_salesforce_submit_callback(
                context,
                conversation_date=conversation_date,
                source_file_name=f"{name}{ext}",
                source_file_type=content_type,
            )

        return _factory

    async def _process_transcription_job_and_notify(
        self,
        context: TurnContext,
        *,
        job_id: str,
        conversation_date: str | None = None,
    ) -> None:
        await run_transcription_pipeline(
            context,
            kind="job",
            send_typing=self.deps.send_typing,
            send_expandable_section=self.deps.send_expandable_section,
            load_settings_by_system_name=self.deps.load_settings_by_system_name,
            load_settings_for_context=self.deps.load_settings_for_context,
            resolve_meeting_details=self.deps.resolve_meeting_details,
            job_id=job_id,
            conversation_date=conversation_date,
            build_on_submit_callback=self._build_salesforce_submit_callback,
        )

    async def _handle_note_taker_config_set_picker(self, context: TurnContext) -> None:
        await self.deps.send_typing(context)

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        (
            _account_id,
            current_account_name,
            current_system_name,
        ) = await note_taker_store.get_meeting_account_info(context, meeting_id)

        salesforce_enabled, current_keyterms = await self._load_config_picker_metadata(
            current_system_name
        )

        try:
            async with async_session_maker() as session:
                stmt = select(
                    NoteTakerSettingsModel.id,
                    NoteTakerSettingsModel.name,
                    NoteTakerSettingsModel.system_name,
                    NoteTakerSettingsModel.description,
                ).order_by(NoteTakerSettingsModel.created_at.asc())
                # Filter to configs belonging to this bot's provider when known
                if self.deps.provider_system_name:
                    stmt = stmt.where(
                        NoteTakerSettingsModel.provider_system_name
                        == self.deps.provider_system_name
                    )
                result = await session.execute(stmt)
                rows = result.all()
        except Exception as err:
            self._logger.exception("Failed to list note taker configs for picker")
            await context.send_activity(
                f"Failed to list note taker configs: {getattr(err, 'message', str(err))}"
            )
            return

        if not rows:
            await context.send_activity(
                "No note taker configs found. Create one in the admin UI first."
            )
            return

        card = create_note_taker_config_picker_card(
            rows,
            current_system_name=current_system_name,
            current_account_name=current_account_name,
            current_keyterms=current_keyterms,
            salesforce_enabled=salesforce_enabled,
        )
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        activity = Activity(type="message", attachments=[attachment])
        await context.send_activity(activity)

    async def _refresh_note_taker_config_picker_card(
        self,
        context: TurnContext,
        *,
        selected_system_name: str,
    ) -> None:
        try:
            async with async_session_maker() as session:
                stmt = select(
                    NoteTakerSettingsModel.id,
                    NoteTakerSettingsModel.name,
                    NoteTakerSettingsModel.system_name,
                    NoteTakerSettingsModel.description,
                ).order_by(NoteTakerSettingsModel.created_at.asc())
                if self.deps.provider_system_name:
                    stmt = stmt.where(
                        NoteTakerSettingsModel.provider_system_name
                        == self.deps.provider_system_name
                    )
                result = await session.execute(stmt)
                rows = result.all()
        except Exception as err:
            self._logger.debug(
                "Failed to refresh note taker config picker card: %s", err
            )
            return

        if not rows:
            return

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        (
            _account_id,
            current_account_name,
            _current_system_name,
        ) = await note_taker_store.get_meeting_account_info(context, meeting_id)

        salesforce_enabled, current_keyterms = await self._load_config_picker_metadata(
            selected_system_name
        )

        card = create_note_taker_config_picker_card(
            rows,
            current_system_name=selected_system_name,
            current_account_name=current_account_name,
            current_keyterms=current_keyterms,
            salesforce_enabled=salesforce_enabled,
        )
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        outgoing = Activity(type="message", attachments=[attachment])

        activity = getattr(context, "activity", None)
        reply_to_id = getattr(activity, "reply_to_id", None)
        if reply_to_id:
            outgoing.id = reply_to_id
            try:
                updater = getattr(context, "update_activity", None)
                if callable(updater):
                    await updater(outgoing)
                    return
            except Exception as err:
                self._logger.debug(
                    "Failed to update config picker card activity %s: %s",
                    reply_to_id,
                    err,
                )

        try:
            await context.send_activity(outgoing)
        except Exception as err:
            self._logger.debug("Failed to send refreshed config picker card: %s", err)

    async def _handle_note_taker_config_set(
        self, context: TurnContext, config_system_name: str, *, show_typing: bool = True
    ) -> bool:
        await self._maybe_send_typing(context, show_typing)

        try:
            async with async_session_maker() as session:
                stmt = select(NoteTakerSettingsModel).where(
                    NoteTakerSettingsModel.system_name == config_system_name
                )
                config_row = (await session.execute(stmt)).scalars().first()
        except Exception as err:
            self._logger.exception(
                "Failed to resolve note taker config %s", config_system_name
            )
            await context.send_activity(
                f"Failed to resolve note taker config: {getattr(err, 'message', str(err))}"
            )
            return False

        if config_row is None:
            await context.send_activity("Note taker config not found.")
            return False

        # In personal chats, store the config in the in-process store.
        if self.deps.is_personal_conversation(context):
            personal_config_store.set(context, config_row.system_name)
            return True

        meeting_context = self.deps.resolve_meeting_details(context)
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve chat or bot id for this conversation."
            )
            return False

        now = dt.datetime.now(dt.timezone.utc)
        stmt = (
            update(TeamsMeeting)
            .where(TeamsMeeting.chat_id == chat_id, TeamsMeeting.bot_id == bot_id)
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
            self._logger.exception(
                "Failed to update Teams meeting for note taker config set (chat_id=%s, bot_id=%s)",
                chat_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save note taker config for this meeting: {getattr(err, 'message', str(err))}"
            )
            return False

        if getattr(result, "rowcount", 0) == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return False

        return True

    async def _handle_note_taker_keyterms_set(
        self,
        context: TurnContext,
        *,
        config_system_name: str,
        keyterms: str,
        show_typing: bool = True,
        notify_user: bool = True,
    ) -> None:
        config_system_name = str(config_system_name or "").strip()
        if not config_system_name:
            await context.send_activity("Please pick a valid config.")
            return

        await self._maybe_send_typing(context, show_typing)

        try:
            async with async_session_maker() as session:
                stmt = select(NoteTakerSettingsModel).where(
                    NoteTakerSettingsModel.system_name == config_system_name
                )
                config_row = (await session.execute(stmt)).scalars().first()
                if config_row is None:
                    await context.send_activity("Note taker config not found.")
                    return

                raw_config = config_row.config
                if isinstance(raw_config, str):
                    try:
                        raw_config = json.loads(raw_config)
                    except Exception:
                        raw_config = None

                config = dict(raw_config) if isinstance(raw_config, dict) else {}
                config["keyterms"] = str(keyterms or "").strip()
                config_row.config = config
                await session.commit()
        except Exception as err:
            self._logger.exception(
                "Failed to update keyterms for note taker config %s",
                config_system_name,
            )
            await context.send_activity(
                f"Failed to save keyterms: {getattr(err, 'message', str(err))}"
            )
            return

        if notify_user:
            await context.send_activity("Keyterms saved.")

    async def _handle_sf_account_set(
        self, context: TurnContext, account_name: str, *, show_typing: bool = True
    ) -> None:
        if not account_name:
            await context.send_activity("Usage: /sf-account-set ACCOUNT_NAME")
            return

        if not self.deps.is_meeting_conversation(context):
            await context.send_activity("This command works only in meeting chats.")
            return

        await self._maybe_send_typing(context, show_typing)

        try:
            settings = await self.deps.load_settings_for_context(context)
            salesforce_api_server = get_salesforce_api_server(settings)
            result = await account_lookup(account_name, server=salesforce_api_server)
        except Exception as err:
            self._logger.exception(
                "Salesforce account lookup failed for %s", account_name
            )
            await context.send_activity(
                f"Salesforce account lookup failed: {getattr(err, 'message', str(err))}"
            )
            return

        if not isinstance(result, list) or not result:
            await context.send_activity("No Salesforce accounts found to set.")
            return

        account_id, account_name_value = pick_first_account_id_and_name(
            result, fallback_account_name=account_name
        )
        if not account_id:
            await context.send_activity(
                "Salesforce account lookup did not return an accountId."
            )
            return

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not meeting_id or not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve meeting, chat, or bot id for this conversation."
            )
            return

        try:
            rowcount = await update_meeting_salesforce_account(
                chat_id=chat_id,
                bot_id=bot_id,
                account_id=account_id,
                account_name=account_name_value,
            )
        except Exception as err:
            self._logger.exception(
                "Failed to update Teams meeting for account set (meeting_id=%s, bot_id=%s)",
                meeting_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save account for this meeting: {getattr(err, 'message', str(err))}"
            )
            return

        if rowcount == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return

    async def _handle_recordings_list_personal(
        self,
        context: TurnContext,
    ) -> None:
        """List recordings across the user's recent meetings (personal chat).

        Fetches known meeting IDs from the ``TeamsMeeting`` database table
        (meetings where this bot was installed), then queries Graph for
        recordings using the user's delegated token.  Only meetings whose
        recordings are accessible to the signed-in user are returned.
        """
        delegated_token = await self._get_delegated_token(
            context,
            self.deps.auth_handler_id,
            "Please sign in with **/sign-in** so I can fetch your recordings.",
        )
        if not delegated_token:
            return

        await self.deps.send_typing(context)

        # Resolve the bot id so we can scope the DB query.
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))

        # Fetch recent meetings from DB that have a Graph meeting id.
        try:
            async with async_session_maker() as session:
                stmt = (
                    select(TeamsMeeting.graph_online_meeting_id)
                    .where(
                        TeamsMeeting.graph_online_meeting_id.isnot(None),
                        TeamsMeeting.is_bot_installed.is_(True),
                    )
                    .order_by(desc(TeamsMeeting.last_seen_at))
                    .limit(30)
                )
                if bot_id:
                    stmt = stmt.where(TeamsMeeting.bot_id == bot_id)
                result = await session.execute(stmt)
                meeting_ids: list[str] = [row[0] for row in result.all() if row[0]]
        except Exception:
            self._logger.exception("Failed to query TeamsMeeting for recordings-list")
            await context.send_activity(
                "Could not retrieve meeting list from the database."
            )
            return

        if not meeting_ids:
            await context.send_activity(
                "No meetings found yet. The bot needs to be added to a meeting first "
                "so that recordings become available."
            )
            return

        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                meetings_with_recs = await list_user_meetings_with_recordings(
                    graph_client,
                    content_token=delegated_token,
                    meeting_ids=meeting_ids,
                    add_size=True,
                )
        except Exception as err:
            self._logger.exception("Failed to list user meetings with recordings")
            await context.send_activity(
                f"Could not retrieve your meetings: {getattr(err, 'message', str(err))}"
            )
            return

        card = create_user_recordings_card(meetings_with_recs)
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        await context.send_activity(Activity(type="message", attachments=[attachment]))

    async def _handle_recordings_list(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
        recordings: list | None = None,
        meeting: dict[str, Any] | None = None,
        delegated_token: str | None = None,
        transcribe_latest: bool = False,
    ) -> None:
        # In personal chat, delegate to the personal-chat handler.
        if self.deps.is_personal_conversation(context):
            await self._handle_recordings_list_personal(context)
            return

        meeting = meeting or self.deps.resolve_meeting_details(context)
        online_meeting_id: str | None = None
        if recordings is None:
            if not (meeting.get("id") or meeting.get("conversationId")):
                self._logger.warning("No meeting id found for recordings-list command.")
                return

            await self.deps.send_typing(context)

            try:
                online_meeting_id = await self.deps.get_online_meeting_id(context)
                if not online_meeting_id:
                    await context.send_activity(
                        "No online meeting id found for this meeting."
                    )
                    return

                if not delegated_token:
                    delegated_token = await self._get_delegated_token(
                        context,
                        self.deps.auth_handler_id,
                        "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
                    )
                    if not delegated_token:
                        return

                await ensure_meeting_title(
                    context,
                    meeting,
                    delegated_token=delegated_token,
                    online_meeting_id=online_meeting_id,
                )

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
                self._logger.exception("Failed to fetch meeting recordings")
                await context.send_activity(
                    f"Could not retrieve meeting recordings for {meeting.get('title') or 'meeting'}: {getattr(err, 'message', str(err))}"
                )
                return

        await self._send_recordings_summary(context, recordings)

        if transcribe_latest and recordings:
            await self.deps.send_typing(context)
            if not online_meeting_id:
                online_meeting_id = await self.deps.get_online_meeting_id(context)
            await ensure_meeting_title(
                context,
                meeting,
                delegated_token=delegated_token,
                online_meeting_id=online_meeting_id,
            )
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

            await context.send_activity(
                "Streaming the latest recording for transcription..."
            )
            await self.deps.send_typing(context)

            headers = {"Authorization": f"Bearer {delegated_token}"}
            conversation_date = _format_recording_date_iso(
                recordings[0].get("createdDateTime")
            )
            conversation_time = _format_recording_datetime_utc_label(
                recordings[0].get("createdDateTime")
            )
            await self.deps.transcribe_stream_and_notify(
                context,
                download_url=content_url,
                headers=headers,
                name_resolver=lambda *_: (name, ext),
                known_size=recordings[0].get("size")
                or await get_recording_file_size(content_url, delegated_token),
                meeting_context=meeting,
                conversation_date=conversation_date,
                conversation_time=conversation_time,
                on_submit_factory=self._make_salesforce_on_submit_factory(
                    context,
                    conversation_date=conversation_date,
                ),
            )

    async def _handle_process_recording(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
        recording_id: str,
    ) -> None:
        meeting = self.deps.resolve_meeting_details(context)
        if not (meeting.get("id") or meeting.get("conversationId")):
            self._logger.warning("No meeting id found for process-recording command.")
            await context.send_activity(
                "No meeting information available in this chat."
            )
            return

        delegated_token = await self._get_delegated_token(
            context,
            self.deps.auth_handler_id,
            "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
        )
        if not delegated_token:
            return

        await self.deps.send_typing(context)

        try:
            online_meeting_id = await self.deps.get_online_meeting_id(context)
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
            self._logger.exception("Failed to fetch recording by id")
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

        await ensure_meeting_title(
            context,
            meeting,
            delegated_token=delegated_token,
            online_meeting_id=online_meeting_id,
        )

        filename = _build_recording_filename(meeting, recording, content_url)
        name = Path(filename).stem
        ext = Path(filename).suffix

        await context.send_activity("Streaming the recording for transcription...")
        await self.deps.send_typing(context)

        headers = {"Authorization": f"Bearer {delegated_token}"}
        conversation_date = _format_recording_date_iso(recording.get("createdDateTime"))
        conversation_time = _format_recording_datetime_utc_label(
            recording.get("createdDateTime")
        )

        await self.deps.transcribe_stream_and_notify(
            context,
            download_url=content_url,
            headers=headers,
            name_resolver=lambda *_: (name, ext),
            known_size=recording.get("size")
            or await get_recording_file_size(content_url, delegated_token),
            meeting_context=meeting,
            conversation_date=conversation_date,
            conversation_time=conversation_time,
            on_submit_factory=self._make_salesforce_on_submit_factory(
                context,
                conversation_date=conversation_date,
            ),
        )

    async def _handle_process_recording_by_meeting_id(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
        *,
        meeting_id: str,
        recording_id: str,
    ) -> None:
        """Process a recording identified by online meeting id + recording id.

        Used from personal chat when the user picks a recording from the
        ``create_user_recordings_card`` adaptive card.
        """
        delegated_token = await self._get_delegated_token(
            context,
            self.deps.auth_handler_id,
            "Please sign in with **/sign-in** so I can fetch the recording.",
        )
        if not delegated_token:
            return

        await self.deps.send_typing(context)

        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                recording = await get_recording_by_id(
                    client=graph_client,
                    online_meeting_id=meeting_id,
                    recording_id=recording_id,
                )
        except Exception as err:
            self._logger.exception("Failed to fetch recording by id (personal)")
            await context.send_activity(
                f"Could not retrieve recording {recording_id}: {getattr(err, 'message', str(err))}"
            )
            return

        if not recording:
            await context.send_activity(f"No recording found with id {recording_id}.")
            return

        if not recording.get("contentUrl") and recording.get("recordingContentUrl"):
            recording["contentUrl"] = recording["recordingContentUrl"]

        content_url = recording.get("contentUrl")
        if not content_url:
            await context.send_activity("Recording did not include a downloadable URL.")
            return

        # Build a minimal meeting context for the transcription pipeline.
        meeting: dict[str, Any] = {"id": meeting_id}
        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                title = await get_online_meeting_title(
                    client=graph_client, online_meeting_id=meeting_id
                )
            if title:
                meeting["title"] = title
        except Exception:
            pass

        filename = _build_recording_filename(meeting, recording, content_url)
        name = Path(filename).stem
        ext = Path(filename).suffix

        await context.send_activity("Streaming the recording for transcription...")
        await self.deps.send_typing(context)

        headers = {"Authorization": f"Bearer {delegated_token}"}
        conversation_date = _format_recording_date_iso(recording.get("createdDateTime"))
        conversation_time = _format_recording_datetime_utc_label(
            recording.get("createdDateTime")
        )

        await self.deps.transcribe_stream_and_notify(
            context,
            download_url=content_url,
            headers=headers,
            name_resolver=lambda *_: (name, ext),
            known_size=recording.get("size")
            or await get_recording_file_size(content_url, delegated_token),
            meeting_context=meeting,
            conversation_date=conversation_date,
            conversation_time=conversation_time,
            on_submit_factory=self._make_salesforce_on_submit_factory(
                context,
                conversation_date=conversation_date,
            ),
        )

    async def _handle_participants_command(
        self, context: TurnContext, text: str
    ) -> None:
        """Handle /participants add|list|clear in personal chat."""
        parts = text.strip().split(maxsplit=2)
        sub = parts[1].lower() if len(parts) > 1 else ""

        if sub == "add":
            raw_name = parts[2].strip() if len(parts) > 2 else ""
            if not raw_name:
                await context.send_activity(
                    "Usage: /participants add Full Name [<email@example.com>]"
                )
                return
            person = _manual_participant_store.add(context, raw_name)
            if person:
                display = (
                    (person.get("first_name") or "")
                    + " "
                    + (person.get("last_name") or "")
                ).strip()
                await context.send_activity(f"Added participant: **{display}**")
            else:
                await context.send_activity("Name was empty — nothing added.")
            return

        if sub == "list":
            people = _manual_participant_store.list(context)
            if not people:
                await context.send_activity(
                    "No participants added yet. Use **/participants add Full Name** to add one."
                )
                return
            lines = ["**Participants:**"]
            for i, p in enumerate(people, 1):
                display = (
                    (p.get("first_name") or "") + " " + (p.get("last_name") or "")
                ).strip()
                email = p.get("email") or ""
                lines.append(f"{i}. {display}" + (f" <{email}>" if email else ""))
            await context.send_activity("\n".join(lines))
            return

        if sub == "clear":
            count = _manual_participant_store.clear(context)
            await context.send_activity(
                f"Cleared {count} participant(s)."
                if count
                else "No participants to clear."
            )
            return

        await context.send_activity(
            "Commands:\n"
            "- **/participants add Full Name** — add a participant\n"
            "- **/participants list** — show current participants\n"
            "- **/participants clear** — remove all participants"
        )

    async def _handle_process_file(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
        link: str,
    ) -> None:
        meeting = self.deps.resolve_meeting_details(context)
        token = None
        if self.deps.is_meeting_conversation(context):
            token = await self._get_delegated_token(
                context,
                self.deps.auth_handler_id,
                "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
            )
            if not token:
                return
            online_meeting_id = await self.deps.get_online_meeting_id(context)
            await ensure_meeting_title(
                context,
                meeting,
                delegated_token=token,
                online_meeting_id=online_meeting_id,
            )

        try:
            download_url, headers, name_resolver = await _download_file_from_link(
                link, token, meeting=meeting
            )
        except Exception as err:
            self._logger.exception("Failed to resolve file download link")
            await context.send_activity(
                f"I couldn't resolve that link: {getattr(err, 'message', str(err))}"
            )
            return

        # In personal chat, merge manually-entered participants into meeting_context
        # so the pipeline can use them for speaker hints.
        if self.deps.is_personal_conversation(context):
            manual_people = _manual_participant_store.list(context)
            if manual_people:
                meeting = dict(meeting or {})
                meeting.setdefault("invited_people", manual_people)

        await context.send_activity("Streaming the file for transcription...")
        await self.deps.transcribe_stream_and_notify(
            context,
            download_url=download_url,
            headers=headers,
            name_resolver=name_resolver,
            meeting_context=meeting
            if (meeting.get("id") or meeting.get("conversationId"))
            else None,
            on_submit_factory=self._make_salesforce_on_submit_factory(
                context,
                conversation_date=None,
            ),
        )

    async def _check_meeting_in_progress(
        self, context: TurnContext, meeting_id: str
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
                    except Exception:
                        continue

                    meeting_info = (
                        participant.get("meeting")
                        if isinstance(participant, dict)
                        else {}
                    )
                    in_meeting_flag = (meeting_info or {}).get("in_meeting") or (
                        meeting_info or {}
                    ).get("inMeeting")
                    if in_meeting_flag:
                        return True

                continuation_token = getattr(paged, "continuation_token", None)
                if not continuation_token:
                    break
        except Exception as err:
            self._logger.debug("Failed to iterate meeting participants: %s", err)
            return None

        return False

    async def _get_recordings_ready_subscription_status(
        self, context: TurnContext, online_meeting_id: str | None
    ) -> str:
        if not online_meeting_id:
            return "unknown (missing online meeting id)"

        delegated_token = await self._get_organizer_delegated_token_from_cache(context)
        if not delegated_token:
            return "unknown (organizer delegated token missing)"

        try:
            async with create_graph_client_with_token(delegated_token) as graph_client:
                subscriptions = await list_subscriptions(graph_client)
            subscription = pick_recordings_ready_subscription(
                subscriptions, online_meeting_id=online_meeting_id
            )
        except Exception as err:
            self._logger.warning(
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

    async def _handle_meeting_info(
        self,
        context: TurnContext,
        state: Optional[TurnState],
    ) -> None:
        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        if not meeting_id:
            await context.send_activity(
                "I couldn't find a meeting id in the channel data for this conversation."
            )
            return

        await self.deps.send_typing(context)

        meeting_info = await TeamsInfo.get_meeting_info(context)
        details = getattr(meeting_info, "details", None) or {}
        organizer_obj = getattr(meeting_info, "organizer", None) or {}
        online_meeting_id = await self.deps.get_online_meeting_id(context)

        await ensure_meeting_title(
            context,
            meeting_context,
            meeting_details=details,
        )
        meeting_title = meeting_context.get("title")
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

        organizer = (
            f"Organizer: {organizer_name} ({organizer_email}) "
            f"[id: {organizer_id}, aadObjectId: {organizer_aad}]"
        )

        (
            account_id,
            account_name,
            note_taker_settings_system_name,
        ) = await note_taker_store.get_meeting_account_info(context, meeting_id)

        try:
            in_progress = await self._check_meeting_in_progress(context, meeting_id)
        except Exception as err:
            self._logger.debug("Meeting in-progress check failed: %s", err)
            in_progress = None

        status = (
            "yes (at least one participant found in meeting)"
            if in_progress is True
            else "no active participants found in meeting"
            if in_progress is False
            else "unknown (could not verify participants)"
        )
        subscription_status = await self._get_recordings_ready_subscription_status(
            context, online_meeting_id
        )

        if not meeting_title and online_meeting_id:
            try:
                has_token = await self._has_existing_token(
                    context, self.deps.auth_handler_id
                )
            except Exception:
                has_token = False

            if has_token:
                delegated_token = await self._get_delegated_token(
                    context,
                    self.deps.auth_handler_id,
                    "Please sign in with /sign-in in our 1:1 chat so I can fetch meeting details from Microsoft Graph.",
                )
                await ensure_meeting_title(
                    context,
                    meeting_context,
                    delegated_token=delegated_token,
                    online_meeting_id=online_meeting_id,
                    meeting_details=details,
                )
                meeting_title = meeting_context.get("title")

        lines = [
            "Meeting info:",
            f"- Title: {meeting_title or 'Unknown'}",
            f"- Type: {meeting_type}",
            f"- Meeting id: {meeting_id or 'Unknown'}",
            f"- Online meeting id: {online_meeting_id or 'Unknown'}",
            f"- Salesforce account: {(account_name or 'Unknown')} (id: {(account_id or 'Unknown')})",
            f"- Note Taker config: {note_taker_settings_system_name or 'Unknown'}",
            f"- {organizer}",
            f"- Start: {_format_iso_datetime(start_time)}",
            f"- End: {_format_iso_datetime(end_time)}",
            f"- In progress: {status}",
            f"- Recordings-ready subscription: {subscription_status}",
        ]
        await context.send_activity("\n".join(lines))

    async def _handle_card_action(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
        submit_value: dict[str, Any],
    ) -> None:
        """Handle Adaptive Card submit actions (magnet_action dispatching)."""
        magnet_action = submit_value.get("magnet_action")

        if magnet_action == "note_taker_config_set":
            config_system_name = (submit_value.get("config_system_name") or "").strip()
            if not config_system_name:
                await context.send_activity("Please pick a valid config.")
                return
            if self.deps.is_meeting_conversation(context):
                allowed = await self._ensure_meeting_organizer_and_signed_in(
                    context, self.deps.auth_handler_id
                )
                if not allowed:
                    return
            account_name = (submit_value.get("account_name") or "").strip()
            salesforce_enabled, _ = await self._load_config_picker_metadata(
                config_system_name
            )
            ok = await self._handle_note_taker_config_set(
                context, config_system_name, show_typing=False
            )
            if not ok:
                return
            if salesforce_enabled and account_name:
                try:
                    await self._handle_sf_account_set(
                        context, account_name, show_typing=False
                    )
                except Exception:
                    self._logger.exception(
                        "Failed to save Salesforce account from config picker."
                    )
            keyterms = str(submit_value.get("keyterms") or "")
            await self._handle_note_taker_keyterms_set(
                context,
                config_system_name=config_system_name,
                keyterms=keyterms,
                show_typing=False,
                notify_user=False,
            )
            await self._refresh_note_taker_config_picker_card(
                context, selected_system_name=config_system_name
            )
            return

        if magnet_action == "confirm_speaker_mapping":
            pending_id = str(submit_value.get("pending_id") or "").strip()
            if not pending_id:
                await context.send_activity("Invalid confirmation: missing pending_id.")
                return
            skip = bool(submit_value.get("skip"))
            if skip:
                confirmed_mapping: dict[str, str] = {}
                extra_keyterms: list[str] = []
                meeting_notes: str = ""
            else:
                confirmed_mapping = {}
                for k, v in submit_value.items():
                    if k.startswith("speaker__") and v:
                        speaker_key = k[len("speaker__") :]
                        confirmed_mapping[speaker_key] = str(v).strip()
                keyterms_raw = str(submit_value.get("keyterms") or "").strip()
                import re as _re

                extra_keyterms = (
                    [
                        t.strip()
                        for t in _re.split(r"[,;\n]+", keyterms_raw)
                        if t.strip()
                    ]
                    if keyterms_raw
                    else []
                )
                meeting_notes = str(submit_value.get("meeting_notes") or "").strip()

            await context.send_activity(
                "Speaker mapping confirmed. Processing summary and chapters..."
            )
            await run_postprocessing_pipeline(
                context,
                pending_id=pending_id,
                speaker_mapping=confirmed_mapping,
                extra_keyterms=extra_keyterms,
                meeting_notes=meeting_notes or None,
                send_expandable_section=self.deps.send_expandable_section,
                load_settings_by_system_name=self.deps.load_settings_by_system_name,
                load_settings_for_context=self.deps.load_settings_for_context,
                resolve_meeting_details=self.deps.resolve_meeting_details,
            )
            return

        if magnet_action == "note_taker_keyterms_set":
            config_system_name = (submit_value.get("config_system_name") or "").strip()
            if not config_system_name:
                await context.send_activity("Please pick a valid config.")
                return
            if self.deps.is_meeting_conversation(context):
                allowed = await self._ensure_meeting_organizer_and_signed_in(
                    context, self.deps.auth_handler_id
                )
                if not allowed:
                    return
            keyterms = str(submit_value.get("keyterms") or "")
            await self._handle_note_taker_keyterms_set(
                context,
                config_system_name=config_system_name,
                keyterms=keyterms,
                show_typing=False,
                notify_user=True,
            )
            await self._refresh_note_taker_config_picker_card(
                context, selected_system_name=config_system_name
            )
            return

        if magnet_action == "view_transcript":
            job_id = str(submit_value.get("job_id") or "").strip()
            if not job_id:
                await context.send_activity("Invalid job ID.")
                return
            await self.deps.send_typing(context)
            await self._handle_view_transcript(context, job_id=job_id)
            return

        if magnet_action == "reprocess_meeting":
            job_id = str(submit_value.get("job_id") or "").strip()
            if not job_id:
                await context.send_activity("Invalid job ID.")
                return
            await self.deps.send_typing(context)
            await self._process_transcription_job_and_notify(context, job_id=job_id)
            return

        if magnet_action == "process_recording_from_list":
            meeting_id = str(submit_value.get("meeting_id") or "").strip()
            recording_id = str(submit_value.get("recording_id") or "").strip()
            if not meeting_id or not recording_id:
                await context.send_activity("Missing meeting or recording id.")
                return
            await self.deps.send_typing(context)
            await self._handle_process_recording_by_meeting_id(
                context,
                turn_state,
                meeting_id=meeting_id,
                recording_id=recording_id,
            )
            return

    async def _handle_message(
        self, context: TurnContext, turn_state: TurnState
    ) -> None:
        activity = getattr(context, "activity", None)
        text = (getattr(activity, "text", "") or "").strip()
        self._logger.info("[teams note-taker] message received: %s", text)

        await self.deps.upsert_teams_user_record(context)

        submit_value = getattr(activity, "value", None)
        if isinstance(submit_value, dict) and submit_value.get("magnet_action"):
            await self._handle_card_action(context, turn_state, submit_value)
            return

        if not text:
            return

        normalized_text = text.lower()

        if normalized_text.startswith("/welcome"):
            await self._send_welcome_card(context)
            return

        if normalized_text.startswith("/sign-in"):
            if self.deps.is_personal_conversation(context):
                try:
                    already_signed_in = await self._has_existing_token(
                        context, self.deps.auth_handler_id
                    )
                except Exception:
                    already_signed_in = False

                if already_signed_in:
                    await context.send_activity(
                        "You're signed in. Use **/sign-out** to sign out."
                    )
                    return

                try:
                    await self.deps.app.auth._start_or_continue_sign_in(
                        context, turn_state, self.deps.auth_handler_id
                    )
                except Exception as err:
                    self._logger.exception("Failed to start sign-in: %s", err)
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
                await self.deps.app.auth.sign_out(context, self.deps.auth_handler_id)
                await context.send_activity(
                    "You're signed out. Use **/sign-in** to sign in again."
                )
            except Exception as err:
                self._logger.exception("Failed to sign out: %s", err)
                await context.send_activity(
                    f"Couldn't sign you out right now: {getattr(err, 'message', str(err))}"
                )
            return

        if normalized_text.startswith("/whoami"):
            info = self.deps.resolve_user_info(context)
            has_existing_token = await self._has_existing_token(
                context, self.deps.auth_handler_id
            )
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
            await self.deps.send_typing(context)
            await self._handle_recordings_list(context, turn_state)
            return

        if normalized_text.startswith("/meeting-info"):
            await self.deps.send_typing(context)
            await self._handle_meeting_info(context, turn_state)
            return

        if self.deps.is_meeting_conversation(context):
            allowed = await self._ensure_meeting_organizer_and_signed_in(
                context, self.deps.auth_handler_id
            )
            if not allowed:
                return

        if normalized_text.startswith("/config"):
            await self._handle_note_taker_config_set_picker(context)
            return

        if normalized_text.startswith("/participants"):
            await self._handle_participants_command(context, text)
            return

        if normalized_text.startswith("/process-file"):
            link = self.deps.extract_process_file_link(context, text)
            if not link:
                await context.send_activity(
                    "Usage: /process-file link_to_file (you can also paste a formatted link)"
                )
                return
            await self.deps.send_typing(context)
            await self._handle_process_file(context, turn_state, link)
            return

        if normalized_text.startswith("/process-recording"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity("Usage: /process-recording RECORDING_ID")
                return
            rec_id = parts[1].strip()
            await self.deps.send_typing(context)
            await self._handle_process_recording(context, turn_state, rec_id)
            return

        if normalized_text.startswith("/recordings-find"):
            await self.deps.send_typing(context)
            await self._handle_recordings_find(context, turn_state)
            return

        if normalized_text.startswith("/my-meetings"):
            await self.deps.send_typing(context)
            await self._handle_my_meetings(context)
            return

        if normalized_text.startswith("/process-transcript-job"):
            parts = normalized_text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await context.send_activity(
                    "Usage: /process-transcript-job TRANSCRIPTION_JOB_ID"
                )
                return
            job_id = parts[1].strip()

            # Verify the job belongs to the current context to prevent cross-access.
            current_meeting = self.deps.resolve_meeting_details(context)
            current_meeting_id: str | None = (current_meeting or {}).get("id")
            if current_meeting_id:
                # Meeting chat: verify the job belongs to THIS meeting.
                job_meta = await transcription_service.get_meta(job_id)
                if job_meta is not None:
                    job_meeting_id: str | None = job_meta.get("meeting_id")
                    if job_meeting_id and job_meeting_id != current_meeting_id:
                        await context.send_activity(
                            "This transcription job does not belong to the current meeting."
                        )
                        return
            elif self.deps.is_personal_conversation(context):
                # Personal chat: verify the job was initiated by THIS user
                # OR the user is a designated superuser for this note-taker.
                job_meta = await transcription_service.get_meta(job_id)
                if job_meta is not None:
                    job_initiated_by: str | None = job_meta.get("initiated_by")
                    if job_initiated_by:
                        _activity = getattr(context, "activity", None)
                        _from = getattr(_activity, "from_property", None) or getattr(
                            _activity, "from", None
                        )
                        current_aad_id: str | None = getattr(
                            _from, "aad_object_id", None
                        )
                        if current_aad_id and job_initiated_by != current_aad_id:
                            # Check superuser before rejecting
                            from services.agents.teams.note_taker import (
                                get_superuser_id_for_bot,
                            )

                            _bot_id = getattr(
                                getattr(_activity, "recipient", None), "id", None
                            )
                            superuser = await get_superuser_id_for_bot(_bot_id)
                            if not (superuser and current_aad_id == superuser):
                                await context.send_activity(
                                    "This transcription job does not belong to you."
                                )
                                return

            await self._process_transcription_job_and_notify(context, job_id=job_id)
            return

        # In personal chat, allow users to drop a file attachment for transcription.
        if self.deps.is_personal_conversation(context):
            attachment_url = extract_teams_file_attachment_url(
                getattr(context, "activity", None)
            )
            if attachment_url:
                await self.deps.send_typing(context)
                await self._handle_process_file(context, turn_state, attachment_url)
                return

        await context.send_activity("...not implemented yet...")

    async def _handle_recordings_find(
        self,
        context: TurnContext,
        turn_state: Optional[TurnState],
    ) -> None:
        meeting = self.deps.resolve_meeting_details(context)
        if not (meeting.get("id") or meeting.get("conversationId")):
            self._logger.warning("No meeting id found for recordings-find command.")
            return

        delegated_token = await self._get_delegated_token(
            context,
            self.deps.auth_handler_id,
            "Please sign in (Recordings connection) so I can fetch recordings with delegated Graph permissions.",
        )
        if not delegated_token:
            return

        await self.deps.send_typing(context)

        try:
            online_meeting_id = await self.deps.get_online_meeting_id(context)
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
            self._logger.exception("Failed to fetch meeting recordings")
            await context.send_activity(
                f"Could not retrieve meeting recordings for {meeting.get('title') or 'meeting'}: {getattr(err, 'message', str(err))}"
            )
            return

        await self._handle_recordings_list(
            context,
            turn_state,
            recordings=recordings,
            meeting=meeting,
            delegated_token=delegated_token,
            transcribe_latest=True,
        )

    async def _get_token_proactively(
        self,
        *,
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
                handler = self.deps.app.auth._resolve_handler(handler_id)
                flow, _ = await handler._load_flow(proactive_context)
                token_response = await flow.get_user_token()
                token_holder["token"] = getattr(token_response, "token", None)
            except Exception as err:
                message = getattr(err, "message", None) or str(err)
                self._logger.warning(
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

        try:
            await self.deps.adapter.continue_conversation(
                self.deps.bot_app_id, continuation, callback
            )
        except Exception as err:
            self._logger.warning(
                "Proactive token check conversation failed (handler=%s): %s",
                handler_id,
                getattr(err, "message", None) or str(err),
            )

        return token_holder["token"]

    async def _get_meeting_organizer_identity(
        self,
        context: TurnContext,
    ) -> dict[str, str | None]:
        meeting_info = await TeamsInfo.get_meeting_info(context)
        organizer_obj = getattr(meeting_info, "organizer", None) or {}
        return {
            "id": getattr(organizer_obj, "id", None),
            "aad_object_id": getattr(organizer_obj, "aadObjectId", None),
        }

    async def _get_organizer_delegated_token_from_cache(
        self,
        context: TurnContext,
    ) -> str | None:
        if not self.deps.is_meeting_conversation(context):
            return None

        try:
            organizer = await self._get_meeting_organizer_identity(context)
        except Exception as err:
            self._logger.warning(
                "Unable to resolve meeting organizer for subscription: %s",
                getattr(err, "message", str(err)),
            )
            return None

        organizer_aad = organizer.get("aad_object_id")
        organizer_id = organizer.get("id")
        if not organizer_aad and not organizer_id:
            self._logger.info(
                "Organizer identity missing; skipping delegated token fetch for subscription."
            )
            return None

        conv_ref = await note_taker_store.fetch_organizer_conversation_reference(
            organizer_aad=organizer_aad, bot_app_id=self.deps.bot_app_id
        )
        if not conv_ref:
            self._logger.info(
                "No organizer personal conversation reference available for subscription token fetch."
            )
            return None

        return await self._get_token_proactively(
            conv_ref=conv_ref,
            handler_id=self.deps.auth_handler_id,
            aad_object_id=organizer_aad,
            user_id=organizer_id,
            tenant_id=self.deps.bot_tenant_id,
            notify_if_missing=False,
        )

    async def _subscribe_to_recording_notifications(self, context: TurnContext) -> None:
        webhook_url = resolve_recordings_ready_webhook_url()
        if not webhook_url:
            self._logger.warning(
                "[teams note-taker] recordings-ready webhook URL not configured; skipping subscription."
            )
            return

        meeting = self.deps.resolve_meeting_details(context)
        chat_id = meeting.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))

        online_meeting_id = await self.deps.get_online_meeting_id(context)
        if not online_meeting_id:
            self._logger.info(
                "[teams note-taker] cannot create recording subscription; missing online meeting id."
            )
            return

        # Skip if there's already an active, non-expired subscription for this meeting.
        if chat_id and bot_id:
            try:
                async with async_session_maker() as session:
                    existing = await session.scalar(
                        select(TeamsMeeting).where(
                            TeamsMeeting.chat_id == chat_id,
                            TeamsMeeting.bot_id == bot_id,
                            TeamsMeeting.subscription_is_active.is_(True),
                            TeamsMeeting.subscription_expires_at
                            > dt.datetime.now(dt.timezone.utc),
                        )
                    )
                if existing is not None:
                    self._logger.info(
                        "[teams note-taker] active subscription %s already exists for chat %s; skipping.",
                        existing.subscription_id,
                        chat_id,
                    )
                    return
            except Exception:
                self._logger.debug(
                    "[teams note-taker] failed to check existing subscription; proceeding with creation.",
                    exc_info=True,
                )

        delegated_token = await self._get_organizer_delegated_token_from_cache(context)
        if not delegated_token:
            self._logger.info(
                "[teams note-taker] organizer delegated token unavailable; cannot create recording subscription."
            )
            await context.send_activity(
                "Cannot create recording subscription because the organizer's authentication token is not available."
            )
            return

        lifecycle_webhook = resolve_recordings_lifecycle_webhook_url()

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
        (
            subscription_id,
            expiration_dt,
            error_message,
        ) = await create_and_persist_recordings_ready_subscription(
            delegated_token=delegated_token,
            online_meeting_id=online_meeting_id,
            chat_id=chat_id,
            bot_id=bot_id,
            notification_url=webhook_url,
            lifecycle_notification_url=lifecycle_webhook,
            subscription_conversation_reference=conv_ref,
            expiration=now + dt.timedelta(hours=4),
        )
        if error_message:
            prefix = (
                ""
                if error_message.lower().startswith("recording subscription")
                else "Recording subscription failed: "
            )
            await context.send_activity(f"{prefix}{error_message}")
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

    async def _handle_view_transcript(
        self,
        context: TurnContext,
        *,
        job_id: str,
    ) -> None:
        """Send the stored transcript for a transcription job."""
        try:
            async with async_session_maker() as session:
                stmt = select(
                    Transcription.full_text,
                    Transcription.filename,
                    Transcription.status,
                ).where(Transcription.file_id == job_id)
                result = await session.execute(stmt)
                row = result.first()
        except Exception:
            self._logger.exception("Failed to fetch transcript for job %s", job_id)
            await context.send_activity("Failed to fetch transcript. Please try again.")
            return

        if not row:
            await context.send_activity(f"No transcription found for job `{job_id}`.")
            return

        full_text = row.full_text
        status = row.status or "unknown"
        filename = row.filename or job_id

        if not full_text:
            await context.send_activity(
                f"Transcription `{filename}` (status: {status}) has no text content."
            )
            return

        title = filename.rsplit(".", 1)[0] if "." in filename else filename
        max_chars = 4000
        snippet = full_text[:max_chars]
        suffix = "..." if len(full_text) > max_chars else ""
        await self.deps.send_expandable_section(
            context,
            title=f"Transcript: {title}",
            content=f"{snippet}{suffix}",
            preserve_newlines=True,
        )

    async def _handle_my_meetings(
        self,
        context: TurnContext,
    ) -> None:
        """List processed meetings for the current user from Magnet's database."""
        user_info = self.deps.resolve_user_info(context)
        aad_object_id: str | None = user_info.get("aad_object_id")
        if not aad_object_id:
            await context.send_activity(
                "Could not determine your identity. Please sign in first with /sign-in."
            )
            return

        try:
            async with async_session_maker() as session:
                stmt = (
                    select(
                        Transcription.file_id,
                        Transcription.filename,
                        Transcription.status,
                        Transcription.duration_seconds,
                        Transcription.created_at,
                        Transcription.meeting_id,
                    )
                    .where(Transcription.initiated_by == aad_object_id)
                    .order_by(desc(Transcription.created_at))
                    .limit(10)
                )
                result = await session.execute(stmt)
                rows = result.all()
        except Exception:
            self._logger.exception(
                "Failed to fetch meetings for user %s", aad_object_id
            )
            await context.send_activity(
                "Failed to fetch your meetings. Please try again later."
            )
            return

        if not rows:
            await context.send_activity(
                "No processed meetings found yet. "
                "Meetings will appear here after the bot has transcribed a recording."
            )
            return

        meetings = [
            {
                "file_id": row.file_id,
                "filename": row.filename,
                "status": row.status,
                "duration_seconds": row.duration_seconds,
                "created_at": row.created_at,
                "meeting_id": row.meeting_id,
            }
            for row in rows
        ]

        card = create_my_meetings_card(meetings)
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        activity = Activity(
            type="message",
            attachments=[attachment],
        )
        await context.send_activity(activity)
