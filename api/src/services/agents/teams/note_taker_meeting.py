from __future__ import annotations

from typing import Any

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo


def _extract_title_from_details(details: Any) -> str | None:
    if details is None:
        return None
    title = getattr(details, "title", None) or getattr(details, "subject", None)
    title = str(title or "").strip()
    return title or None


def _meeting_cache(context: TurnContext) -> dict[str, Any]:
    cache = getattr(context, "_magnet_note_taker_cache", None)
    if isinstance(cache, dict):
        return cache
    cache = {}
    setattr(context, "_magnet_note_taker_cache", cache)
    return cache


def _meeting_cache_key(
    meeting: dict[str, Any] | None, online_meeting_id: str | None
) -> str | None:
    if online_meeting_id:
        key = str(online_meeting_id).strip()
        if key:
            return f"online:{key}"
    if not isinstance(meeting, dict):
        return None
    for field in ("id", "conversationId", "meetingId", "meeting_id", "chat_id"):
        raw = meeting.get(field)
        key = str(raw or "").strip()
        if key:
            return f"meeting:{key}"
    return None


async def ensure_meeting_title(
    context: TurnContext,
    meeting: dict[str, Any] | None,
    *,
    delegated_token: str | None = None,
    online_meeting_id: str | None = None,
    meeting_details: Any | None = None,
) -> None:
    """
    Ensure `meeting["title"]` is populated (best-effort).

    Resolution order:
    1) existing meeting["title"]/["subject"]
    2) cached value on the TurnContext (avoids repeated API calls per turn)
    3) Teams SDK `TeamsInfo.get_meeting_info()` (or provided `meeting_details`) - not available in 0.6.1 get_meeting_info() yet
    4) Microsoft Graph via `get_online_meeting_title()` (requires delegated_token + online_meeting_id)
    """
    if not isinstance(meeting, dict):
        return
    if meeting.get("title") or meeting.get("subject"):
        return

    cache = _meeting_cache(context)
    cache_key = _meeting_cache_key(meeting, online_meeting_id)
    if cache_key:
        cached_title = cache.get(f"{cache_key}:title")
        if isinstance(cached_title, str) and cached_title.strip():
            meeting["title"] = cached_title.strip()
            return

    details = meeting_details
    if details is None:
        try:
            meeting_info = await TeamsInfo.get_meeting_info(context)
            details = getattr(meeting_info, "details", None) or {}
        except Exception:
            details = None

    title = _extract_title_from_details(details)
    if title:
        meeting["title"] = title
        if cache_key:
            cache[f"{cache_key}:title"] = title
        return

    if not (delegated_token and online_meeting_id):
        return

    try:
        from .graph import create_graph_client_with_token, get_online_meeting_title

        async with create_graph_client_with_token(delegated_token) as graph_client:
            title = await get_online_meeting_title(
                client=graph_client,
                online_meeting_id=str(online_meeting_id),
            )
        title = str(title or "").strip() or None
    except Exception:
        title = None

    if title:
        meeting["title"] = title
        if cache_key:
            cache[f"{cache_key}:title"] = title
