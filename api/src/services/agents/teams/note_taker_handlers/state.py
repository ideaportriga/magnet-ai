from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import desc, select

from microsoft_agents.activity import Activity, Attachment
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState

from core.db.models.transcription.transcription import Transcription
from core.db.session import async_session_maker

from .. import note_taker_store
from ..note_taker_cards import (
    create_my_meetings_card,
    create_note_taker_welcome_card,
)
from ..note_taker_files import _download_file_from_link
from ..note_taker_meeting import ensure_meeting_title
from ..note_taker_people import ManualParticipantStore
from ..note_taker_transcription import (
    run_postprocessing_pipeline,
    run_transcription_pipeline,
)
from ..note_taker_utils import extract_teams_file_attachment_url
from ..teams_user_store import normalize_bot_id
from .mixins import (
    AuthMixin,
    ConfigCardMixin,
    MeetingInfoMixin,
    RecordingsMixin,
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
    # Azure AD tenant of the Teams bot app (not our org-tenant).
    bot_azure_tenant_id: str
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


class NoteTakerHandlerState(
    AuthMixin,
    ConfigCardMixin,
    MeetingInfoMixin,
    RecordingsMixin,
):
    def __init__(self, deps: NoteTakerHandlerDeps) -> None:
        self.deps = deps
        self._logger = getLogger(__name__)

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
