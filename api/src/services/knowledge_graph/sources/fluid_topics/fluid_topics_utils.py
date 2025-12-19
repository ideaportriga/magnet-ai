from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any, Iterable, Iterator

import httpx
from html2text import HTML2Text
from litestar.exceptions import ClientException

if TYPE_CHECKING:
    from .fluid_topics_sync import FluidTopicsPipelineContext, FluidTopicsSyncPipeline

logger = logging.getLogger(__name__)


def _log_extra_from_ctx(
    pipeline: FluidTopicsSyncPipeline, **extra: Any
) -> dict[str, Any]:
    return {"graph_id": pipeline._graph_id, "source_id": pipeline._source_id, **extra}


def _extract_text_from_html(html: str) -> str:
    """Convert HTML to plain text suitable for embeddings."""

    if not isinstance(html, str) or not html.strip():
        return ""

    # Fluid Topics returns HTML fragments. Embeddings should be based on *text*, not markup,
    # so we convert HTML -> "plain-ish" text and normalize whitespace.
    try:
        h = HTML2Text()
        # Avoid wrapping lines; embeddings generally prefer raw text
        if hasattr(h, "body_width"):
            h.body_width = 0
        # Keep output more "text-like" than "markdown-like"
        if hasattr(h, "ignore_links"):
            h.ignore_links = True
        if hasattr(h, "ignore_images"):
            h.ignore_images = True
        if hasattr(h, "ignore_emphasis"):
            h.ignore_emphasis = True
        text_out = h.handle(html)
    except Exception:  # noqa: BLE001
        # Worst case: strip tags very naively
        text_out = re.sub(r"<[^>]+>", " ", html)

    # Normalize whitespace/newlines
    text_out = text_out.replace("\u200b", "")  # zero-width space
    text_out = re.sub(r"\r\n?", "\n", text_out)
    text_out = re.sub(r"\n{3,}", "\n\n", text_out)
    text_out = re.sub(r"[ \t]{2,}", " ", text_out)
    return text_out.strip()


def normalize_map_toc_payload(payload: Any) -> list[dict[str, Any]]:
    """Normalize the map TOC API payload into a list of root toc-node dicts."""

    if isinstance(payload, list):
        return [n for n in payload if isinstance(n, dict)]

    if isinstance(payload, dict):
        for key in ("toc", "entries", "items", "children", "results"):
            val = payload.get(key)
            if isinstance(val, list):
                return [n for n in val if isinstance(n, dict)]

        # Some APIs return a single root node object.
        if any(k in payload for k in ("title", "contentId", "children")):
            return [payload]

    return []


def ft_toc_to_kg_toc(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Fluid Topics toc nodes to Knowledge Graph TOC JSON.

    The Admin UI expects nodes in the shape: { name, children? } (text is optional).
    """

    out: list[dict[str, Any]] = []
    for n in nodes:
        title_val = n.get("title")
        name = str(title_val).strip() if title_val is not None else ""
        if not name:
            name = "Untitled"

        children_val = n.get("children")
        children_nodes: list[dict[str, Any]] = []
        if isinstance(children_val, list) and children_val:
            children_nodes = ft_toc_to_kg_toc(
                [c for c in children_val if isinstance(c, dict)]
            )

        node: dict[str, Any] = {"name": name}
        if children_nodes:
            node["children"] = children_nodes
        out.append(node)

    return out


def iter_ft_toc_content_nodes(
    nodes: Iterable[dict[str, Any]],
) -> Iterator[tuple[str, str]]:
    """Yield (contentId, title) for all nodes in a Fluid Topics TOC tree."""

    for node in nodes:
        if not isinstance(node, dict):
            continue

        content_id = node.get("contentId")
        title = str(node.get("title") or "").strip()
        if content_id:
            yield (str(content_id), str(title or ""))

        children = node.get("children") or []
        if isinstance(children, list) and children:
            yield from iter_ft_toc_content_nodes(
                [c for c in children if isinstance(c, dict)]
            )


def _build_ft_url_template(
    url_template: str, *, map_id: str, content_id: str | None = None
) -> str:
    """Fill a URL template containing {mapId} and optionally {contentId} placeholders."""

    try:
        if content_id is not None:
            return url_template.format(mapId=map_id, contentId=content_id)
        else:
            return url_template.format(mapId=map_id)
    except Exception:  # noqa: BLE001
        # Be resilient if the template contains other braces that `.format()` would treat
        # as placeholders. We only substitute the known Fluid Topics placeholders.
        s = url_template.replace("{mapId}", map_id)
        if content_id is not None:
            s = s.replace("{contentId}", content_id)
        return s


async def fetch_map_toc(
    pipeline: FluidTopicsSyncPipeline,
    ctx: FluidTopicsPipelineContext,
    map_id: str,
    *,
    timeout_s: float = 30.0,
):
    """Download TOC tree for a Fluid Topics map."""

    t0 = time.monotonic()
    try:
        async with ctx.semaphore("fluid_api"):
            resp = await pipeline._client.get(
                _build_ft_url_template(
                    pipeline._fluid_topics_config.map_toc_url_template, map_id=map_id
                ),
                headers={"x-api-key": pipeline._fluid_topics_config.api_key},
                timeout=timeout_s,
            )
            resp.raise_for_status()
            payload = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Fluid Topics map TOC fetch failed",
            extra=_log_extra_from_ctx(
                pipeline,
                map_id=map_id,
                status_code=exc.response.status_code,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise
    except httpx.RequestError as exc:
        logger.warning(
            "Fluid Topics map TOC fetch failed",
            extra=_log_extra_from_ctx(
                pipeline,
                map_id=map_id,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise

    logger.debug(
        "Fluid Topics map TOC fetch completed",
        extra=_log_extra_from_ctx(
            pipeline,
            map_id=map_id,
            status_code=resp.status_code,
            elapsed_ms=(time.monotonic() - t0) * 1000.0,
        ),
    )
    return payload


async def fetch_topic_content(
    pipeline: FluidTopicsSyncPipeline,
    ctx: FluidTopicsPipelineContext,
    map_id: str,
    content_id: str,
    *,
    timeout_s: float = 30.0,
) -> str:
    """Fetch a TOPIC content block."""

    t0 = time.monotonic()
    try:
        # We bound overall Fluid Topics traffic with a shared semaphore to prevent upstream throttling / rate limits
        async with ctx.semaphore("fluid_api"):
            resp = await pipeline._client.get(
                _build_ft_url_template(
                    pipeline._fluid_topics_config.map_content_url_template,
                    map_id=map_id,
                    content_id=content_id,
                ),
                headers={"x-api-key": pipeline._fluid_topics_config.api_key},
                timeout=timeout_s,
            )
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Fluid Topics topic fetch failed",
            extra=_log_extra_from_ctx(
                pipeline,
                map_id=map_id,
                content_id=content_id,
                status_code=exc.response.status_code,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise
    except httpx.RequestError as exc:
        logger.warning(
            "Fluid Topics topic fetch failed",
            extra=_log_extra_from_ctx(
                pipeline,
                map_id=map_id,
                content_id=content_id,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise

    text = _extract_text_from_html(html)
    logger.debug(
        "Fluid Topics topic fetch completed",
        extra=_log_extra_from_ctx(
            pipeline,
            map_id=map_id,
            content_id=content_id,
            status_code=resp.status_code,
            html_len=len(html or ""),
            text_len=len(text or ""),
            elapsed_ms=(time.monotonic() - t0) * 1000.0,
        ),
    )
    return text


async def download_file(
    pipeline: FluidTopicsSyncPipeline,
    ctx: FluidTopicsPipelineContext,
    filename: str,
    *,
    url_timeout_s: float = 20.0,
    file_timeout_s: float = 60.0,
) -> bytes:
    """Download file bytes for a DOCUMENT entry from Fluid Topics.

    Fluid Topics document retrieval is typically a two-step process:
    1) Call the configured `pdf_api_url` with `fileName` to get a temporary download URL
       (often a pre-signed URL) as plain text.
    2) Download the actual bytes from that returned URL.
    """

    try:
        t0 = time.monotonic()
        # 1) Get the download URL (Fluid Topics gateway)
        async with ctx.semaphore("fluid_api"):
            response = await pipeline._client.get(
                pipeline._fluid_topics_config.pdf_api_url,
                params={"fileName": filename},
                headers={"x-api-key": pipeline._fluid_topics_config.api_key},
                timeout=url_timeout_s,
            )
            response.raise_for_status()
            download_url = (response.text or "").strip()
            if not download_url:
                raise ClientException(
                    f"Fluid Topics PDF API returned empty download URL for {filename}"
                )

        # 2) Download the actual file (often a pre-signed URL; not a Fluid Topics endpoint).
        # IMPORTANT: do not log the pre-signed URL itself (it may contain credentials/tokens).
        download_host = None
        download_scheme = None
        try:
            u = httpx.URL(download_url)
            download_host = u.host
            download_scheme = u.scheme
        except Exception:  # noqa: BLE001
            pass

        async with ctx.semaphore("pdf_fetch"):
            file_response = await pipeline._client.get(
                download_url, timeout=file_timeout_s
            )
            file_response.raise_for_status()
            content = file_response.content

        logger.debug(
            "Fluid Topics file download completed",
            extra=_log_extra_from_ctx(
                pipeline,
                filename=filename,
                bytes=len(content),
                download_host=download_host,
                download_scheme=download_scheme,
                elapsed_ms=(time.monotonic() - t0) * 1000.0,
            ),
        )
        return content

    except httpx.HTTPStatusError as exc:
        host = None
        try:
            host = exc.request.url.host
        except Exception:  # noqa: BLE001
            pass
        logger.warning(
            "Fluid Topics file download failed",
            extra=_log_extra_from_ctx(
                pipeline,
                filename=filename,
                status_code=exc.response.status_code,
                request_host=host,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise ClientException(
            f"Failed to download file {filename} (HTTP {exc.response.status_code})"
        ) from exc
    except httpx.RequestError as exc:
        host = None
        try:
            host = exc.request.url.host
        except Exception:  # noqa: BLE001
            pass
        logger.warning(
            "Fluid Topics file download failed",
            extra=_log_extra_from_ctx(
                pipeline,
                filename=filename,
                request_host=host,
                error=str(exc),
                error_type=type(exc).__name__,
            ),
        )
        raise ClientException(
            f"Failed to download file {filename} (request error): {exc}"
        ) from exc
