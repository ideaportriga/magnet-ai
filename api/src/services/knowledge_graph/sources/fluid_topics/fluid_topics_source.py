import logging
from typing import Any, override

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.base import get_knowledge_source_settings
from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.observability import observability_context, observe

from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from .fluid_topics_models import FluidTopicsRuntimeConfig
from .fluid_topics_sync import FluidTopicsSyncPipeline

logger = logging.getLogger(__name__)


class FluidTopicsSource(AbstractDataSource):
    """Fluid Topics source for Knowledge Graph.

    The Fluid Topics Search API can return multiple entry types; currently following types are supported:
    - DOCUMENT: file-based content (often PDFs) ingested as standalone documents.
    - TOPIC: HTML topic content ingested as chunks, grouped by mapId into a single document.

    Concurrency model:
    - Three queues: page fetch -> topic/file fetch -> document processing
    - Two semaphores:
      - FLUID_API_CONCURRENCY: caps *all* Fluid Topics gateway HTTP calls
      - PDF_FETCH_CONCURRENCY: caps PDF download workload (pdf-api-url + file bytes)
    """

    # Search paging
    SEARCH_PER_PAGE = 50
    SEARCH_TIMEOUT_S = 30.0

    # Global HTTP limits
    FLUID_API_CONCURRENCY = 1
    PDF_FETCH_CONCURRENCY = 3

    # Queues
    LISTING_QUEUE_MAX = 1
    CONTENT_FETCH_QUEUE_MAX = 1000
    DOCUMENT_PROCESSING_QUEUE_MAX = 10

    # Workers per queue
    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 1
    DOCUMENT_PROCESSING_WORKERS = 5

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.FLUID_TOPICS:
            raise ValueError("Source must be a Fluid Topics source")
        super().__init__(source)

    @override
    @observe(name="Sync Fluid Topics source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Synchronize documents/topics from Fluid Topics into the Knowledge Graph."""

        logger.info(
            "Fluid Topics sync started",
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        cfg = self._get_sync_config()
        embedding_model = await self._require_embedding_model(db_session)

        observability_context.update_current_span(
            input={"source_id": str(self.source.id), "filters": cfg.filters}
        )

        pipeline = FluidTopicsSyncPipeline(
            source=self,
            pipeline_config=SyncPipelineConfig(
                name="fluid_topics",
                listing_queue_max=int(self.LISTING_QUEUE_MAX),
                content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                document_processing_queue_max=int(self.DOCUMENT_PROCESSING_QUEUE_MAX),
                listing_workers=max(1, int(self.LISTING_WORKERS)),
                content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                document_processing_workers=max(
                    1, int(self.DOCUMENT_PROCESSING_WORKERS)
                ),
                semaphores={
                    "fluid_api": int(self.FLUID_API_CONCURRENCY),
                    "pdf_fetch": int(self.PDF_FETCH_CONCURRENCY),
                },
            ),
            fluid_topics_config=cfg,
            embedding_model=embedding_model,
        )

        try:
            counters = await pipeline.run()
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Fluid Topics sync failed",
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
            "synced": counters.synced,
            "failed": counters.failed,
            "skipped": counters.skipped,
            "total_found": counters.total_found,
            "status": self.source.status,
            "last_sync_at": self.source.last_sync_at,
        }

        logger.info("Fluid Topics sync completed", extra=summary)

        observability_context.update_current_span(output=summary)

        return summary

    def _get_sync_config(self) -> FluidTopicsRuntimeConfig:
        """Merge provider/env defaults with per-source overrides."""

        cfg = self.source.config or {}
        knowledge_settings = get_knowledge_source_settings()

        filters = cfg.get("filters") or []
        if not isinstance(filters, list):
            raise ClientException("Fluid Topics filters configuration must be a list")

        cfg = FluidTopicsRuntimeConfig(
            api_key=cfg.get("api_key") or knowledge_settings.FLUID_TOPICS_API_KEY,
            search_api_url=cfg.get("search_api_url")
            or knowledge_settings.FLUID_TOPICS_SEARCH_API_URL,
            pdf_api_url=cfg.get("pdf_api_url")
            or knowledge_settings.FLUID_TOPICS_PDF_API_URL,
            map_content_url_template=cfg.get("map_content_url")
            or knowledge_settings.FLUID_TOPICS_MAP_CONTENT,
            map_toc_url_template=cfg.get("map_toc_url")
            or knowledge_settings.FLUID_TOPICS_MAP_TOC,
            map_structure_url_template=cfg.get("map_structure_url")
            or knowledge_settings.FLUID_TOPICS_MAP_STRUCTURE,
            filters=filters,
        )

        if not cfg.api_key or not cfg.search_api_url:
            raise ClientException(
                "FLUID_TOPICS_API_KEY or FLUID_TOPICS_SEARCH_API_URL is missing in configuration or environment."
            )

        if not cfg.map_content_url_template:
            logger.warning(
                "FLUID_TOPICS_MAP_CONTENT is not configured; TOPIC entries will be skipped."
            )
        if not cfg.map_toc_url_template:
            logger.warning(
                "FLUID_TOPICS_MAP_TOC is not configured; TOPIC entries will be skipped."
            )
        if not cfg.map_structure_url_template:
            logger.warning(
                "FLUID_TOPICS_MAP_STRUCTURE is not configured; TOPIC entries will not have map metadata."
            )

        if not cfg.pdf_api_url:
            logger.warning(
                "FLUID_TOPICS_PDF_API_URL is not configured; DOCUMENT entries will be skipped."
            )

        logger.info(
            "Sync config: search_per_page=%s fluid_api_concurrency=%s pdf_fetch_concurrency=%s ",
            self.SEARCH_PER_PAGE,
            self.FLUID_API_CONCURRENCY,
            self.PDF_FETCH_CONCURRENCY,
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        return cfg
