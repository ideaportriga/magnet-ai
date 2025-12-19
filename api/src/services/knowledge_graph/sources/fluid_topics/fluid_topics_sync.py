from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, override

import httpx
from litestar.exceptions import ClientException

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...content_load_services import load_content_from_bytes
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .fluid_topics_models import (
    FluidTopicsContentFetchTask,
    FluidTopicsListingTask,
    FluidTopicsRuntimeConfig,
    FluidTopicsSharedSyncState,
    ProcessDocumentTask,
)
from .fluid_topics_utils import (
    download_file,
    fetch_map_toc,
    fetch_topic_content,
    ft_toc_to_kg_toc,
    iter_ft_toc_content_nodes,
    normalize_map_toc_payload,
)

if TYPE_CHECKING:
    from .fluid_topics_source import FluidTopicsSource

logger = logging.getLogger(__name__)

FluidTopicsPipelineContext = SyncPipelineContext[
    FluidTopicsListingTask, FluidTopicsContentFetchTask, ProcessDocumentTask
]


class FluidTopicsSyncPipeline(
    SyncPipeline[
        FluidTopicsListingTask, FluidTopicsContentFetchTask, ProcessDocumentTask
    ]
):
    """Fluid Topics pipeline implementation.

    This class combines:
    - the generic pipeline runner (from SyncPipeline)
    - Fluid Topics-specific worker implementations + shared run state
    """

    def __init__(
        self,
        source: "FluidTopicsSource",
        pipeline_config: SyncPipelineConfig,
        fluid_topics_config: FluidTopicsRuntimeConfig,
        embedding_model: str,
    ):
        super().__init__(config=pipeline_config)
        self._source = source
        self._graph_id = str(source.source.graph_id)
        self._source_id = str(source.source.id)
        self._fluid_topics_config = fluid_topics_config
        self._embedding_model = embedding_model

        # Run-scoped resources/state (created in `run()`)
        self._client: httpx.AsyncClient | None = None
        self._state: FluidTopicsSharedSyncState | None = None

    @override
    async def bootstrap(self, ctx: FluidTopicsPipelineContext) -> None:
        # Kick off pagination by seeding the first page.
        await ctx.listing_queue.put(FluidTopicsListingTask(page=1))

    @override
    async def run(self) -> SyncCounters:
        """Run a Fluid Topics sync with no parameters."""

        async with httpx.AsyncClient() as client:
            self._state = FluidTopicsSharedSyncState()
            self._client = client
            try:
                return await self._run_pipeline(
                    listing_worker=self._listing_worker,
                    content_fetch_worker=self._content_fetch_worker,
                    document_processing_worker=self._document_processing_worker,
                )
            finally:
                self._client = None
                self._state = None

    async def _listing_worker(
        self, ctx: FluidTopicsPipelineContext, worker_id: int
    ) -> None:
        self._worker_validation()

        logger.debug(
            "Fluid Topics listing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async for task in ctx.iter_listing_tasks():
            page = int(task.page)
            # If we already learned this is the last page (or an error occurred), just drain.
            if self._state.pages_done.is_set():
                continue

            try:
                logger.debug(
                    "Fluid Topics search page fetching",
                    extra=self._log_extra(worker_id=worker_id, page=page),
                )
                try:
                    async with ctx.semaphore("fluid_api"):
                        response = await self._client.post(
                            self._fluid_topics_config.search_api_url,
                            json={
                                "filters": self._fluid_topics_config.filters,
                                "paging": {
                                    "page": page,
                                    "perPage": self._source.SEARCH_PER_PAGE,
                                },
                            },
                            headers={"x-api-key": self._fluid_topics_config.api_key},
                            timeout=self._source.SEARCH_TIMEOUT_S,
                        )
                    response.raise_for_status()
                    json_response = response.json()
                except httpx.RequestError as exc:
                    raise ClientException(
                        f"Failed to fetch data from Fluid Topics (request error): {exc}"
                    ) from exc
                except httpx.HTTPStatusError as exc:
                    raise ClientException(
                        f"Failed to fetch data from Fluid Topics (HTTP {exc.response.status_code})"
                    ) from exc

                results = json_response.get("results", [])
                docs_enqueued = 0
                maps_enqueued = 0

                for result in results:
                    entries = result.get("entries", [])
                    await ctx.inc("total_found", len(entries))

                    for entry in entries:
                        entry_type = entry.get("type")

                        if entry_type == "DOCUMENT":
                            if not self._fluid_topics_config.pdf_api_url:
                                await ctx.inc("skipped")
                                continue

                            doc_info = entry.get("document") or {}
                            filename = str(doc_info.get("filename"))
                            if not filename:
                                await ctx.inc("skipped")
                                continue

                            await ctx.content_fetch_queue.put(
                                FluidTopicsContentFetchTask(
                                    kind="document", filename=filename
                                )
                            )

                            docs_enqueued += 1
                            continue

                        if entry_type == "TOPIC":
                            if (
                                not self._fluid_topics_config.map_content_url_template
                                or not self._fluid_topics_config.map_toc_url_template
                            ):
                                await ctx.inc("skipped")
                                continue

                            async with self._state.seen_maps_lock:
                                topic_info = entry.get("topic") or {}
                                map_id = str(topic_info.get("mapId"))
                                map_title = str(topic_info.get("mapTitle") or "")
                                if not map_id:
                                    await ctx.inc("skipped")
                                    continue

                                if map_id not in self._state.seen_maps:
                                    self._state.seen_maps[map_id] = map_title
                                else:
                                    # We intentionally ingest a map only once even if it appears in multiple
                                    # search results (e.g. because multiple topics match the search query).
                                    await ctx.dec("total_found")
                                    continue

                            await ctx.content_fetch_queue.put(
                                FluidTopicsContentFetchTask(
                                    kind="map", map_id=map_id, map_title=map_title
                                )
                            )

                            maps_enqueued += 1
                            continue

                        logger.warning(
                            "Unknown Fluid Topics entry type",
                            extra=self._log_extra(
                                worker_id=worker_id, page=page, entry_type=entry_type
                            ),
                        )
                        await ctx.inc("skipped")

                logger.debug(
                    "Parsed Fluid Topics search page",
                    extra=self._log_extra(
                        worker_id=worker_id,
                        page=page,
                        results=len(results),
                        docs_enqueued=docs_enqueued,
                        maps_enqueued=maps_enqueued,
                    ),
                )

                if bool(json_response.get("paging", {}).get("isLastPage")):
                    self._state.pages_done.set()
                    logger.debug(
                        "Reached last Fluid Topics search page",
                        extra=self._log_extra(worker_id=worker_id, page=page),
                    )
                    continue

                await ctx.listing_queue.put(FluidTopicsListingTask(page=page + 1))

            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Fluid Topics listing worker failed",
                    extra=self._log_extra(
                        worker_id=worker_id,
                        page=page,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    ),
                )
                self._state.pages_done.set()
                await ctx.inc("failed")

    async def _content_fetch_worker(
        self, ctx: FluidTopicsPipelineContext, worker_id: int
    ) -> None:
        self._worker_validation()

        logger.debug(
            "Fluid Topics content_fetch worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async with async_session_maker() as session:
            async for task in ctx.iter_content_fetch_tasks():
                try:
                    if task.kind == "map":
                        map_id = task.map_id
                        map_title = task.map_title or map_id
                        doc_name = map_title.strip()

                        logger.debug(
                            "Fetching Fluid Topics map",
                            extra=self._log_extra(
                                worker_id=worker_id, map_id=map_id, map_title=map_title
                            ),
                        )

                        (
                            toc,
                            chunks,
                            failed,
                            skipped,
                        ) = await self._fetch_map_toc_and_chunks(ctx, map_id)

                        if failed:
                            await ctx.inc("failed", int(failed))
                        if skipped:
                            await ctx.inc("skipped", int(skipped))

                        document = await self._source.create_document_for_source(
                            session, filename=doc_name, default_document_type="html"
                        )

                        await self._source._upsert_document_metadata(
                            graph_id=document["graph_id"],
                            doc_id=document["id"],
                            title=str(map_title),
                            toc_json=toc,
                        )

                        await ctx.document_processing_queue.put(
                            ProcessDocumentTask(
                                document=document,
                                chunks=chunks,
                                toc=toc,
                                document_title=str(map_title),
                            )
                        )
                        continue

                    if task.kind == "document":
                        filename = task.filename

                        content_config = await get_content_config(
                            session,
                            self._graph_id,
                            filename,
                            source_type=self._source.source.type,
                        )
                        if not content_config:
                            logger.warning(
                                "Skipping Fluid Topics document: no content config found",
                                extra=self._log_extra(
                                    worker_id=worker_id, filename=filename
                                ),
                            )
                            await ctx.inc("skipped")
                            continue

                        logger.debug(
                            "Downloading Fluid Topics file",
                            extra=self._log_extra(
                                worker_id=worker_id, filename=filename
                            ),
                        )
                        file_bytes = await download_file(self, ctx, filename)

                        content = load_content_from_bytes(file_bytes, content_config)
                        total_pages = content["metadata"].get("total_pages")

                        document = await self._source.create_document_for_source(
                            session,
                            filename=filename,
                            total_pages=total_pages,
                            default_document_type="pdf",
                            content_profile=content_config.name
                            if content_config
                            else None,
                        )

                        await ctx.document_processing_queue.put(
                            ProcessDocumentTask(
                                document=document,
                                extracted_text=content["text"],
                                content_config=content_config,
                            )
                        )
                        continue

                    logger.warning(
                        "Unknown Fluid Topics content_fetch task kind",
                        extra=self._log_extra(worker_id=worker_id, task_kind=task.kind),
                    )

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Failed to fetch topic/document content from Fluid Topics",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            task_kind=task.kind,
                            filename=getattr(task, "filename", None),
                            map_id=getattr(task, "map_id", None),
                            map_title=getattr(task, "map_title", None),
                            error=str(exc),
                            error_type=type(exc).__name__,
                        ),
                    )
                    await ctx.inc("failed")
                    try:
                        # Best-effort error marker; failure should not crash the worker.
                        task_name = (
                            getattr(task, "filename", None)
                            or getattr(task, "map_title", None)
                            or getattr(task, "map_id", None)
                        )
                        if task_name:
                            await self._source._mark_document_error(
                                session, str(task_name), exc
                            )
                    except Exception as mark_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to mark Fluid Topics document error",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                task_kind=task.kind,
                                error=str(mark_exc),
                                error_type=type(mark_exc).__name__,
                            ),
                        )
                    try:
                        await session.rollback()
                    except Exception as rb_exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to rollback session after Fluid Topics task failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                task_kind=task.kind,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )

                await ctx.inc("skipped")

    async def _document_processing_worker(
        self, ctx: FluidTopicsPipelineContext, worker_id: int
    ) -> None:
        self._worker_validation()

        logger.debug(
            "Fluid Topics document_processing worker started",
            extra=self._log_extra(worker_id=worker_id),
        )

        async with async_session_maker() as session:
            async for task in ctx.iter_document_processing_tasks():
                try:
                    await self._source.process_document(
                        session,
                        task.document,
                        chunks=task.chunks,
                        document_title=task.document_title,
                        toc_json=task.toc,
                        extracted_text=task.extracted_text,
                        config=task.content_config,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    doc_name = str(task.document.get("name") or "")
                    logger.exception(
                        "Failed to process document",
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
                            "Failed to mark document error during processing",
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
                            "Failed to rollback session after document processing failure",
                            extra=self._log_extra(
                                worker_id=worker_id,
                                document_name=doc_name,
                                error=str(rb_exc),
                                error_type=type(rb_exc).__name__,
                            ),
                        )

    async def _fetch_map_toc_and_chunks(
        self, ctx: FluidTopicsPipelineContext, map_id: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
        """Fetch TOC + all topic contents (chunks) for a map.

        Returns: (toc, chunks, failed_count, skipped_count)
        """

        t0 = time.monotonic()
        payload = await fetch_map_toc(self, ctx, map_id)
        toc_nodes = normalize_map_toc_payload(payload)
        toc = ft_toc_to_kg_toc(toc_nodes)

        # Collect unique contentIds from the TOC tree.
        # (Fluid Topics can repeat nodes across branches; we de-duplicate to avoid redundant fetches.)
        content_requests: list[tuple[str, str]] = []
        seen_content_ids: set[str] = set()
        for content_id, title in iter_ft_toc_content_nodes(toc_nodes):
            if content_id in seen_content_ids:
                continue
            seen_content_ids.add(content_id)
            content_requests.append((content_id, title))

        if len(content_requests) == 0:
            logger.info(
                "Fluid Topics map has empty TOC / no content nodes",
                extra=self._log_extra(map_id=map_id, toc_root_nodes=len(toc_nodes)),
            )
            return toc, [], 0, 0

        fetch_tasks = []
        for content_id, _ in content_requests:
            fetch_tasks.append(fetch_topic_content(self, ctx, map_id, content_id))

        logger.debug(
            "Fetching Fluid Topics topics for map",
            extra=self._log_extra(
                map_id=map_id,
                topics=len(fetch_tasks),
                toc_root_nodes=len(toc_nodes),
            ),
        )

        fetched_topics = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        chunks: list[dict[str, Any]] = []
        failed = 0
        skipped = 0
        for (content_id, title), fetched_content in zip(
            content_requests, fetched_topics, strict=False
        ):
            if isinstance(fetched_content, Exception):
                logger.error(
                    "Failed to fetch Fluid Topics topic content",
                    extra=self._log_extra(
                        map_id=map_id,
                        content_id=content_id,
                        title=title,
                        error=str(fetched_content),
                        error_type=type(fetched_content).__name__,
                    ),
                )
                failed += 1
                continue

            if not fetched_content:
                skipped += 1
                continue

            chunks.append(
                {
                    "title": title or content_id,
                    "toc_reference": title or content_id,
                    "page": None,
                    "text": fetched_content,
                    "type": "TOPIC",
                }
            )

        elapsed_ms = (time.monotonic() - t0) * 1000.0
        logger.debug(
            "Fetched Fluid Topics map content",
            extra=self._log_extra(
                map_id=map_id,
                toc_root_nodes=len(toc_nodes),
                topics_total=len(content_requests),
                topics_ok=len(chunks),
                topics_failed=int(failed),
                topics_skipped=int(skipped),
                elapsed_ms=elapsed_ms,
            ),
        )

        return toc, chunks, failed, skipped

    def _worker_validation(self) -> None:
        if not self._client or not self._state:
            raise RuntimeError(
                "Attempt to run pipeline worker outside of pipeline context."
            )

    def _log_extra(self, **extra: Any) -> dict[str, Any]:
        return {"graph_id": self._graph_id, "source_id": self._source_id, **extra}
