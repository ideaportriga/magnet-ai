from __future__ import annotations

import logging
from typing import Any, override
from urllib.parse import urlparse

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.observability import observability_context, observe

from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from .web_models import WebRuntimeConfig
from .web_sync import WebSyncPipeline

logger = logging.getLogger(__name__)


class WebDataSource(AbstractDataSource):
    """Web scraper source for Knowledge Graph.

    Fetches HTML pages from a configured URL, extracts text content,
    and optionally follows links within the same domain.
    """

    LISTING_QUEUE_MAX = 0  # Unbounded: listing can self-enqueue discovered links
    CONTENT_FETCH_QUEUE_MAX = 100
    DOCUMENT_PROCESSING_QUEUE_MAX = 20

    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 2
    DOCUMENT_PROCESSING_WORKERS = 2

    HTTP_CONCURRENCY = 5

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.WEB:
            raise ValueError("Source must be a Web source")
        super().__init__(source)

    @override
    @observe(name="Sync Web source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Scrape web pages and ingest them into the Knowledge Graph."""

        logger.info(
            "Web sync started",
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        cfg = self._get_sync_config()
        embedding_model = await self._require_embedding_model(db_session)

        observability_context.update_current_span(
            input={
                "source_id": str(self.source.id),
                "url": cfg.url,
                "follow_links": cfg.follow_links,
                "max_depth": cfg.max_depth,
                "max_pages": cfg.max_pages,
                "css_selector": cfg.css_selector,
            }
        )

        pipeline = WebSyncPipeline(
            source=self,
            pipeline_config=SyncPipelineConfig(
                name="web",
                listing_queue_max=int(self.LISTING_QUEUE_MAX),
                content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                document_processing_queue_max=int(self.DOCUMENT_PROCESSING_QUEUE_MAX),
                listing_workers=max(1, int(self.LISTING_WORKERS)),
                content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                document_processing_workers=max(
                    1, int(self.DOCUMENT_PROCESSING_WORKERS)
                ),
                semaphores={"http": int(self.HTTP_CONCURRENCY)},
            ),
            web_config=cfg,
            embedding_model=embedding_model,
        )

        try:
            counters = await pipeline.run()
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Web sync failed",
                extra={
                    "graph_id": str(self.source.graph_id),
                    "source_id": str(self.source.id),
                    "error": e,
                },
            )
            raise

        await self._finalize(db_session, counters=counters)

        summary = {
            "source_id": str(self.source.id),
            "url": cfg.url,
            "follow_links": cfg.follow_links,
            "max_depth": cfg.max_depth,
            "max_pages": cfg.max_pages,
            "documents_created": counters.content_changed,
            "documents_metadata_updated_only": counters.metadata_only_updated,
            "documents_unchanged": counters.unchanged_skipped,
            "documents_failed": counters.failed,
            "documents_deleted": counters.deleted,
            "total_in_source": counters.total_found,
            "status": self.source.status,
            "last_sync_at": self.source.last_sync_at,
        }

        logger.info("Web sync completed", extra=summary)
        observability_context.update_current_span(output=summary)
        return summary

    def _get_sync_config(self) -> WebRuntimeConfig:
        cfg = self.source.config or {}

        url = str(cfg.get("url") or "").strip()
        if not url:
            raise ClientException("URL is required in source.config.url")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ClientException(f"Invalid URL scheme: {url}")
        if not parsed.netloc:
            raise ClientException(f"Invalid URL: {url}")

        follow_links = bool(cfg.get("follow_links", False))
        max_depth = int(cfg.get("max_depth", 2))
        max_pages = int(cfg.get("max_pages", 100))
        css_selector = cfg.get("css_selector") or None

        # Clamp values
        max_depth = max(1, min(max_depth, 10))
        max_pages = max(1, min(max_pages, 1000))

        return WebRuntimeConfig(
            url=url,
            follow_links=follow_links,
            max_depth=max_depth,
            max_pages=max_pages,
            css_selector=css_selector,
            allowed_domain=parsed.netloc,
        )
