from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from core.db.session import async_session_maker

from ...content_load_services import load_content_from_bytes
from ...models import ContentConfig, SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .file_upload_models import (
    FileUploadContentFetchTask,
    FileUploadListingTask,
    FileUploadProcessDocumentTask,
)

if TYPE_CHECKING:
    from .file_upload_source import FileUploadDataSource

logger = logging.getLogger(__name__)

FileUploadPipelineContext = SyncPipelineContext[
    FileUploadListingTask, FileUploadContentFetchTask, FileUploadProcessDocumentTask
]


class FileUploadSyncPipeline(
    SyncPipeline[
        FileUploadListingTask, FileUploadContentFetchTask, FileUploadProcessDocumentTask
    ]
):
    """Pipeline for file uploads.

    Differences vs. other sources:
    - No listing stage: the listing queue stays empty.
    - `bootstrap()` seeds the uploaded file directly into the content-fetch queue.
    """

    def __init__(
        self,
        *,
        source: "FileUploadDataSource",
        pipeline_config: SyncPipelineConfig,
        embedding_model: str,
        filename: str,
        file_bytes: bytes,
        content_config: ContentConfig,
    ) -> None:
        super().__init__(config=pipeline_config)
        self._source = source

        if not source.source:
            raise RuntimeError(
                "FileUploadSyncPipeline requires source.source to be set."
            )

        self._graph_id = str(source.source.graph_id)
        self._source_id = str(source.source.id)

        self._embedding_model = embedding_model

        self._filename = filename
        self._file_bytes = file_bytes
        self._content_config = content_config

    @override
    async def bootstrap(self, ctx: FileUploadPipelineContext) -> None:
        # There is no listing stage for file uploads; enqueue the file directly.
        await ctx.inc("total_found", 1)
        await ctx.content_fetch_queue.put(
            FileUploadContentFetchTask(
                filename=self._filename,
                file_bytes=self._file_bytes,
                content_config=self._content_config,
            )
        )

    @override
    async def run(self) -> SyncCounters:
        return await self._run_pipeline(
            listing_worker=self._listing_worker,
            content_fetch_worker=self._content_fetch_worker,
            document_processing_worker=self._document_processing_worker,
        )

    async def _listing_worker(
        self, ctx: FileUploadPipelineContext, worker_id: int
    ) -> None:
        # Listing queue should remain empty; just drain until sentinel.
        async for _ in ctx.iter_listing_tasks():
            logger.debug(
                "Unexpected file upload listing task",
                extra=self._log_extra(worker_id=worker_id),
            )

    async def _content_fetch_worker(
        self, ctx: FileUploadPipelineContext, worker_id: int
    ) -> None:
        async with async_session_maker() as session:
            async for task in ctx.iter_content_fetch_tasks():
                filename = str(task.filename or "").strip()
                if not filename:
                    await ctx.inc("skipped")
                    continue

                try:
                    content = load_content_from_bytes(
                        task.file_bytes, task.content_config
                    )
                    total_pages = content["metadata"].get("total_pages")

                    document = await self._source.create_document_for_source(
                        session,
                        filename=filename,
                        total_pages=total_pages,
                        file_metadata=content.get("metadata")
                        if isinstance(content, dict)
                        else None,
                        default_document_type="txt",
                        content_profile=task.content_config.name
                        if task.content_config
                        else None,
                    )

                    await ctx.document_processing_queue.put(
                        FileUploadProcessDocumentTask(
                            document=document,
                            extracted_text=content["text"],
                            content_config=task.content_config,
                        )
                    )

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "File upload content_fetch worker failed",
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
                            "Failed to mark file upload document error",
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
                            "Failed to rollback session after file upload content_fetch failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                doc_filename=filename or None,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )
                    raise

    async def _document_processing_worker(
        self, ctx: FileUploadPipelineContext, worker_id: int
    ) -> None:
        async with async_session_maker() as session:
            async for task in ctx.iter_document_processing_tasks():
                doc_name = str(task.document.get("name") or "")
                try:
                    await self._source.process_document(
                        session,
                        task.document,
                        extracted_text=task.extracted_text,
                        config=task.content_config,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "File upload document_processing worker failed",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            document_id=task.document.get("id"),
                            document_name=doc_name or None,
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
                            "Failed to mark file upload document error during processing",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name or None,
                                error=str(mark_exc),
                                error_type=type(mark_exc).__name__,
                            ),
                        )
                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after file upload processing failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name or None,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )
                    raise

    def _log_extra(self, **extra: object) -> dict[str, object]:
        return {"graph_id": self._graph_id, "source_id": self._source_id, **extra}
