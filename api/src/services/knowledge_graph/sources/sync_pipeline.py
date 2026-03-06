import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Generic, Literal, TypeVar
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource, docs_table_name
from core.db.session import async_session_maker
from core.domain.knowledge_graph.services import KnowledgeGraphDocumentService
from services.observability import observability_context, observe
from services.observability.models import SpanExportMethod

from ..content_load_services import load_content_from_bytes
from ..models import (
    ContentConfig,
    LoadedContent,
    StoreDocumentResult,
    SyncCounters,
    SyncPipelineConfig,
)

logger = logging.getLogger(__name__)

ListTaskT = TypeVar("ListTaskT")
ContentTaskT = TypeVar("ContentTaskT")
ProcessTaskT = TypeVar("ProcessTaskT")

CounterField = Literal["synced", "failed", "skipped", "total_found"]


@dataclass
class SyncPipelineContext(Generic[ListTaskT, ContentTaskT, ProcessTaskT]):
    """Runtime context shared across all workers in a pipeline run."""

    # Queues
    listing_queue: asyncio.Queue[Any]
    content_fetch_queue: asyncio.Queue[Any]
    document_processing_queue: asyncio.Queue[Any]

    # Controls
    semaphores: dict[str, asyncio.Semaphore]
    counters: SyncCounters

    # A per-run sentinel token. Workers should never enqueue it.
    sentinel: object

    _counters_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def inc(self, field: CounterField, n: int = 1) -> None:
        if n == 0:
            return
        async with self._counters_lock:
            setattr(self.counters, field, int(getattr(self.counters, field)) + int(n))

    async def dec(self, field: CounterField, n: int = 1) -> None:
        if n == 0:
            return
        async with self._counters_lock:
            setattr(self.counters, field, int(getattr(self.counters, field)) - int(n))

    def semaphore(self, name: str) -> asyncio.Semaphore:
        sem = self.semaphores.get(name)
        if not sem:
            raise KeyError(
                f"Semaphore '{name}' is not configured. Available: {list(self.semaphores.keys())}"
            )
        return sem

    async def iter_queue(self, queue: asyncio.Queue[Any]) -> AsyncIterator[Any]:
        """Iterate items from a queue until sentinel is received.

        Ensures `queue.task_done()` is called for every dequeued item (including sentinel).
        """
        while True:
            item = await queue.get()
            try:
                if item is self.sentinel:
                    return
                yield item
            finally:
                queue.task_done()

    async def iter_listing_tasks(self) -> AsyncIterator[ListTaskT]:
        async for item in self.iter_queue(self.listing_queue):
            yield item  # type: ignore[misc]

    async def iter_content_fetch_tasks(self) -> AsyncIterator[ContentTaskT]:
        async for item in self.iter_queue(self.content_fetch_queue):
            yield item  # type: ignore[misc]

    async def iter_document_processing_tasks(self) -> AsyncIterator[ProcessTaskT]:
        async for item in self.iter_queue(self.document_processing_queue):
            yield item  # type: ignore[misc]


ListingWorker = Callable[
    [SyncPipelineContext[ListTaskT, ContentTaskT, ProcessTaskT], int], Awaitable[None]
]
ContentFetchWorker = Callable[
    [SyncPipelineContext[ListTaskT, ContentTaskT, ProcessTaskT], int], Awaitable[None]
]
DocumentProcessingWorker = Callable[
    [SyncPipelineContext[ListTaskT, ContentTaskT, ProcessTaskT], int], Awaitable[None]
]


class SyncPipeline(Generic[ListTaskT, ContentTaskT, ProcessTaskT], ABC):
    """Reusable 3-stage async pipeline runner.

    This class is intentionally source-agnostic:
    - It owns the queues, semaphores, counters, and worker lifecycle.
    - Each knowledge source provides the actual worker implementations.

    Contract:
    - Listing workers may enqueue new listing tasks and content-fetch tasks.
    - Content-fetch workers may enqueue document-processing tasks.
    - Document-processing workers should not enqueue new tasks (keeps shutdown deterministic).
    """

    document_service = KnowledgeGraphDocumentService()

    def __init__(self, config: SyncPipelineConfig):
        config.validate()
        self.config = config
        self.counters = SyncCounters()
        self._seen_source_document_ids: set[str] = set()
        self._seen_ids_lock = asyncio.Lock()

    async def bootstrap(
        self, ctx: SyncPipelineContext[ListTaskT, ContentTaskT, ProcessTaskT]
    ) -> None:
        """Perform run-scoped bootstrap work before the pipeline starts draining stages.

        Use this hook to enqueue initial tasks (e.g. the first page of a paginated listing),
        warm caches, or fetch "cursor" metadata required by the workers.

        This method is called **after** workers are started (so they can immediately consume
        tasks you enqueue), and **before** any stage is awaited/drained.

        Default: no-op.
        """

        return None

    @abstractmethod
    async def run(self) -> SyncCounters:
        """Run the pipeline.

        Subclasses should provide:
        - bootstrap (initial work / initial task enqueueing)
        - worker implementations

        Most implementations will call `self._run_pipeline(...)`.
        """
        raise NotImplementedError

    @observe(name="Run sync pipeline")
    async def _run_pipeline(
        self,
        *,
        listing_worker: ListingWorker[ListTaskT, ContentTaskT, ProcessTaskT],
        content_fetch_worker: ContentFetchWorker[ListTaskT, ContentTaskT, ProcessTaskT],
        document_processing_worker: DocumentProcessingWorker[
            ListTaskT, ContentTaskT, ProcessTaskT
        ],
    ) -> SyncCounters:
        sentinel = object()

        logger.info(
            "Starting %s: workers(listing=%s content_fetch=%s document_processing=%s) queues(max listing=%s content_fetch=%s document_processing=%s) semaphores=%s",
            self.config.name,
            self.config.listing_workers,
            self.config.content_fetch_workers,
            self.config.document_processing_workers,
            self.config.listing_queue_max,
            self.config.content_fetch_queue_max,
            self.config.document_processing_queue_max,
            self.config.semaphores,
        )

        observability_context.update_current_config(
            span_export_method=SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
        )

        listing_queue: asyncio.Queue[Any] = asyncio.Queue(
            maxsize=self.config.listing_queue_max
        )
        content_fetch_queue: asyncio.Queue[Any] = asyncio.Queue(
            maxsize=self.config.content_fetch_queue_max
        )
        document_processing_queue: asyncio.Queue[Any] = asyncio.Queue(
            maxsize=self.config.document_processing_queue_max
        )

        semaphores: dict[str, asyncio.Semaphore] = {
            name: asyncio.Semaphore(int(limit))
            for name, limit in (self.config.semaphores or {}).items()
        }

        ctx: SyncPipelineContext[ListTaskT, ContentTaskT, ProcessTaskT] = (
            SyncPipelineContext(
                listing_queue=listing_queue,
                content_fetch_queue=content_fetch_queue,
                document_processing_queue=document_processing_queue,
                semaphores=semaphores,
                counters=self.counters,
                sentinel=sentinel,
            )
        )

        # Start workers
        listing_tasks = [
            asyncio.create_task(listing_worker(ctx, i))
            for i in range(int(self.config.listing_workers))
        ]
        content_tasks = [
            asyncio.create_task(content_fetch_worker(ctx, i))
            for i in range(int(self.config.content_fetch_workers))
        ]
        processing_tasks = [
            asyncio.create_task(document_processing_worker(ctx, i))
            for i in range(int(self.config.document_processing_workers))
        ]

        all_tasks = [*listing_tasks, *content_tasks, *processing_tasks]

        try:
            # Bootstrap/kickoff hook (enqueue initial tasks, etc.)
            await self.bootstrap(ctx)

            # Stage drain + shutdown ordering:
            # - let listing workers finish scheduling work
            # - then let content-fetch workers finish producing processing tasks
            # - finally let document-processing workers drain
            await listing_queue.join()
            logger.info("Stage complete: %s listing queue drained", self.config.name)
            for _ in listing_tasks:
                await listing_queue.put(sentinel)
            listing_results = await asyncio.gather(
                *listing_tasks, return_exceptions=True
            )

            await content_fetch_queue.join()
            logger.info(
                "Stage complete: %s content_fetch queue drained", self.config.name
            )
            for _ in content_tasks:
                await content_fetch_queue.put(sentinel)
            content_results = await asyncio.gather(
                *content_tasks, return_exceptions=True
            )

            await document_processing_queue.join()
            logger.info(
                "Stage complete: %s document_processing queue drained", self.config.name
            )
            for _ in processing_tasks:
                await document_processing_queue.put(sentinel)
            processing_results = await asyncio.gather(
                *processing_tasks, return_exceptions=True
            )
        finally:
            # Ensure we never leak background workers if bootstrap fails or the caller cancels.
            for t in all_tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*all_tasks, return_exceptions=True)

        # Surface unexpected worker exceptions.
        for results in (listing_results, content_results, processing_results):
            for r in results:
                if isinstance(r, BaseException) and not isinstance(
                    r, asyncio.CancelledError
                ):
                    logger.error("Pipeline worker failed: %s", r)
                    raise r

        logger.info(
            "Completed %s: counters(total_found=%s synced=%s failed=%s skipped=%s)",
            self.config.name,
            self.counters.total_found,
            self.counters.synced,
            self.counters.failed,
            self.counters.skipped,
        )
        return self.counters

    async def store_document(
        self,
        session: AsyncSession,
        source: KnowledgeGraphSource,
        *,
        content: bytes | str,
        graph_id: UUID | str,
        filename: str,
        source_document_id: str | None = None,
        source_modified_at: datetime | None = None,
        source_metadata: dict[str, Any] | None = None,
        default_document_type: str = "txt",
        content_config: ContentConfig | None = None,
        title: str | None = None,
        external_link: str | None = None,
        toc: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> StoreDocumentResult:
        """Hash content, detect unchanged documents, and either update metadata or create/update.

        When content is bytes and content_config is provided, the bytes are loaded via
        load_content_from_bytes to extract text, total_pages, and file_metadata.
        The loaded content is returned in the result for downstream processing.

        When content is str, the hash is computed from the UTF-8 encoding and
        no content loading is performed.

        Returns StoreDocumentResult with document=None when only metadata was updated
        (content unchanged), or document + loaded_content when a new document was created.
        """
        if isinstance(content, str):
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        else:
            content_hash = hashlib.sha256(content).hexdigest()

        if source_document_id and content_hash:
            rows = await self.document_service.query_documents(
                session,
                graph_id=graph_id,
                source_id=source.id,
                source_document_id=str(source_document_id),
                content_hash=content_hash,
                columns=("id",),
            )
            existing_doc_id = (
                str(rows[0].get("id")) if rows and rows[0].get("id") else None
            )
            if existing_doc_id:
                await self.document_service.update_document_metadata_only(
                    session,
                    source,
                    document_id=existing_doc_id,
                    filename=filename,
                    source_document_id=str(source_document_id),
                    source_modified_at=source_modified_at,
                    source_metadata=source_metadata,
                    content_profile=content_config.name if content_config else None,
                )
                return StoreDocumentResult()

        loaded: LoadedContent | None = None
        total_pages: int | None = None
        file_metadata: dict[str, Any] | None = None

        if isinstance(content, bytes) and content_config:
            loaded = load_content_from_bytes(content, content_config)
            file_metadata = loaded.get("metadata")
            total_pages = file_metadata.get("total_pages") if file_metadata else None

        document = await self.document_service.upsert_document(
            session,
            source,
            filename=filename,
            total_pages=total_pages,
            file_metadata=file_metadata,
            source_document_id=str(source_document_id) if source_document_id else None,
            source_metadata=source_metadata,
            source_modified_at=source_modified_at,
            content_hash=content_hash,
            default_document_type=default_document_type,
            content_profile=content_config.name if content_config else None,
            title=title,
            toc=toc,
            external_link=external_link,
        )

        return StoreDocumentResult(document=document, loaded_content=loaded)

    async def track_source_document_id(self, source_document_id: str) -> None:
        """Register a source_document_id as seen during the current sync run.

        Call this for every document discovered in the remote source so that
        `cleanup_orphaned_documents` can later identify documents that no longer exist.
        """
        async with self._seen_ids_lock:
            self._seen_source_document_ids.add(source_document_id)

    async def cleanup_orphaned_documents(
        self,
        *,
        graph_id: UUID,
        source_id: str | UUID,
        counters: SyncCounters,
        log_extra: dict[str, Any] | None = None,
    ) -> int:
        """Delete documents that exist in the Knowledge Graph but are no longer in the source.

        Only deletes documents WITH source_document_id (intelligent sync enabled).
        Legacy documents without source_document_id are skipped for safety.

        Should be called after the pipeline has finished processing all documents,
        so that `_seen_source_document_ids` is fully populated.
        """
        seen_ids = self._seen_source_document_ids
        extra = log_extra or {}

        logger.info(
            "Starting orphaned document cleanup",
            extra={
                **extra,
                "total_found": counters.total_found,
                "seen_source_ids": len(seen_ids),
            },
        )

        graph_uuid = graph_id if isinstance(graph_id, UUID) else UUID(str(graph_id))
        source_id_str = str(source_id)

        async with async_session_maker() as session:
            docs_table = docs_table_name(graph_uuid)
            result = await session.execute(
                text(
                    f"""
                    SELECT id::text, source_document_id, name
                    FROM {docs_table}
                    WHERE source_id = :sid
                    """
                ),
                {"sid": source_id_str},
            )

            existing_docs = result.all()
            orphaned_docs = []

            for doc_id, source_doc_id, doc_name in existing_docs:
                if source_doc_id and source_doc_id not in seen_ids:
                    orphaned_docs.append((doc_id, source_doc_id, doc_name))
                elif not source_doc_id:
                    logger.debug(
                        "Found legacy document without source_document_id - skipping cleanup",
                        extra={
                            **extra,
                            "document_id": doc_id,
                            "document_name": doc_name,
                        },
                    )

            if not orphaned_docs:
                logger.info(
                    "No orphaned documents found",
                    extra={**extra, "existing_in_kg": len(existing_docs)},
                )
                return 0

            logger.info(
                "Deleting orphaned documents",
                extra={
                    **extra,
                    "orphaned_count": len(orphaned_docs),
                    "existing_count": len(existing_docs),
                },
            )

            deleted_count = 0

            for doc_id, source_doc_id, doc_name in orphaned_docs:
                try:
                    await self.document_service.delete_document(
                        session, graph_uuid, UUID(doc_id)
                    )
                    deleted_count += 1
                    logger.debug(
                        "Deleted orphaned document",
                        extra={
                            **extra,
                            "document_id": doc_id,
                            "source_document_id": source_doc_id,
                            "document_name": doc_name,
                        },
                    )
                except Exception as delete_exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to delete orphaned document",
                        extra={
                            **extra,
                            "document_id": doc_id,
                            "source_document_id": source_doc_id,
                            "document_name": doc_name,
                            "error": str(delete_exc),
                        },
                    )

            logger.info(
                "Orphaned document cleanup completed",
                extra={
                    **extra,
                    "deleted": deleted_count,
                    "failed": len(orphaned_docs) - deleted_count,
                },
            )

            return deleted_count
