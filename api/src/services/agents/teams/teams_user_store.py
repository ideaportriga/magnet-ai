from __future__ import annotations

import datetime as dt
from logging import getLogger
from typing import Any

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.teams import TeamsUser

logger = getLogger(__name__)


def normalize_bot_id(raw: str | None) -> str | None:
    if not raw:
        return None
    return raw[3:] if raw.startswith("28:") else raw


def _resolve_scope(raw_scope: str | None) -> str:
    if raw_scope in {"personal", "groupChat", "channel"}:
        return raw_scope
    return "personal"


async def _fetch_member_profile(
    context: TurnContext, user_id: str
) -> tuple[str | None, str | None]:
    try:
        member = await TeamsInfo.get_member(context, user_id)
        email = getattr(member, "email", None)
        upn = getattr(member, "user_principal_name", None)
        return email, upn
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Failed to fetch Teams member profile: %s", exc)
        return None, None


def _conversation_reference_from_activity(activity: Any) -> dict[str, Any]:
    """Build a serialized conversation reference snapshot from the activity."""
    try:
        reference = activity.get_conversation_reference()
        return reference.model_dump(exclude_none=True, by_alias=False)
    except Exception as exc:  # pragma: no cover - fallback path
        logger.debug("Failed to build conversation reference via helper: %s", exc)
        from_user = getattr(activity, "from_property", None) or getattr(
            activity, "from", None
        )
        conversation = getattr(activity, "conversation", None)
        recipient = getattr(activity, "recipient", None)
        channel_data = getattr(activity, "channel_data", None) or {}

        return {
            "service_url": getattr(activity, "service_url", None),
            "conversation": {"id": getattr(conversation, "id", None)},
            "channel_id": getattr(activity, "channel_id", None),
            "bot": {"id": getattr(recipient, "id", None)},
            "user": {"id": getattr(from_user, "id", None)},
            "tenant_id": (channel_data.get("tenant") or {}).get("id"),
        }


async def upsert_teams_user(session: AsyncSession, context: TurnContext) -> None:
    """
    Best-effort upsert of a Teams user for proactive messaging.

    Always updates conversation reference + last_seen_at; stores email/UPN if available.
    """
    activity = getattr(context, "activity", None)
    if not activity:
        logger.debug("Skipping Teams user upsert: missing activity on context.")
        return

    from_user = getattr(activity, "from_property", None) or getattr(
        activity, "from", None
    )
    conversation = getattr(activity, "conversation", None)
    recipient = getattr(activity, "recipient", None)
    channel_data = getattr(activity, "channel_data", None) or {}

    teams_user_id = getattr(from_user, "id", None)
    aad_object_id = getattr(from_user, "aad_object_id", None)
    display_name = getattr(from_user, "name", None) or getattr(
        from_user, "display_name", None
    )
    scope = _resolve_scope(getattr(conversation, "conversation_type", None))
    conversation_id = getattr(conversation, "id", None)
    service_url = getattr(activity, "service_url", None)
    bot_id = normalize_bot_id(getattr(recipient, "id", None))
    tenant_id = (channel_data.get("tenant") or {}).get("id")

    if not all([teams_user_id, scope, conversation_id, service_url, bot_id]):
        logger.debug(
            "Skipping Teams user upsert: missing identifiers (user_id=%s, scope=%s, "
            "conversation_id=%s, service_url=%s, bot_id=%s)",
            teams_user_id,
            scope,
            conversation_id,
            service_url,
            bot_id,
        )
        return

    conversation_reference = _conversation_reference_from_activity(activity)
    # Ensure we persist tenant id for future proactive operations if we fell back
    if tenant_id and "tenant_id" not in conversation_reference:
        conversation_reference["tenant_id"] = tenant_id
    now = dt.datetime.now(dt.timezone.utc)

    email = None
    user_principal_name = None
    email, user_principal_name = await _fetch_member_profile(context, teams_user_id)

    insert_stmt = pg_insert(TeamsUser).values(
        aad_object_id=aad_object_id,
        teams_user_id=teams_user_id,
        user_principal_name=user_principal_name,
        email=email,
        display_name=display_name,
        scope=scope,
        conversation_id=conversation_id,
        service_url=service_url,
        bot_id=bot_id,
        conversation_reference=conversation_reference,
        last_seen_at=now,
    )

    update_values: dict[str, Any] = {
        "conversation_id": conversation_id,
        "service_url": service_url,
        "bot_id": bot_id,
        "conversation_reference": conversation_reference,
        "last_seen_at": now,
        "display_name": display_name,
        "updated_at": func.now(),
    }
    if aad_object_id:
        update_values["aad_object_id"] = aad_object_id
    if email:
        update_values["email"] = email
    if user_principal_name:
        update_values["user_principal_name"] = user_principal_name

    if aad_object_id:
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[TeamsUser.aad_object_id, TeamsUser.scope, TeamsUser.bot_id],
            index_where=TeamsUser.aad_object_id.isnot(None),
            set_=update_values,
        )
    else:
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[TeamsUser.teams_user_id, TeamsUser.scope, TeamsUser.bot_id],
            set_=update_values,
        )

    await session.execute(stmt)
