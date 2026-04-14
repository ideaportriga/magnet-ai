from __future__ import annotations

import logging
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, override
from urllib.parse import urljoin, urlparse
from uuid import UUID

import httpx
from bs4 import BeautifulSoup

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .web_models import (
    WebContentFetchTask,
    WebListingTask,
    WebProcessDocumentTask,
    WebRuntimeConfig,
    WebSharedSyncState,
)

if TYPE_CHECKING:
    from .web_source import WebDataSource

logger = logging.getLogger(__name__)

WebPipelineContext = SyncPipelineContext[
    WebListingTask, WebContentFetchTask, WebProcessDocumentTask
]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def normalize_url(url: str) -> str:
    """Strip fragments and normalize a URL for deduplication."""
    parsed = urlparse(url)
    # Rebuild without fragment; keep query for uniqueness
    path = parsed.path.rstrip("/") or "/"
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def extract_page_content(html: str, css_selector: str | None = None) -> tuple[str, str]:
    """Extract (title, text_content) from an HTML string.

    If *css_selector* is given, content is extracted from matching elements.
    Otherwise falls back through ``<main>``, ``<article>``, ``<body>``.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = "Untitled"
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    else:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

    # Content area
    content_area = None
    if css_selector:
        elements = soup.select(css_selector)
        if elements:
            # Combine text from all matching elements
            texts: list[str] = []
            for el in elements:
                for tag in el(["script", "style", "nav", "footer"]):
                    tag.decompose()
                texts.append(el.get_text(separator="\n", strip=True))
            text = "\n\n".join(t for t in texts if t)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return title, "\n".join(lines)

    content_area = soup.find("main") or soup.find("article") or soup.find("body")

    if not content_area:
        return title, ""

    for tag in content_area(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = content_area.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return title, "\n".join(lines)


def extract_links(html: str, base_url: str, allowed_domain: str) -> list[str]:
    """Extract, resolve, and filter links from HTML to same-domain pages."""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        absolute = urljoin(base_url, href)
        normalized = normalize_url(absolute)
        parsed = urlparse(normalized)

        # Only follow http(s) links within allowed domains
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc != allowed_domain:
            continue
        if normalized in seen:
            continue

        # Skip obvious non-page resources
        ext = PurePath(parsed.path).suffix.lower()
        if ext in (
            ".pdf",
            ".zip",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".css",
            ".js",
            ".xml",
            ".json",
            ".mp4",
            ".mp3",
            ".wav",
        ):
            continue

        seen.add(normalized)
        links.append(normalized)

    return links


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class WebSyncPipeline(
    SyncPipeline[WebListingTask, WebContentFetchTask, WebProcessDocumentTask]
):
    """Web scraper pipeline: list URLs -> fetch & store -> chunk & embed."""

    def __init__(
        self,
        source: "WebDataSource",
        pipeline_config: SyncPipelineConfig,
        web_config: WebRuntimeConfig,
        embedding_model: str,
    ):
        super().__init__(config=pipeline_config)
        self._source = source
        self._graph_uuid = (
            source.source.graph_id
            if isinstance(source.source.graph_id, UUID)
            else UUID(str(source.source.graph_id))
        )
        self._graph_id = str(self._graph_uuid)
        self._source_id = str(source.source.id)
        self._web_config = web_config
        self._embedding_model = embedding_model
        self._state = WebSharedSyncState()
        # Shared storage for HTML content between listing and content-fetch stages
        self._html_cache: dict[str, str] = {}

    @override
    async def bootstrap(self, ctx: WebPipelineContext) -> None:
        normalized = normalize_url(self._web_config.url)
        self._state.visited_urls.add(normalized)
        await ctx.listing_queue.put(WebListingTask(url=normalized, depth=0))

    @override
    async def run(self) -> SyncCounters:
        counters = await self._run_pipeline(
            listing_worker=self._listing_worker,
            content_fetch_worker=self._content_fetch_worker,
            document_processing_worker=self._document_processing_worker,
        )

        try:
            counters.deleted = await self.cleanup_orphaned_documents(
                graph_id=self._graph_uuid,
                source_id=self._source.source.id,
                counters=counters,
                log_extra=self._log_extra(),
            )
        except Exception as cleanup_exc:  # noqa: BLE001
            logger.error(
                "Orphaned document cleanup failed",
                extra=self._log_extra(error=str(cleanup_exc)),
            )

        return counters

    # ------------------------------------------------------------------
    # Stage 1: Listing (fetch HTML + discover links)
    # ------------------------------------------------------------------

    async def _listing_worker(self, ctx: WebPipelineContext, worker_id: int) -> None:
        logger.debug(
            "Web listing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "MagnetAI-WebScraper/1.0"},
        ) as client:
            async for task in ctx.iter_listing_tasks():
                try:
                    async with ctx.semaphore("http"):
                        response = await client.get(task.url)
                        response.raise_for_status()

                    html = response.text
                    await self.track_source_document_id(task.url)
                    await ctx.inc("total_found")

                    # Extract content for the content-fetch stage
                    title, text_content = extract_page_content(
                        html, self._web_config.css_selector
                    )

                    if text_content:
                        await ctx.content_fetch_queue.put(
                            WebContentFetchTask(
                                url=task.url,
                                title=title,
                                text_content=text_content,
                            )
                        )
                    else:
                        await ctx.inc("skipped")
                        logger.debug(
                            "Skipping page with no extractable content",
                            extra=self._log_extra(worker_id=worker_id, url=task.url),
                        )

                    # Follow links if configured
                    if (
                        self._web_config.follow_links
                        and task.depth < self._web_config.max_depth
                    ):
                        links = extract_links(
                            html, task.url, self._web_config.allowed_domain
                        )
                        for link in links:
                            async with self._state.urls_lock:
                                if link in self._state.visited_urls:
                                    continue
                                if (
                                    self._state.pages_count
                                    >= self._web_config.max_pages
                                ):
                                    break
                                self._state.visited_urls.add(link)
                                self._state.pages_count += 1

                            await ctx.listing_queue.put(
                                WebListingTask(url=link, depth=task.depth + 1)
                            )

                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "HTTP error fetching page",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            url=task.url,
                            status_code=e.response.status_code,
                        ),
                    )
                    await ctx.inc("failed")
                except httpx.RequestError as e:
                    logger.warning(
                        "Request error fetching page",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            url=task.url,
                            error=str(e),
                        ),
                    )
                    await ctx.inc("failed")
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Web listing worker failed",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            url=task.url,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        ),
                    )
                    await ctx.inc("failed")

    # ------------------------------------------------------------------
    # Stage 2: Content fetch (store document in KG)
    # ------------------------------------------------------------------

    async def _content_fetch_worker(
        self, ctx: WebPipelineContext, worker_id: int
    ) -> None:
        logger.debug(
            "Web content_fetch worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async for task in ctx.iter_content_fetch_tasks():
            async with async_session_maker() as session:
                try:
                    # Ensure filename has .html extension so content
                    # profiles with glob patterns like *.html can match.
                    doc_title = task.title or "page"
                    filename = f"{doc_title}.html"

                    content_config = await get_content_config(
                        session,
                        self._graph_uuid,
                        filename,
                        source_id=self._source_id,
                        source_type=self._source.source.type,
                    )

                    text_bytes = task.text_content.encode("utf-8")

                    result = await self.store_document(
                        session,
                        self._source.source,
                        content=text_bytes,
                        graph_id=self._graph_uuid,
                        source_document_id=task.url,
                        filename=filename,
                        external_link=task.url,
                        default_document_type="html",
                        content_config=content_config,
                    )

                    if not result.document:
                        await ctx.inc("metadata_only_updated")
                        continue

                    await ctx.inc("content_changed")

                    logger.info(
                        "Web document created/updated for processing",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            url=task.url,
                            doc_id=result.document.get("id"),
                        ),
                    )

                    extracted_text = task.text_content
                    raw_text = task.text_content
                    if result.loaded_content:
                        extracted_text = result.loaded_content.get(
                            "text", task.text_content
                        )
                        raw_text = result.loaded_content.get(
                            "raw_text", task.text_content
                        )

                    await ctx.document_processing_queue.put(
                        WebProcessDocumentTask(
                            document=result.document,
                            extracted_text=extracted_text,
                            raw_text=raw_text,
                            content_config=content_config,
                            external_link=task.url,
                        )
                    )

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Web content_fetch worker failed",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            url=task.url,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        ),
                    )
                    await ctx.inc("failed")

                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after web task failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                error=str(rb_exc),
                            ),
                        )

    # ------------------------------------------------------------------
    # Stage 3: Document processing (chunk + embed)
    # ------------------------------------------------------------------

    async def _document_processing_worker(
        self, ctx: WebPipelineContext, worker_id: int
    ) -> None:
        logger.debug(
            "Web document_processing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async for task in ctx.iter_document_processing_tasks():
            async with async_session_maker() as session:
                doc_name = str(task.document.get("name") or "").strip()
                try:
                    await self._source.process_document(
                        session,
                        task.document,
                        extracted_text=task.extracted_text,
                        raw_text=task.raw_text,
                        config=task.content_config,
                        document_title=doc_name or None,
                        external_link=task.external_link,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Failed to process web document",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            document_id=task.document.get("id"),
                            document_name=doc_name,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        ),
                    )
                    await ctx.inc("failed")
                    try:
                        if doc_name:
                            await self._source._mark_document_error(
                                session, doc_name, exc
                            )
                    except Exception as mark_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to mark web document error",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name,
                                error=str(mark_exc),
                            ),
                        )
                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after web processing failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name,
                                error=str(rb_exc),
                            ),
                        )

    def _log_extra(self, **extra: Any) -> dict[str, Any]:
        return {"graph_id": self._graph_id, "source_id": self._source_id, **extra}
