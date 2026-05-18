"""Meeting-info, in-progress check, subscription state for NoteTakerHandlerState.

Split out of `state.py` — see NOTE_TAKER_REVISION_PLAN.md §3.2 P1-a.
Covers the read-mostly meeting context surface:

* ``/meeting-info`` command renderer
* in-progress detection via TeamsInfo paged-members
* recordings-ready subscription status lookup against Graph
* recordings-ready subscription creation + persistence

Relies on ``self.deps`` and ``self._logger`` from the concrete class.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import select

from microsoft_agents.activity import ConversationReference
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.hosting.teams import TeamsInfo

from core.db.models.teams import TeamsMeeting
from core.db.session import async_session_maker

from ... import note_taker_store
from ...graph import (
    create_and_persist_recordings_ready_subscription,
    create_graph_client_with_token,
    list_subscriptions,
    pick_recordings_ready_subscription,
    resolve_recordings_lifecycle_webhook_url,
    resolve_recordings_ready_webhook_url,
)
from ...note_taker_meeting import ensure_meeting_title
from ...note_taker_utils import (
    _format_duration,
    _format_iso_datetime,
)
from ...teams_user_store import normalize_bot_id


class MeetingInfoMixin:
    """Meeting context, in-progress detection, subscription management."""

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
