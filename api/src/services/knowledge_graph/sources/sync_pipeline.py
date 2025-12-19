import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Awaitable, Callable, Generic, Literal, TypeVar

from ..models import SyncCounters, SyncPipelineConfig

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

    def __init__(self, config: SyncPipelineConfig):
        config.validate()
        self.config = config
        self.counters = SyncCounters()

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
