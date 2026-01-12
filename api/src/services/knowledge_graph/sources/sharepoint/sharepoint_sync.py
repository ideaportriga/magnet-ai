from __future__ import annotations

import logging
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, override
from uuid import UUID

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...content_load_services import load_content_from_bytes
from ...metadata_services import accumulate_discovered_metadata_fields
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .sharepoint_models import (
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
        return await self._run_pipeline(
            listing_worker=self._listing_worker,
            content_fetch_worker=self._content_fetch_worker,
            document_processing_worker=self._document_processing_worker,
        )

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

                for f in files:
                    await ctx.inc("total_found")
                    await ctx.content_fetch_queue.put(
                        SharePointContentFetchTask(file=f)
                    )

                if self._sharepoint_config.recursive:
                    for sub in subfolders:
                        sub_url = normalize_server_relative_url(sub)
                        if not sub_url:
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
                    file_metadata: dict[str, Any] = {}
                    async with ctx.semaphore("sharepoint"):
                        try:
                            file_metadata = (
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

                        file_bytes = await download_sharepoint_file_bytes(
                            sp_ctx,
                            server_relative_url=file_ref.server_relative_url,
                        )

                    if file_metadata:
                        try:
                            await accumulate_discovered_metadata_fields(
                                session,
                                graph_id=self._graph_uuid,
                                source_id=self._source.source.id,
                                metadata=file_metadata,
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

                    content = load_content_from_bytes(file_bytes, content_config)
                    total_pages = content["metadata"].get("total_pages")

                    document = await self._source.create_document_for_source(
                        session,
                        filename=filename,
                        total_pages=total_pages,
                        file_metadata=content.get("metadata")
                        if isinstance(content, dict)
                        else None,
                        source_metadata=file_metadata,
                        default_document_type="pdf",
                        content_profile=content_config.name if content_config else None,
                    )

                    await ctx.document_processing_queue.put(
                        ProcessDocumentTask(
                            document=document,
                            extracted_text=content["text"],
                            content_config=content_config,
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
