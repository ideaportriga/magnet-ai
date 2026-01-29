import datetime as dt
from typing import Any

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo

from core.db.models.teams import TeamsMeeting, TeamsUser
from core.db.session import async_session_maker
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .teams_user_store import normalize_bot_id


def _is_meeting_conversation(context: TurnContext) -> bool:
    activity = getattr(context, "activity", None)
    conversation = getattr(activity, "conversation", None)
    conversation_type = getattr(conversation, "conversation_type", None)
    return conversation_type == "groupChat"


def _resolve_meeting_details(context: TurnContext) -> dict[str, Any]:
    activity = getattr(context, "activity", None)
    channel_data = getattr(activity, "channel_data", None) or {}
    conversation = getattr(activity, "conversation", None)
    meeting_data = channel_data.get("meeting") or {}
    return {
        "id": meeting_data.get("id"),
        "conversationId": getattr(conversation, "id", None),
        "title": meeting_data.get("title") or meeting_data.get("subject"),
    }


def _resolve_user_info(context: TurnContext) -> dict[str, Any]:
    activity = getattr(context, "activity", None)
    from_user = getattr(activity, "from_property", None) or getattr(
        activity, "from", None
    )
    conversation = getattr(activity, "conversation", None)

    aad_object_id = getattr(from_user, "aad_object_id", None)
    user_id = getattr(from_user, "id", None)
    display_name = getattr(from_user, "name", None) or getattr(
        from_user, "display_name", None
    )

    return {
        "id": user_id,
        "aad_object_id": aad_object_id,
        "name": display_name,
        "conversation_type": getattr(conversation, "conversation_type", None),
    }


async def _get_online_meeting_id(context: TurnContext) -> str | None:
    meeting_info = await TeamsInfo.get_meeting_info(context)
    details = getattr(meeting_info, "details", None) or {}
    return getattr(details, "ms_graph_resource_id", None)


async def get_meeting_account_info(
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
    except Exception:
        return (None, None, None)


async def get_meeting_account_id(
    context: TurnContext, meeting_id: str | None
) -> str | None:
    account_id, _account_name, _settings_system_name = await get_meeting_account_info(
        context, meeting_id
    )
    return account_id


async def upsert_teams_meeting_record(
    context: TurnContext, *, is_bot_installed: bool
) -> None:
    """Upsert Teams meeting state when the bot is added or removed."""
    if not _is_meeting_conversation(context):
        return

    meeting = _resolve_meeting_details(context)
    meeting_id = meeting.get("id")
    chat_id = meeting.get("conversationId")
    if not chat_id:
        return

    bot_id = normalize_bot_id(
        getattr(
            getattr(getattr(context, "activity", None), "recipient", None), "id", None
        )
    )

    online_meeting_id: str | None = None
    try:
        online_meeting_id = await _get_online_meeting_id(context)
    except Exception:
        online_meeting_id = None

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

    async with async_session_maker() as session:
        try:
            await session.execute(stmt)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def fetch_organizer_conversation_reference(
    *, organizer_aad: str, bot_app_id: str
) -> dict | None:
    if not organizer_aad or not bot_app_id:
        return None

    normalized = normalize_bot_id(bot_app_id)
    async with async_session_maker() as session:
        stmt = (
            select(TeamsUser.conversation_reference)
            .where(
                TeamsUser.bot_id == normalized, TeamsUser.aad_object_id == organizer_aad
            )
            .order_by(TeamsUser.last_seen_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def lookup_conversation_reference_by_user_hint(
    session,
    *,
    bot_app_id: str | None,
    user_hint: str,
) -> dict | None:
    """Try to find a TeamsUser conversation reference by either AAD or Teams user id."""
    if not user_hint or not bot_app_id:
        return None

    normalized = normalize_bot_id(bot_app_id)
    stmt = (
        select(TeamsUser.conversation_reference)
        .where(
            or_(
                TeamsUser.aad_object_id == user_hint,
                TeamsUser.teams_user_id == user_hint,
            ),
            TeamsUser.bot_id == normalized,
        )
        .order_by(TeamsUser.last_seen_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().first()
