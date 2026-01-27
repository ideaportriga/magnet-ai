from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, override
from urllib.parse import urlparse
from uuid import UUID

from core.db.models.knowledge_graph import docs_table_name
from core.db.session import async_session_maker
from sqlalchemy import text

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
    SHAREPOINT_SYSTEM_FOLDERS,
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

        # Orphaned document cleanup (always runs unless API failure detected)
        try:
            counters.deleted = await self._cleanup_orphaned_documents(counters)
        except Exception as cleanup_exc:  # noqa: BLE001
            logger.error(
                "Orphaned document cleanup failed",
                extra=self._log_extra(error=str(cleanup_exc)),
            )
            # Don't fail the entire sync if cleanup fails

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
                async with async_session_maker() as session:
                    for f in files:
                        await ctx.inc("total_found")

                        # Fetch metadata to enable change detection
                        file_metadata = {}
                        try:
                            async with ctx.semaphore("sharepoint"):
                                file_metadata = (
                                    await fetch_sharepoint_file_list_item_fields(
                                        sp_ctx,
                                        server_relative_url=f.server_relative_url,
                                    )
                                )
                        except Exception as meta_exc:  # noqa: BLE001
                            logger.debug(
                                "Failed to fetch SharePoint file metadata in listing phase",
                                extra=self._log_extra(
                                    worker_id=worker_id,
                                    file=f.name,
                                    error=str(meta_exc),
                                ),
                            )

                        # Extract change tracking metadata
                        # SharePoint returns "Modified" in list item fields, not "TimeLastModified"
                        unique_id = (
                            file_metadata.get("UniqueId") if file_metadata else None
                        )
                        time_last_modified = (
                            (
                                file_metadata.get("TimeLastModified")
                                or file_metadata.get("Modified")
                            )
                            if file_metadata
                            else None
                        )

                        # Track seen source_document_ids for orphan cleanup
                        if unique_id:
                            async with self._state.seen_ids_lock:
                                self._state.seen_source_document_ids.add(str(unique_id))

                        # Check if document is unchanged (optimization: skip download)
                        if unique_id and time_last_modified:
                            try:
                                # Parse SharePoint timestamp to datetime for comparison
                                source_modified_dt: datetime | None = None
                                if isinstance(time_last_modified, datetime):
                                    source_modified_dt = time_last_modified
                                elif isinstance(time_last_modified, str):
                                    try:
                                        source_modified_dt = datetime.fromisoformat(
                                            time_last_modified.replace("Z", "+00:00")
                                        )
                                    except Exception:  # noqa: BLE001
                                        pass

                                if source_modified_dt:
                                    docs_table = docs_table_name(self._graph_uuid)
                                    result = await session.execute(
                                        text(
                                            f"""
                                            SELECT source_modified_at
                                            FROM {docs_table}
                                            WHERE source_id = :sid AND source_document_id = :doc_id
                                            LIMIT 1
                                            """
                                        ),
                                        {
                                            "sid": str(self._source.source.id),
                                            "doc_id": str(unique_id),
                                        },
                                    )
                                    existing_modified = result.scalar_one_or_none()

                                    if existing_modified:
                                        # Ensure both are timezone-aware for comparison
                                        # PostgreSQL returns timezone-aware datetime
                                        if source_modified_dt.tzinfo is None:
                                            source_modified_dt = (
                                                source_modified_dt.replace(
                                                    tzinfo=existing_modified.tzinfo
                                                )
                                            )

                                        # If timestamps match, skip this file
                                        if existing_modified == source_modified_dt:
                                            await ctx.inc("unchanged_skipped")

                                            logger.debug(
                                                "Skipping unchanged SharePoint file",
                                                extra=self._log_extra(
                                                    worker_id=worker_id,
                                                    file=f.name,
                                                    unique_id=unique_id,
                                                    db_modified=existing_modified.isoformat(),
                                                    sp_modified=source_modified_dt.isoformat(),
                                                ),
                                            )
                                            continue
                            except Exception as check_exc:  # noqa: BLE001
                                logger.debug(
                                    "Failed to check document change status",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        file=f.name,
                                        error=str(check_exc),
                                    ),
                                )
                                # On error, proceed with sync (safe fallback)

                        # Create enhanced file ref with metadata
                        from .sharepoint_models import SharePointFileRef

                        enhanced_file = SharePointFileRef(
                            name=f.name,
                            server_relative_url=f.server_relative_url,
                            unique_id=str(unique_id) if unique_id else None,
                            time_last_modified=str(time_last_modified)
                            if time_last_modified
                            else None,
                        )

                        logger.debug(
                            "Enqueueing SharePoint file for fetch",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                file=f.name,
                                unique_id=unique_id,
                                has_modified_time=bool(time_last_modified),
                            ),
                        )

                        await ctx.content_fetch_queue.put(
                            SharePointContentFetchTask(file=enhanced_file)
                        )

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
                    file_metadata: dict[str, Any] = {}
                    file_bytes: bytes | None = None

                    # For .aspx pages, get HTML content from CanvasContent1 instead of downloading file bytes
                    is_aspx_page = filename.lower().endswith(".aspx")

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

                    # Compute content hash for change detection
                    content_hash = hashlib.sha256(file_bytes).hexdigest()

                    # Extract change tracking metadata from file ref or metadata
                    source_document_id = file_ref.unique_id or file_metadata.get(
                        "UniqueId"
                    )
                    source_modified_at_raw = (
                        file_ref.time_last_modified
                        or file_metadata.get("TimeLastModified")
                        or file_metadata.get("Modified")
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

                    # Check if only metadata changed (hash matches)
                    # Initialize variable at outer scope for debug tracking
                    existing_doc_row = None

                    if source_document_id and content_hash:
                        try:
                            docs_table = docs_table_name(self._graph_uuid)
                            result = await session.execute(
                                text(
                                    f"""
                                    SELECT id::text, content_hash, source_modified_at
                                    FROM {docs_table}
                                    WHERE source_id = :sid AND source_document_id = :doc_id
                                    LIMIT 1
                                    """
                                ),
                                {
                                    "sid": str(self._source.source.id),
                                    "doc_id": str(source_document_id),
                                },
                            )
                            existing_doc_row = result.one_or_none()

                            if existing_doc_row and existing_doc_row[1] == content_hash:
                                # Content unchanged - only update metadata
                                logger.debug(
                                    "Hash matches - attempting metadata-only update",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        doc_filename=filename,
                                        hash_matches=True,
                                    ),
                                )
                                await self._source.update_document_metadata_only(
                                    session,
                                    document_id=existing_doc_row[0],
                                    filename=filename,
                                    source_document_id=str(source_document_id),
                                    source_modified_at=source_modified_at,
                                    file_metadata=None,  # Not loading content for metadata-only updates
                                    source_metadata=file_metadata,
                                )
                                logger.debug(
                                    "Metadata update completed successfully",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        doc_filename=filename,
                                    ),
                                )
                                await ctx.inc("metadata_only_updated")

                                logger.debug(
                                    "Updated SharePoint document metadata only (content unchanged)",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        doc_filename=filename,
                                        source_document_id=source_document_id,
                                    ),
                                )
                                continue  # Skip full processing
                        except Exception as hash_check_exc:  # noqa: BLE001
                            logger.warning(
                                "Failed to check content hash - proceeding with full sync",
                                extra=self._log_extra(
                                    worker_id=worker_id,
                                    doc_filename=filename,
                                    source_document_id=source_document_id,
                                    content_hash=content_hash,
                                    error=str(hash_check_exc),
                                    error_type=type(hash_check_exc).__name__,
                                ),
                                exc_info=True,
                            )
                            # On error, proceed with full sync (safe fallback)

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
                    external_link = self._build_external_link(
                        file_ref.server_relative_url
                    )

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
                        source_document_id=str(source_document_id)
                        if source_document_id
                        else None,
                        source_modified_at=source_modified_at,
                        content_hash=content_hash,
                    )

                    # Track whether this is a new document or content update
                    # Note: create_document_for_source returns is_new_document in the dict
                    # We increment content_changed for documents that need full reprocessing
                    await ctx.inc("content_changed")

                    logger.info(
                        "SharePoint document created/updated for processing",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            doc_filename=filename,
                            doc_id=document.get("id"),
                            source_doc_id=source_document_id,
                            has_hash=bool(content_hash),
                        ),
                    )

                    await ctx.document_processing_queue.put(
                        ProcessDocumentTask(
                            document=document,
                            extracted_text=content["text"],
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

    async def _cleanup_orphaned_documents(self, counters: SyncCounters) -> int:
        """Delete documents that exist in the Knowledge Graph but not in SharePoint source.

        Only deletes documents WITH source_document_id (intelligent sync enabled).
        Legacy documents without source_document_id are skipped for safety.
        """
        seen_ids = self._state.seen_source_document_ids

        logger.info(
            "Starting orphaned document cleanup",
            extra=self._log_extra(
                total_found=counters.total_found,
                seen_source_ids=len(seen_ids),
            ),
        )

        async with async_session_maker() as session:
            docs_table = docs_table_name(self._graph_uuid)
            result = await session.execute(
                text(
                    f"""
                    SELECT id::text, source_document_id, name
                    FROM {docs_table}
                    WHERE source_id = :sid
                    """
                ),
                {"sid": str(self._source.source.id)},
            )

            existing_docs = result.all()
            orphaned_docs = []

            # Find orphaned documents (exist in KG but not in source)
            for doc_id, source_doc_id, doc_name in existing_docs:
                if source_doc_id and source_doc_id not in seen_ids:
                    orphaned_docs.append((doc_id, source_doc_id, doc_name))
                elif not source_doc_id:
                    # Legacy document - skip cleanup (created before intelligent sync)
                    logger.debug(
                        "Found legacy document without source_document_id - skipping cleanup",
                        extra=self._log_extra(
                            document_id=doc_id,
                            document_name=doc_name,
                        ),
                    )

            if not orphaned_docs:
                logger.info(
                    "No orphaned documents found",
                    extra=self._log_extra(existing_in_kg=len(existing_docs)),
                )
                return 0

            logger.info(
                "Deleting orphaned documents",
                extra=self._log_extra(
                    orphaned_count=len(orphaned_docs),
                    existing_count=len(existing_docs),
                ),
            )

            # Delete orphaned documents (chunks will cascade via FK)
            from core.domain.knowledge_graph.service import (
                KnowledgeGraphDocumentService,
            )

            doc_service = KnowledgeGraphDocumentService()
            deleted_count = 0

            for doc_id, source_doc_id, doc_name in orphaned_docs:
                try:
                    await doc_service.delete_document(
                        session,
                        graph_id=self._graph_uuid,
                        id=UUID(doc_id),
                    )
                    deleted_count += 1
                    logger.debug(
                        "Deleted orphaned document",
                        extra=self._log_extra(
                            document_id=doc_id,
                            source_document_id=source_doc_id,
                            document_name=doc_name,
                        ),
                    )
                except Exception as delete_exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to delete orphaned document",
                        extra=self._log_extra(
                            document_id=doc_id,
                            source_document_id=source_doc_id,
                            document_name=doc_name,
                            error=str(delete_exc),
                        ),
                    )

            logger.info(
                "Orphaned document cleanup completed",
                extra=self._log_extra(
                    deleted=deleted_count, failed=len(orphaned_docs) - deleted_count
                ),
            )

            return deleted_count

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
