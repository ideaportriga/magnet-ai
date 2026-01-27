from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, override

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.observability import observability_context, observe

from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from .sharepoint_models import SharePointRuntimeConfig
from .sharepoint_sync import SharePointSyncPipeline
from .sharepoint_utils import (
    resolve_sharepoint_auth,
    resolve_sharepoint_location,
    resolve_sharepoint_site_url,
    validate_sharepoint_runtime_config,
)

logger = logging.getLogger(__name__)


class SharePointDataSource(AbstractDataSource):
    """SharePoint Documents source for Knowledge Graph.

    This source lists files from a SharePoint document library/folder and ingests PDFs
    as Knowledge Graph documents.
    """

    # Pipeline tuning (keep conservative defaults; SharePoint often throttles)
    SHAREPOINT_CONCURRENCY = 2

    # Unbounded: listing worker can enqueue multiple subfolder tasks per folder without deadlocking.
    LISTING_QUEUE_MAX = 0
    CONTENT_FETCH_QUEUE_MAX = 200
    DOCUMENT_PROCESSING_QUEUE_MAX = 10

    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 2
    DOCUMENT_PROCESSING_WORKERS = 3

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.SHAREPOINT:
            raise ValueError("Source must be a SharePoint source")
        super().__init__(source)

    @override
    def extract_source_document_id(self, source_item: Any) -> str | None:
        """Extract SharePoint's UniqueId as the stable document identifier.

        Note: This method is not currently used by SharePoint sync pipeline.
        The pipeline directly accesses file_ref.unique_id and file_metadata["UniqueId"].
        """
        # SharePoint metadata dict format
        if isinstance(source_item, dict):
            unique_id = source_item.get("UniqueId")
            return str(unique_id) if unique_id else None

        return None

    @override
    def extract_source_modified_at(self, source_item: Any) -> datetime | None:
        """Extract SharePoint's Modified timestamp as the modification timestamp.

        Note: This method is not currently used by SharePoint sync pipeline.
        The pipeline directly accesses file_ref.time_last_modified and file_metadata["Modified"].
        """
        # SharePoint metadata dict format
        if isinstance(source_item, dict):
            modified = source_item.get("Modified")
            if isinstance(modified, datetime):
                return modified
            if isinstance(modified, str):
                try:
                    return datetime.fromisoformat(modified.replace("Z", "+00:00"))
                except Exception:  # noqa: BLE001
                    return None

        return None

    @override
    @observe(name="Sync SharePoint source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Synchronize PDF documents from SharePoint into the Knowledge Graph."""

        logger.info(
            "SharePoint sync started",
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
                "site_url": cfg.site_url,
                "library": cfg.library,
                "folder": cfg.folder,
                "recursive": cfg.recursive,
            }
        )

        pipeline = SharePointSyncPipeline(
            source=self,
            pipeline_config=SyncPipelineConfig(
                name="sharepoint",
                listing_queue_max=int(self.LISTING_QUEUE_MAX),
                content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                document_processing_queue_max=int(self.DOCUMENT_PROCESSING_QUEUE_MAX),
                listing_workers=max(1, int(self.LISTING_WORKERS)),
                content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                document_processing_workers=max(
                    1, int(self.DOCUMENT_PROCESSING_WORKERS)
                ),
                semaphores={"sharepoint": int(self.SHAREPOINT_CONCURRENCY)},
            ),
            sharepoint_config=cfg,
            embedding_model=embedding_model,
        )

        try:
            counters = await pipeline.run()
        except Exception as e:  # noqa: BLE001
            logger.error(
                "SharePoint sync failed",
                extra={
                    "graph_id": str(self.source.graph_id),
                    "source_id": str(self.source.id),
                    "error": e,
                },
            )
            raise

        await self._finalize(db_session, counters=counters)

        summary: dict[str, Any] = {
            # Source info
            "source_id": str(self.source.id),
            "site_url": cfg.site_url,
            "library": cfg.library,
            "folder": cfg.folder,
            "recursive": cfg.recursive,
            # Document operations breakdown
            # Note: content_changed includes both new documents and documents with changed content
            # We don't currently track new vs updated separately - both go through same pipeline
            "documents_created": counters.content_changed,  # New + content updates that needed reprocessing
            "metadata_only_updated": counters.metadata_only_updated,
            "documents_content_changed": counters.content_changed,  # Same as documents_created
            "documents_unchanged": counters.unchanged_skipped,
            "documents_failed": counters.failed,
            "documents_deleted": counters.deleted,
            # Legacy counters (for backward compatibility)
            "synced": counters.synced,  # Successfully processed (embedded)
            "failed": counters.failed,
            "skipped": counters.skipped,
            # Totals
            "total_in_source": counters.total_found,
            "total_found": counters.total_found,  # Legacy
            # Status
            "status": self.source.status,
            "last_sync_at": self.source.last_sync_at,
        }

        logger.info("SharePoint sync completed", extra=summary)
        observability_context.update_current_span(output=summary)
        return summary

    def _get_sync_config(self) -> SharePointRuntimeConfig:
        cfg = self.source.config or {}

        site_url = resolve_sharepoint_site_url(cfg)
        if not site_url:
            raise ClientException("SharePoint site URL is required in source.config")

        library, folder, recursive = resolve_sharepoint_location(cfg)
        client_id, client_secret, tenant, thumbprint, private_key = (
            resolve_sharepoint_auth(cfg)
        )

        runtime_cfg = SharePointRuntimeConfig(
            site_url=site_url,
            library=library,
            folder=folder,
            recursive=recursive,
            client_id=client_id,
            client_secret=client_secret,
            tenant=tenant,
            thumbprint=thumbprint,
            private_key=private_key,
        )

        validate_sharepoint_runtime_config(runtime_cfg)
        return runtime_cfg
