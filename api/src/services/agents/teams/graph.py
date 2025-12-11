import datetime as dt
from typing import Any
from urllib.parse import quote
import asyncio

import httpx
from logging import getLogger

logger = getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


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


async def fetch_chat_meeting_info(client: GraphClient, chat_id: str) -> dict[str, Any]:
    """Fetch onlineMeetingInfo for a Teams chat."""
    logger.info("fetch_chat_meeting_info chatId=%s", chat_id)
    encoded_chat_id = quote(chat_id, safe="")
    path = f"/chats/{encoded_chat_id}"
    data = await client.get_json(path, params={"$select": "onlineMeetingInfo"})
    info = data.get("onlineMeetingInfo") or {}
    logger.info("fetch_chat_meeting_info info=%s", info)
    return info


async def resolve_meeting_id_from_join_url(
    client: GraphClient, join_url: str | None
) -> str | None:
    """Resolve an online meeting ID from its join URL."""
    if not join_url:
        return None

    escaped_url = join_url.replace("'", "''")
    base_path = "/me/onlineMeetings"

    try:
        response = await client.get_json(
            base_path, params={"$filter": f"JoinWebUrl eq '{escaped_url}'"}
        )
        values = response.get("value") or []
        match = values[0] if values else None
        meeting_id = match.get("id") if isinstance(match, dict) else None
        if meeting_id:
            logger.info(
                "Resolved meeting id from joinUrl joinUrl=%s meetingId=%s",
                join_url,
                meeting_id,
            )
            return meeting_id
        return None
    except httpx.HTTPStatusError as err:
        body = None
        try:
            body = err.response.json()
        except Exception:
            body = err.response.text
        logger.warning(
            "resolve_meeting_id_from_join_url failed status=%s code=%s message=%s raw=%s",
            getattr(err.response, "status_code", None),
            body.get("error", {}).get("code") if isinstance(body, dict) else None,
            body.get("error", {}).get("message")
            if isinstance(body, dict)
            else str(err),
            body if isinstance(body, dict) else None,
        )
        return None
    except Exception as err:
        logger.warning("resolve_meeting_id_from_join_url failed: %s", err)
        return None


async def resolve_meeting_id(
    client: GraphClient, chat_id: str | None, join_url: str | None
) -> str | None:
    """Resolve a meeting ID using chat metadata and/or join URL."""
    resolved_join_url = join_url
    if not resolved_join_url and chat_id:
        info = await fetch_chat_meeting_info(client, chat_id)
        join_web_url = info.get("joinWebUrl") if isinstance(info, dict) else None
        if join_web_url:
            resolved_join_url = join_web_url

    if resolved_join_url:
        try:
            return await resolve_meeting_id_from_join_url(client, resolved_join_url)
        except Exception as exc:  # defensive: log and keep going
            logger.warning(
                "Failed to resolve meeting id from joinUrl: %s",
                getattr(exc, "message", str(exc)),
            )

    return None


async def get_recording_file_size(content_url: str, token: str) -> int | None:
    if not content_url:
        return None

    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            range_headers = {**headers, "Range": "bytes=0-0"}
            get_resp = await client.get(content_url, headers=range_headers)
            get_resp.raise_for_status()

            content_range = get_resp.headers.get("Content-Range")
            if content_range and "/" in content_range:
                total_size = content_range.split("/")[-1]
                if total_size.isdigit():
                    return int(total_size)

            content_length = get_resp.headers.get("Content-Length")
            if content_length and content_length.isdigit():
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


async def fetch_meeting_recordings(
    *,
    client: GraphClient,
    join_url: str | None = None,
    chat_id: str | None = None,
    add_size: bool = False,
    content_token: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch recordings for a meeting, resolving meeting ID when necessary."""

    meeting_identifier = await resolve_meeting_id(client, chat_id, join_url)

    if meeting_identifier:
        try:
            logger.info("fetch_meeting_recordings meetingId=%s", meeting_identifier)
            encoded_meeting_id = quote(meeting_identifier, safe="")
            base_path = f"/me/onlineMeetings/{encoded_meeting_id}"
            recordings = await fetch_recordings(
                client, meeting_identifier, base_path=base_path
            )

            if add_size and content_token:

                async def _attach_size(rec: dict) -> None:
                    url = rec.get("contentUrl")
                    if url:
                        rec["size"] = await get_recording_file_size(url, content_token)

                await asyncio.gather(*(_attach_size(r) for r in recordings))

            logger.info(
                "Graph recordings fetched meetingId=%s recordingsCount=%d",
                meeting_identifier,
                len(recordings),
            )
            return recordings

        except httpx.HTTPStatusError as err:
            error_code = None
            try:
                body = err.response.json() if err.response is not None else {}
                error_code = (
                    body.get("error", {}).get("code")
                    if isinstance(body, dict)
                    else None
                )
            except Exception:
                body = None
            logger.warning(
                "Graph artifacts attempt failed meetingId=%s statusCode=%s code=%s message=%s",
                meeting_identifier,
                getattr(err.response, "status_code", None),
                error_code,
                str(err),
            )
            raise

    return []


__all__ = [
    "create_graph_client_with_token",
    "fetch_meeting_recordings",
]
