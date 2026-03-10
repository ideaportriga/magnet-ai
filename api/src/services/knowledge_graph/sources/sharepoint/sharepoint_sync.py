from __future__ import annotations

import logging
from datetime import datetime
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, override
from urllib.parse import urlparse
from uuid import UUID

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...metadata_services import accumulate_discovered_metadata_fields
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .sharepoint_models import (
    SHAREPOINT_SYSTEM_FOLDERS,
    ProcessDocumentTask,
    SharePointContentFetchTask,
    SharePointListingTask,
    SharePointRuntimeConfig,
    SharePointSharedSyncState,
)
from .sharepoint_utils import (
    create_sharepoint_context,
    download_sharepoint_file_bytes,
    fetch_sharepoint_file_list_item_fields,
    get_root_folder_server_relative_url,
    list_sharepoint_folder_children,
    normalize_server_relative_url,
)

if TYPE_CHECKING:
    from .sharepoint_source import SharePointDataSource

logger = logging.getLogger(__name__)

SharePointPipelineContext = SyncPipelineContext[
    SharePointListingTask, SharePointContentFetchTask, ProcessDocumentTask
]


class SharePointSyncPipeline(
    SyncPipeline[SharePointListingTask, SharePointContentFetchTask, ProcessDocumentTask]
):
    """SharePoint pipeline implementation (list -> download -> ingest)."""

    def __init__(
        self,
        source: "SharePointDataSource",
        pipeline_config: SyncPipelineConfig,
        sharepoint_config: SharePointRuntimeConfig,
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
        self._sharepoint_config = sharepoint_config
        self._embedding_model = embedding_model
        self._state = SharePointSharedSyncState()

    @override
    async def bootstrap(self, ctx: SharePointPipelineContext) -> None:
        root_folder = normalize_server_relative_url(
            get_root_folder_server_relative_url(self._sharepoint_config)
        )
        if not root_folder:
            return

        async with self._state.folders_lock:
            self._state.queued_folders.add(root_folder)
        await ctx.listing_queue.put(
            SharePointListingTask(folder_server_relative_url=root_folder)
        )

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

    async def _listing_worker(
        self, ctx: SharePointPipelineContext, worker_id: int
    ) -> None:
        logger.debug(
            "SharePoint listing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        sp_ctx = await create_sharepoint_context(self._sharepoint_config)

        async for task in ctx.iter_listing_tasks():
            folder_url = normalize_server_relative_url(task.folder_server_relative_url)
            if not folder_url:
                await ctx.inc("skipped")
                continue

            # Best-effort de-duplication: if a folder task is ever enqueued twice,
            # only process it once.
            async with self._state.folders_lock:
                if folder_url in self._state.processed_folders:
                    continue
                self._state.processed_folders.add(folder_url)

            try:
                async with ctx.semaphore("sharepoint"):
                    files, subfolders = await list_sharepoint_folder_children(
                        sp_ctx, folder_server_relative_url=folder_url
                    )

                # Fetch metadata for all files in this folder for intelligent sync
                for f in files:
                    await ctx.inc("total_found")

                    if f.unique_id:
                        await self.track_source_document_id(f.unique_id)

                    logger.debug(
                        "Enqueueing SharePoint file for fetch",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            source_document_id=f.unique_id,
                            file=f.name,
                        ),
                    )

                    await ctx.content_fetch_queue.put(SharePointContentFetchTask(f))

                if self._sharepoint_config.recursive:
                    for sub in subfolders:
                        sub_url = normalize_server_relative_url(sub)
                        if not sub_url:
                            continue

                        # Skip SharePoint system folders - these contain UI elements
                        # and system files that can't be downloaded (403 errors)
                        folder_name = sub_url.rstrip("/").split("/")[-1]

                        if folder_name in SHAREPOINT_SYSTEM_FOLDERS:
                            logger.debug(
                                "Skipping SharePoint system folder",
                                extra=self._log_extra(
                                    worker_id=worker_id, folder=sub_url
                                ),
                            )
                            continue

                        # De-dup at enqueue-time (so we don't flood the listing queue).
                        async with self._state.folders_lock:
                            if sub_url in self._state.queued_folders:
                                continue
                            self._state.queued_folders.add(sub_url)

                        await ctx.listing_queue.put(
                            SharePointListingTask(folder_server_relative_url=sub_url)
                        )

                logger.info(
                    "SharePoint listing completed",
                    extra=self._log_extra(
                        worker_id=worker_id,
                        folder=folder_url,
                        files=len(files),
                        subfolders=len(subfolders),
                    ),
                )

            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "SharePoint listing worker failed",
                    extra=self._log_extra(
                        worker_id=worker_id,
                        folder=folder_url,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    ),
                )
                await ctx.inc("failed")

    async def _content_fetch_worker(
        self, ctx: SharePointPipelineContext, worker_id: int
    ) -> None:
        logger.debug(
            "SharePoint content_fetch worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        sp_ctx = await create_sharepoint_context(self._sharepoint_config)

        async with async_session_maker() as session:
            async for task in ctx.iter_content_fetch_tasks():
                filename = ""
                try:
                    file_ref = task.file
                    filename = str(file_ref.name or "").strip()
                    if not filename:
                        await ctx.inc("skipped")
                        continue

                    content_config = await get_content_config(
                        session,
                        self._graph_uuid,
                        filename,
                        source_id=str(self._source.source.id),
                        source_type=self._source.source.type,
                    )
                    if not content_config:
                        await ctx.inc("skipped")
                        continue

                    # Best-effort: collect SharePoint list item fields and accumulate as
                    # "discovered metadata" for this knowledge graph. Failures here should
                    # not block ingestion.
                    source_metadata: dict[str, Any] = {}
                    file_bytes: bytes | None = None

                    # For .aspx pages, get HTML content from CanvasContent1 instead of downloading file bytes
                    is_aspx_page = filename.lower().endswith(".aspx")

                    async with ctx.semaphore("sharepoint"):
                        try:
                            source_metadata = (
                                await fetch_sharepoint_file_list_item_fields(
                                    sp_ctx,
                                    server_relative_url=file_ref.server_relative_url,
                                )
                            )
                        except Exception as meta_exc:  # noqa: BLE001
                            logger.error(
                                "Failed to fetch SharePoint file metadata",
                                extra=self._log_extra(
                                    worker_id=worker_id,
                                    doc_filename=filename or None,
                                    error=str(meta_exc),
                                    error_type=type(meta_exc).__name__,
                                ),
                            )

                        if is_aspx_page:
                            # For pages, get HTML content from CanvasContent1 property
                            from .sharepoint_utils import fetch_sharepoint_page_content

                            page_html = await fetch_sharepoint_page_content(
                                sp_ctx,
                                server_relative_url=file_ref.server_relative_url,
                            )
                            if page_html:
                                file_bytes = page_html.encode("utf-8")
                            else:
                                logger.warning(
                                    "No CanvasContent1 found for SharePoint page",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        doc_filename=filename or None,
                                    ),
                                )
                                file_bytes = b""
                        else:
                            # For documents, download file bytes normally
                            file_bytes = await download_sharepoint_file_bytes(
                                sp_ctx,
                                server_relative_url=file_ref.server_relative_url,
                            )

                    if not file_bytes:
                        await ctx.inc("skipped")
                        continue

                    # Extract change tracking metadata from file ref or metadata
                    source_document_id = file_ref.unique_id
                    source_modified_at_raw = source_metadata.get(
                        "TimeLastModified"
                    ) or source_metadata.get("Modified")

                    external_link = self._build_external_link(
                        file_ref.server_relative_url
                    )

                    # Parse source_modified_at to datetime
                    source_modified_at: datetime | None = None
                    if source_modified_at_raw:
                        if isinstance(source_modified_at_raw, datetime):
                            source_modified_at = source_modified_at_raw
                        elif isinstance(source_modified_at_raw, str):
                            try:
                                source_modified_at = datetime.fromisoformat(
                                    source_modified_at_raw.replace("Z", "+00:00")
                                )
                            except Exception:  # noqa: BLE001
                                pass

                    if source_metadata:
                        try:
                            await accumulate_discovered_metadata_fields(
                                session,
                                graph_id=self._graph_uuid,
                                source_id=self._source.source.id,
                                metadata=source_metadata,
                                origin="source",
                            )
                            await session.commit()
                        except Exception as meta_db_exc:  # noqa: BLE001
                            await session.rollback()
                            logger.error(
                                "Failed to persist SharePoint discovered metadata",
                                extra=self._log_extra(
                                    worker_id=worker_id,
                                    doc_filename=filename or None,
                                    error=str(meta_db_exc),
                                    error_type=type(meta_db_exc).__name__,
                                ),
                            )

                    result = await self.store_document(
                        session,
                        self._source.source,
                        content=file_bytes,
                        graph_id=self._graph_uuid,
                        source_document_id=source_document_id,
                        filename=filename,
                        source_modified_at=source_modified_at,
                        source_metadata=source_metadata,
                        default_document_type="aspx" if is_aspx_page else "pdf",
                        content_config=content_config,
                        content_reader_context={
                            "document_url": external_link or "",
                            "site_url": self._sharepoint_config.site_url or "",
                            "server_relative_url": file_ref.server_relative_url or "",
                            "filename": filename,
                        },
                        external_link=external_link,
                    )
                    if not result.document:
                        await ctx.inc("metadata_only_updated")
                        continue

                    await ctx.inc("content_changed")

                    logger.info(
                        "SharePoint document created/updated for processing",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            doc_filename=filename,
                            doc_id=result.document.get("id"),
                            source_doc_id=source_document_id,
                        ),
                    )

                    await ctx.document_processing_queue.put(
                        ProcessDocumentTask(
                            document=result.document,
                            extracted_text=result.loaded_content["text"],
                            content_config=content_config,
                            external_link=external_link,
                        )
                    )

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "SharePoint content_fetch worker failed",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            doc_filename=filename or None,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        ),
                    )
                    await ctx.inc("failed")

                    try:
                        if filename:
                            await self._source._mark_document_error(
                                session, filename, exc
                            )
                    except Exception as mark_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to mark SharePoint document error",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                doc_filename=filename or None,
                                error=str(mark_exc),
                                error_type=type(mark_exc).__name__,
                            ),
                        )
                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after SharePoint task failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                doc_filename=filename or None,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )

    async def _document_processing_worker(
        self, ctx: SharePointPipelineContext, worker_id: int
    ) -> None:
        logger.debug(
            "SharePoint document_processing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async with async_session_maker() as session:
            async for task in ctx.iter_document_processing_tasks():
                doc_name = str(task.document.get("name") or "").strip()
                try:
                    await self._source.process_document(
                        session,
                        task.document,
                        extracted_text=task.extracted_text,
                        config=task.content_config,
                        document_title=PurePath(doc_name).stem
                        if doc_name
                        else doc_name,
                        external_link=task.external_link,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Failed to process SharePoint document",
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
                            "Failed to mark SharePoint document error during processing",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name,
                                error=str(mark_exc),
                                error_type=type(mark_exc).__name__,
                            ),
                        )
                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after SharePoint processing failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )

    def _log_extra(self, **extra: Any) -> dict[str, Any]:
        return {"graph_id": self._graph_id, "source_id": self._source_id, **extra}

    def _build_external_link(self, server_relative_url: str | None) -> str | None:
        url = str(server_relative_url or "").strip()
        if not url:
            return None
        parsed = urlparse(self._sharepoint_config.site_url or "")
        if not parsed.scheme or not parsed.netloc:
            return None
        if not url.startswith("/"):
            url = f"/{url}"
        return f"{parsed.scheme}://{parsed.netloc}{url}"
