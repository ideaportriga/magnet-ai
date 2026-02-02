import datetime as dt
from typing import Any
from urllib.parse import quote, unquote
import asyncio
import os

import httpx
from logging import getLogger

from core.db.models.teams import TeamsMeeting
from core.db.session import async_session_maker
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


def resolve_recordings_ready_webhook_url(
    *, public_base_url: str | None = None
) -> str | None:
    base_url = (
        (
            public_base_url
            if public_base_url is not None
            else os.getenv("PUBLIC_BASE_URL", "")
        )
        .strip()
        .rstrip("/")
    )
    if base_url:
        return f"{base_url}/api/user/agents/teams/webhooks/recordings-ready"
    return None


def resolve_recordings_lifecycle_webhook_url(
    *, public_base_url: str | None = None
) -> str | None:
    base_url = (
        (
            public_base_url
            if public_base_url is not None
            else os.getenv("PUBLIC_BASE_URL", "")
        )
        .strip()
        .rstrip("/")
    )
    if base_url:
        return f"{base_url}/api/user/agents/teams/webhooks/recordings-lifecycle"
    return None


def extract_meeting_id_from_notification(notification: dict[str, Any]) -> str | None:
    resource_data = notification.get("resourceData") or {}
    meeting_id = resource_data.get("meetingId")
    if meeting_id:
        return meeting_id

    resource = str(notification.get("resource") or "")
    if not resource:
        return None
    marker = "onlineMeetings("
    if marker in resource:
        start = resource.index(marker) + len(marker)
        end = resource.find(")", start)
        if end > start:
            raw = resource[start:end].strip("'\"")
            return unquote(raw)
    return None


def extract_user_from_resource(notification: dict[str, Any]) -> str | None:
    resource = str(notification.get("resource") or "")
    if not resource or "users(" not in resource:
        return None
    try:
        start = resource.index("users(") + len("users(")
        end = resource.index(")", start)
        return unquote(resource[start:end]).strip("'\"")
    except ValueError:
        return None


async def create_and_persist_recordings_ready_subscription(
    *,
    delegated_token: str,
    online_meeting_id: str,
    chat_id: str | None,
    bot_id: str | None,
    notification_url: str,
    lifecycle_notification_url: str | None,
    subscription_conversation_reference: dict[str, Any] | None,
    expiration: dt.datetime | None = None,
) -> tuple[str | None, dt.datetime | None, str | None]:
    """Create a recordings-ready Graph subscription and persist metadata into TeamsMeeting.

    Returns (subscription_id, expiration_dt, error_message).
    """
    subscription_id: str | None = None
    expiration_dt: dt.datetime | None = None

    try:
        payload = await create_recordings_ready_subscription(
            token=delegated_token,
            online_meeting_id=online_meeting_id,
            notification_url=notification_url,
            lifecycle_notification_url=lifecycle_notification_url,
            expiration=expiration,
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

        if chat_id and bot_id:
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

        return None, None, error_message

    if not chat_id or not bot_id or not subscription_id:
        return (
            subscription_id,
            expiration_dt,
            "Recording subscription not set (missing chat or subscription id).",
        )

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
                    subscription_conversation_reference=subscription_conversation_reference,
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
                        "subscription_conversation_reference": subscription_conversation_reference,
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
        return (
            subscription_id,
            expiration_dt,
            "Failed to persist recording subscription metadata.",
        )

    return subscription_id, expiration_dt, None


class GraphClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = GRAPH_BASE_URL,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not token:
            raise ValueError("A Graph access token is required to build a client.")

        headers = {"Authorization": f"Bearer {token}"}
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url, headers=headers, timeout=timeout
        )

    async def __aenter__(self) -> "GraphClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_json(
        self, url: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def create_graph_client_with_token(token: str) -> GraphClient:
    return GraphClient(token)


async def get_online_meeting_title(
    *,
    client: GraphClient,
    online_meeting_id: str,
) -> str | None:
    if not online_meeting_id:
        return None

    encoded_meeting_id = quote(str(online_meeting_id), safe="")
    online_meeting = await client.get_json(f"/me/onlineMeetings/{encoded_meeting_id}")
    if not isinstance(online_meeting, dict):
        return None

    title = str(
        online_meeting.get("subject") or online_meeting.get("title") or ""
    ).strip()
    return title or None


async def create_recordings_ready_subscription(
    *,
    token: str,
    online_meeting_id: str,
    notification_url: str,
    lifecycle_notification_url: str | None = None,
    expiration: dt.datetime | None = None,
    client_state: str = "recordings-ready",
) -> dict[str, Any]:
    if not token:
        raise ValueError("A Graph access token is required to create a subscription.")
    if not online_meeting_id:
        raise ValueError("A meeting id is required to create a subscription.")
    if not notification_url:
        raise ValueError("A notification URL is required to create a subscription.")

    expiration_dt = expiration or (
        dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=4)
    )
    expiration_iso = expiration_dt.isoformat()
    if expiration_iso.endswith("+00:00"):
        expiration_iso = expiration_iso.replace("+00:00", "Z")

    encoded_meeting_id = quote(online_meeting_id, safe="")
    resource = f"communications/onlineMeetings/{encoded_meeting_id}/recordings"
    body = {
        "changeType": "created",
        "notificationUrl": notification_url,
        "resource": resource,
        "expirationDateTime": expiration_iso,
        "clientState": client_state,
        "latestSupportedTlsVersion": "v1_2",
    }
    if lifecycle_notification_url:
        body["lifecycleNotificationUrl"] = lifecycle_notification_url

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GRAPH_BASE_URL}/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
        )
        if response.status_code >= 400:
            logger.error(
                "Graph subscription create failed status=%s body=%s",
                response.status_code,
                response.text,
            )
            response.raise_for_status()
        return response.json()


async def get_recording_file_size(content_url: str, token: str) -> int | None:
    if not content_url:
        return None

    headers = {"Authorization": f"Bearer {token}"}

    try:
        timeout = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Prefer HEAD when available.
            try:
                head_resp = await client.head(content_url, headers=headers)
                if head_resp.status_code < 400:
                    content_length = head_resp.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        return int(content_length)
            except httpx.HTTPError:
                pass

            # Fallback: a 1-byte range request, then parse Content-Range total size.
            range_headers = {**headers, "Range": "bytes=0-0"}
            async with client.stream(
                "GET", content_url, headers=range_headers
            ) as get_resp:
                get_resp.raise_for_status()

                content_range = get_resp.headers.get("Content-Range")
                if content_range and "/" in content_range:
                    total_size = content_range.split("/")[-1]
                    if total_size.isdigit():
                        return int(total_size)

                content_length = get_resp.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    # Could be "1" for range responses; still better than None.
                    return int(content_length)

            return None

    except Exception as err:
        logger.warning("Failed to get file size for recording: %s", err)
        return None


async def fetch_recordings(
    client: GraphClient,
    meeting_id: str,
    *,
    base_path: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch all recordings for the given meeting, sorted newest-first."""
    if not base_path:
        encoded_meeting_id = quote(meeting_id, safe="")
        base_path = f"/me/onlineMeetings/{encoded_meeting_id}"

    all_items: list[dict[str, Any]] = []
    url: str | None = f"{base_path}/recordings"
    first_page = True

    try:
        while url:
            request_url = url
            params = None
            if first_page and not url.startswith("http"):
                params = {"$top": 100}
            response = await client.get_json(request_url, params=params)
            items = response.get("value") or []
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    duration_seconds = None
                    started = item.get("createdDateTime")
                    ended = item.get("endDateTime")
                    if started and ended:
                        try:
                            started_dt = dt.datetime.fromisoformat(
                                started.replace("Z", "+00:00")
                            )
                            ended_dt = dt.datetime.fromisoformat(
                                ended.replace("Z", "+00:00")
                            )
                            delta_seconds = int((ended_dt - started_dt).total_seconds())
                            if delta_seconds >= 0:
                                duration_seconds = delta_seconds
                        except Exception:
                            pass

                    all_items.append(
                        {
                            "id": item.get("id"),
                            "createdDateTime": item.get("createdDateTime"),
                            "contentUrl": item.get("contentUrl")
                            or item.get("recordingContentUrl")
                            or item.get("downloadUrl"),
                            "duration": duration_seconds,
                        }
                    )

            url = response.get("@odata.nextLink") or None
            logger.debug("fetch_recordings nextLink=%s", url)
            first_page = False

        logger.debug("fetch_recordings total items=%d", len(all_items))

        def _ts(value: str | None) -> float:
            if not value:
                return 0.0
            try:
                return dt.datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                return 0.0

        all_items.sort(key=lambda item: _ts(item.get("createdDateTime")), reverse=True)
        return all_items
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            return []
        logger.error("Graph recordings fetch failed: %s", err)
        raise


async def get_recording_by_id(
    *,
    client: GraphClient,
    online_meeting_id: str,
    recording_id: str,
    # base_path: str | None = None,
) -> dict[str, Any] | None:
    if not online_meeting_id or not recording_id:
        return None

    encoded_meeting_id = quote(online_meeting_id, safe="")
    encoded_recording_id = quote(recording_id, safe="")
    # path = base_path or f"/me/onlineMeetings/{encoded_meeting_id}"
    path = f"/me/onlineMeetings/{encoded_meeting_id}"
    url = f"{path}/recordings/{encoded_recording_id}"

    try:
        return await client.get_json(url)
    except httpx.HTTPStatusError as err:
        if getattr(err.response, "status_code", None) == 404:
            return None
        logger.error(
            "Graph single recording fetch failed meetingId=%s recordingId=%s: %s",
            online_meeting_id,
            recording_id,
            err,
        )
        raise


async def get_meeting_recordings(
    *,
    client: GraphClient,
    online_meeting_id: str,
    add_size: bool = False,
    content_token: str | None = None,
) -> list[dict[str, Any]]:
    try:
        logger.info("fetch_meeting_recordings meetingId=%s", online_meeting_id)
        encoded_meeting_id = quote(online_meeting_id, safe="")
        base_path = f"/me/onlineMeetings/{encoded_meeting_id}"
        recordings = await fetch_recordings(
            client, online_meeting_id, base_path=base_path
        )

        if add_size and content_token:

            async def _add_size(rec: dict) -> None:
                url = rec.get("contentUrl")
                if url:
                    rec["size"] = await get_recording_file_size(url, content_token)

            await asyncio.gather(*(_add_size(r) for r in recordings))

            logger.info(
                "Graph recordings fetched meetingId=%s recordingsCount=%d",
                online_meeting_id,
                len(recordings),
            )
            return recordings

    except httpx.HTTPStatusError as err:
        error_code = None
        try:
            body = err.response.json() if err.response is not None else {}
            error_code = (
                body.get("error", {}).get("code") if isinstance(body, dict) else None
            )
        except Exception:
            body = None
            logger.warning(
                "Graph artifacts attempt failed meetingId=%s statusCode=%s code=%s message=%s",
                online_meeting_id,
                getattr(err.response, "status_code", None),
                error_code,
                str(err),
            )
            raise

    return []


async def list_subscriptions(client: GraphClient) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    url: str | None = "/subscriptions"
    first_page = True

    while url:
        try:
            response = await client.get_json(url)
        except httpx.HTTPStatusError as err:
            if first_page and getattr(err.response, "status_code", None) == 400:
                response = await client.get_json(url, params=None)
            else:
                raise

        page_items = response.get("value") or []
        if isinstance(page_items, list):
            for item in page_items:
                if isinstance(item, dict):
                    items.append(item)

        url = response.get("@odata.nextLink") or None
        first_page = False

    return items


def pick_recordings_ready_subscription(
    subscriptions: list[dict[str, Any]],
    *,
    online_meeting_id: str,
) -> dict[str, Any] | None:
    if not online_meeting_id:
        return None

    encoded_meeting_id = quote(online_meeting_id, safe="")
    target_resources = {
        f"communications/onlineMeetings/{encoded_meeting_id}/recordings",
        f"communications/onlineMeetings/{online_meeting_id}/recordings",
    }

    matches: list[dict[str, Any]] = []
    for item in subscriptions:
        if not isinstance(item, dict):
            continue
        resource = str(item.get("resource") or "")
        if not resource:
            continue
        if "recordings" not in resource or "onlineMeetings" not in resource:
            continue
        resource_unquoted = unquote(resource)
        if online_meeting_id not in resource_unquoted and not any(
            target in resource or target in resource_unquoted
            for target in target_resources
        ):
            continue
        client_state = item.get("clientState")
        if client_state and client_state != "recordings-ready":
            continue
        matches.append(item)

    if not matches:
        return None

    def _expires_at(item: dict[str, Any]) -> dt.datetime:
        raw = item.get("expirationDateTime") or ""
        try:
            return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

    matches.sort(key=_expires_at, reverse=True)
    return matches[0]


__all__ = [
    "create_recordings_ready_subscription",
    "create_graph_client_with_token",
    "get_recording_by_id",
    "get_meeting_recordings",
    "get_online_meeting_title",
    "list_subscriptions",
    "pick_recordings_ready_subscription",
]
