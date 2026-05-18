"""Recording listing + manual processing for NoteTakerHandlerState.

Split out of `state.py` — see NOTE_TAKER_REVISION_PLAN.md §3.2 P1-a.
Covers the user-facing recording-discovery commands:

* ``/recordings-list`` (group chat: list this meeting's recordings;
  personal chat: list recent meetings with recordings)
* ``/recordings-find`` (list + auto-transcribe latest)
* ``/process-recording <id>`` (manual single-recording trigger)
* ``process_recording_from_list`` card action (by meeting + recording id)
* summary rendering helper used by the list paths

Relies on ``self.deps`` and ``self._logger`` from the concrete class.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from sqlalchemy import desc, select

from microsoft_agents.activity import Activity, Attachment
from microsoft_agents.hosting.core import TurnContext, TurnState

from core.db.models.teams import TeamsMeeting
from core.db.session import async_session_maker

from ...graph import (
    create_graph_client_with_token,
    get_meeting_recordings,
    get_online_meeting_title,
    get_recording_by_id,
    get_recording_file_size,
    list_user_meetings_with_recordings,
)
from ...note_taker_cards import create_user_recordings_card
from ...note_taker_meeting import ensure_meeting_title
from ...note_taker_utils import (
    _build_recording_filename,
    _format_duration,
    _format_file_size,
    _format_recording_date_iso,
    _format_recording_datetime,
    _format_recording_datetime_utc_label,
)
from ...teams_user_store import normalize_bot_id


class RecordingsMixin:
    """Recording listing + manual processing handlers."""

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
