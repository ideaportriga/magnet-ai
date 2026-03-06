import asyncio
import logging
import time
from pathlib import PurePath
from typing import TYPE_CHECKING, Any, override
from urllib.parse import urlparse, urlunparse
from uuid import UUID

import httpx
from litestar.exceptions import ClientException

from core.config.base import get_knowledge_source_settings
from core.db.models.knowledge_graph import KnowledgeGraphChunk
from core.db.session import async_session_maker
from utils.datetime_utils import parse_date_string

from ...content_config_services import (
    get_content_config,
    get_structured_content_config,
)
from ...metadata_services import accumulate_discovered_metadata_fields
from ...models import MetadataMultiValueContainer, SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .fluid_topics_models import (
    FluidTopicsContentFetchTask,
    FluidTopicsDocumentFetchTask,
    FluidTopicsListingTask,
    FluidTopicsMapFetchTask,
    FluidTopicsRuntimeConfig,
    FluidTopicsSharedSyncState,
    ProcessDocumentTask,
)
from .fluid_topics_utils import (
    download_file,
    fetch_map_structure,
    fetch_map_toc,
    fetch_topic_content,
    ft_toc_to_kg_toc,
    iter_ft_toc_content_nodes,
    normalize_map_toc_payload,
    parse_fluid_topics_metadata_list,
)

if TYPE_CHECKING:
    from .fluid_topics_source import FluidTopicsSource

logger = logging.getLogger(__name__)

FluidTopicsPipelineContext = SyncPipelineContext[
    FluidTopicsListingTask, FluidTopicsContentFetchTask, ProcessDocumentTask
]

# Fluid Topics "intelligent sync" notes:
# - We compute `content_hash` and use `source_document_id` (mapId/documentId) to detect unchanged content.
# - When the stored hash matches, we do a metadata-only update and skip re-processing (chunking/embedding).
# - We still download/fetch the content to compute the hash; further optimization would require an API-provided
#   ETag/lastModified check that lets us skip downloads.


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
        self._viewer_base_url = self._resolve_viewer_base_url()

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
                counters = await self._run_pipeline(
                    listing_worker=self._listing_worker,
                    content_fetch_worker=self._content_fetch_worker,
                    document_processing_worker=self._document_processing_worker,
                )

                try:
                    counters.deleted = await self.cleanup_orphaned_documents(
                        graph_id=UUID(self._graph_id),
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
                            doc_id = str(doc_info.get("id"))
                            doc_filename = str(doc_info.get("filename"))
                            doc_title = str(doc_info.get("title") or "").strip() or None
                            doc_link = self._build_document_external_link(
                                doc_info.get("viewerUrl")
                            )
                            doc_metadata = parse_fluid_topics_metadata_list(
                                doc_info.get("metadata")
                            )
                            if not doc_id or not doc_filename:
                                await ctx.inc("skipped")
                                continue

                            await self.track_source_document_id(doc_id)

                            await ctx.content_fetch_queue.put(
                                FluidTopicsDocumentFetchTask(
                                    id=doc_id,
                                    filename=doc_filename,
                                    title=doc_title,
                                    metadata=doc_metadata,
                                    last_edition_date=doc_info.get("lastEditionDate"),
                                    external_link=doc_link,
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

                                await self.track_source_document_id(map_id)

                                if map_id not in self._state.seen_maps:
                                    self._state.seen_maps[map_id] = map_title
                                else:
                                    # We intentionally ingest a map only once even if it appears in multiple
                                    # search results (e.g. because multiple topics match the search query).
                                    await ctx.dec("total_found")
                                    continue

                            await ctx.content_fetch_queue.put(
                                FluidTopicsMapFetchTask(
                                    id=map_id,
                                    title=map_title,
                                    metadata_from_structure=True,
                                )
                            )

                            maps_enqueued += 1
                            continue

                        if entry_type == "MAP":
                            if (
                                not self._fluid_topics_config.map_content_url_template
                                or not self._fluid_topics_config.map_toc_url_template
                            ):
                                await ctx.inc("skipped")
                                continue

                            async with self._state.seen_maps_lock:
                                map_info = entry.get("map") or {}
                                map_id = str(map_info.get("mapId") or "")
                                map_title = str(map_info.get("title") or "")
                                map_metadata = parse_fluid_topics_metadata_list(
                                    map_info.get("metadata")
                                )
                                if not map_id:
                                    await ctx.inc("skipped")
                                    continue

                                await self.track_source_document_id(map_id)

                                if map_id not in self._state.seen_maps:
                                    self._state.seen_maps[map_id] = map_title
                                else:
                                    # We intentionally ingest a map only once even if it appears in multiple
                                    # search results (e.g. because multiple topics match the search query).
                                    await ctx.dec("total_found")
                                    continue

                            await ctx.content_fetch_queue.put(
                                FluidTopicsMapFetchTask(
                                    id=map_id,
                                    title=map_title,
                                    metadata=map_metadata,
                                    last_edition_date=map_info.get("lastEditionDate"),
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

        graph_uuid = UUID(self._graph_id)
        source_uuid = self._source.source.id

        def _to_discovery_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
            """Convert JSON-friendly metadata dict into discovery-friendly values."""
            if not isinstance(meta, dict) or not meta:
                return {}
            out: dict[str, Any] = {}
            for k, v in meta.items():
                key = str(k or "").strip()
                if not key:
                    continue
                if isinstance(v, list):
                    # Expand multi-valued fields for discovery stats.
                    out[key] = MetadataMultiValueContainer.from_iterable(v)
                else:
                    out[key] = v
            return out

        async with async_session_maker() as session:
            async for task in ctx.iter_content_fetch_tasks():
                try:
                    if isinstance(task, FluidTopicsMapFetchTask):
                        map_id = task.id
                        map_title = task.title or map_id
                        doc_name = map_title.strip()
                        map_metadata = task.metadata
                        map_last_edition_date = task.last_edition_date
                        external_link: str | None = None
                        structure: dict[str, Any] | None = None

                        # For TOPIC search entries, Fluid Topics doesn't include map metadata in the search
                        # response. We fetch it from the map structure endpoint when available.
                        if task.metadata_from_structure:
                            if not self._fluid_topics_config.map_structure_url_template:
                                logger.warning(
                                    "Skipping Fluid Topics map structure metadata fetch: FLUID_TOPICS_MAP_STRUCTURE is not configured",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        map_id=map_id,
                                        map_title=map_title,
                                    ),
                                )
                            else:
                                try:
                                    structure = await fetch_map_structure(
                                        self, ctx, str(map_id)
                                    )
                                    if isinstance(structure, dict):
                                        structure_title = str(
                                            structure.get("title") or ""
                                        ).strip()
                                        if structure_title:
                                            map_title = structure_title

                                        structure_metadata = (
                                            parse_fluid_topics_metadata_list(
                                                structure.get("metadata")
                                            )
                                        )
                                        map_last_edition_date = structure.get(
                                            "lastEdition"
                                        )
                                        external_link = self._build_map_external_link(
                                            structure.get("readerUrl")
                                        )

                                        # Also persist common top-level structure fields under familiar keys
                                        # (keeps metadata consistent between MAP vs TOPIC ingestion paths).
                                        top_level: dict[str, Any] = {}
                                        lang = str(structure.get("lang") or "").strip()
                                        origin_id = str(
                                            structure.get("originId") or ""
                                        ).strip()
                                        base_id = str(
                                            structure.get("baseId") or ""
                                        ).strip()
                                        cluster_id = str(
                                            structure.get("clusterId") or ""
                                        ).strip()

                                        if structure_title:
                                            top_level["ft:title"] = structure_title
                                        if lang:
                                            top_level["ft:locale"] = lang
                                        if origin_id:
                                            top_level["ft:originId"] = origin_id
                                        if base_id:
                                            top_level["ft:baseId"] = base_id
                                        if cluster_id:
                                            top_level["ft:clusterId"] = cluster_id

                                        map_metadata = {
                                            **(structure_metadata or {}),
                                            **top_level,
                                        } or None
                                except Exception as meta_exc:  # noqa: BLE001
                                    logger.warning(
                                        "Failed to fetch Fluid Topics map structure metadata",
                                        extra=self._log_extra(
                                            worker_id=worker_id,
                                            map_id=map_id,
                                            map_title=map_title,
                                            error=str(meta_exc),
                                            error_type=type(meta_exc).__name__,
                                        ),
                                    )
                        else:
                            # MAP entries have metadata in search results, but readerUrl lives in
                            # the map structure endpoint; fetch it only to resolve external_link.
                            if (
                                self._viewer_base_url
                                and self._fluid_topics_config.map_structure_url_template
                            ):
                                try:
                                    structure = await fetch_map_structure(
                                        self, ctx, str(map_id)
                                    )
                                    if isinstance(structure, dict):
                                        external_link = self._build_map_external_link(
                                            structure.get("readerUrl")
                                        )
                                except Exception as meta_exc:  # noqa: BLE001
                                    logger.warning(
                                        "Failed to fetch Fluid Topics map readerUrl",
                                        extra=self._log_extra(
                                            worker_id=worker_id,
                                            map_id=map_id,
                                            map_title=map_title,
                                            error=str(meta_exc),
                                            error_type=type(meta_exc).__name__,
                                        ),
                                    )

                        # Best-effort: persist discovered metadata fields for this graph/source.
                        if map_metadata:
                            try:
                                await accumulate_discovered_metadata_fields(
                                    session,
                                    graph_id=graph_uuid,
                                    source_id=source_uuid,
                                    metadata=_to_discovery_metadata(map_metadata),
                                    origin="source",
                                )
                                await session.commit()
                            except Exception as meta_db_exc:  # noqa: BLE001
                                await session.rollback()
                                logger.error(
                                    "Failed to persist Fluid Topics discovered map metadata",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        map_id=map_id,
                                        map_title=map_title,
                                        error=str(meta_db_exc),
                                        error_type=type(meta_db_exc).__name__,
                                    ),
                                )

                        logger.debug(
                            "Fetching Fluid Topics map",
                            extra=self._log_extra(
                                worker_id=worker_id, map_id=map_id, map_title=map_title
                            ),
                        )

                        (
                            full_content,
                            toc,
                            chunks,
                            failed,
                            skipped,
                        ) = await self._get_fluid_topics_data(ctx, map_id)

                        if failed:
                            await ctx.inc("failed", int(failed))
                        if skipped:
                            await ctx.inc("skipped", int(skipped))

                        map_source_modified_at = parse_date_string(
                            map_last_edition_date
                        )
                        content_config = await get_structured_content_config(
                            session,
                            UUID(self._graph_id),
                            source_id=str(self._source.source.id),
                            source_type=self._source.source.type,
                        )

                        result = await self.store_document(
                            session,
                            self._source.source,
                            content=full_content,
                            graph_id=self._graph_id,
                            source_document_id=str(map_id),
                            filename=doc_name,
                            source_modified_at=map_source_modified_at,
                            source_metadata=map_metadata,
                            default_document_type="html",
                            content_config=content_config,
                            title=str(map_title),
                            toc=toc,
                            external_link=external_link,
                        )
                        if not result.document:
                            await ctx.inc("metadata_only_updated")
                            continue

                        await ctx.inc("content_changed")

                        await ctx.document_processing_queue.put(
                            ProcessDocumentTask(
                                content_config=content_config,
                                document=result.document,
                                document_title=str(map_title),
                                chunks=chunks,
                                toc=toc,
                                extracted_text=full_content,
                                external_link=external_link,
                                source_modified_at=map_source_modified_at,
                            )
                        )
                        continue

                    if isinstance(task, FluidTopicsDocumentFetchTask):
                        doc_id = task.id
                        filename = task.filename

                        content_config = await get_content_config(
                            session,
                            self._graph_id,
                            filename,
                            source_id=str(self._source.source.id),
                            source_type=self._source.source.type,
                        )
                        if not content_config:
                            logger.warning(
                                "Skipping Fluid Topics document: no content config found",
                                extra=self._log_extra(
                                    worker_id=worker_id, doc_filename=filename
                                ),
                            )
                            await ctx.inc("skipped")
                            continue

                        # Best-effort: persist discovered metadata fields for this graph/source.
                        if task.metadata:
                            try:
                                await accumulate_discovered_metadata_fields(
                                    session,
                                    graph_id=graph_uuid,
                                    source_id=source_uuid,
                                    metadata=_to_discovery_metadata(task.metadata),
                                    origin="source",
                                )
                                await session.commit()
                            except Exception as meta_db_exc:  # noqa: BLE001
                                await session.rollback()
                                logger.error(
                                    "Failed to persist Fluid Topics discovered document metadata",
                                    extra=self._log_extra(
                                        worker_id=worker_id,
                                        doc_filename=filename,
                                        error=str(meta_db_exc),
                                        error_type=type(meta_db_exc).__name__,
                                    ),
                                )

                        logger.debug(
                            "Downloading Fluid Topics file",
                            extra=self._log_extra(
                                worker_id=worker_id, doc_filename=filename
                            ),
                        )
                        file_bytes = await download_file(self, ctx, filename)

                        source_modified_at = parse_date_string(task.last_edition_date)

                        result = await self.store_document(
                            session,
                            self._source.source,
                            content=file_bytes,
                            graph_id=graph_uuid,
                            source_document_id=str(doc_id),
                            filename=filename,
                            source_modified_at=source_modified_at,
                            source_metadata=task.metadata,
                            default_document_type="pdf",
                            content_config=content_config,
                            title=str(task.title) if task.title else None,
                            external_link=task.external_link,
                        )
                        if not result.document:
                            await ctx.inc("metadata_only_updated")
                            continue

                        await ctx.inc("content_changed")

                        await ctx.document_processing_queue.put(
                            ProcessDocumentTask(
                                content_config=content_config,
                                document=result.document,
                                document_title=task.title,
                                extracted_text=result.loaded_content["text"],
                                external_link=task.external_link,
                                source_modified_at=source_modified_at,
                            )
                        )
                        continue

                    logger.warning(
                        "Unknown Fluid Topics content_fetch task",
                        extra=self._log_extra(
                            worker_id=worker_id, task_type=type(task).__name__
                        ),
                    )

                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Failed to fetch topic/document content from Fluid Topics",
                        extra=self._log_extra(
                            worker_id=worker_id,
                            task_type=type(task).__name__,
                            doc_filename=getattr(task, "filename", None),
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
                                task_type=type(task).__name__,
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
                                task_type=type(task).__name__,
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
                doc_name = str(task.document.get("name") or "").strip()
                filename_fallback_title = (
                    PurePath(doc_name).stem if doc_name else doc_name
                )
                resolved_document_title = (
                    str(task.document_title or "").strip() or filename_fallback_title
                )
                try:
                    await self._source.process_document(
                        session,
                        task.document,
                        chunks=task.chunks,
                        document_title=resolved_document_title,
                        toc_json=task.toc,
                        extracted_text=task.extracted_text,
                        config=task.content_config,
                        external_link=task.external_link,
                        source_modified_at=task.source_modified_at,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
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

    async def _get_fluid_topics_data(
        self, ctx: FluidTopicsPipelineContext, map_id: str
    ) -> tuple[str, list[dict[str, Any]], list[KnowledgeGraphChunk], int, int]:
        """Fetch TOC + all topic contents (chunks) for a map.

        Returns: (full_content, toc, chunks, failed_count, skipped_count)
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
            return "", toc, [], 0, 0

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
        chunks: list[KnowledgeGraphChunk] = []
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

            content, embedded_content = fetched_content

            chunks.append(
                KnowledgeGraphChunk(
                    chunk_type="TOPIC",
                    title=title or content_id,
                    toc_reference=title or content_id,
                    content=content,
                    content_format="html",
                    embedded_content=embedded_content,
                )
            )

        full_content = "\n".join(c.content for c in chunks if c.content)

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

        return full_content, toc, chunks, failed, skipped

    def _worker_validation(self) -> None:
        if not self._client or not self._state:
            raise RuntimeError(
                "Attempt to run pipeline worker outside of pipeline context."
            )

    def _log_extra(self, **extra: Any) -> dict[str, Any]:
        return {"graph_id": self._graph_id, "source_id": self._source_id, **extra}

    def _resolve_viewer_base_url(self) -> str | None:
        settings = get_knowledge_source_settings()
        base_url = str(
            getattr(settings, "FLUID_TOPICS_VIEWER_BASE_URL", "") or ""
        ).strip()
        return base_url or None

    def _build_document_external_link(self, viewer_url: str | None) -> str | None:
        url = str(viewer_url or "").strip()
        if not url:
            return None
        if not self._viewer_base_url:
            return url
        parsed_base = urlparse(self._viewer_base_url)
        parsed_viewer = urlparse(url)
        replaced = parsed_viewer._replace(
            scheme=parsed_base.scheme or parsed_viewer.scheme,
            netloc=parsed_base.netloc or parsed_viewer.netloc,
        )
        return urlunparse(replaced)

    def _build_map_external_link(self, reader_url: str | None) -> str | None:
        if not self._viewer_base_url:
            return None
        rel = str(reader_url or "").strip()
        if not rel:
            return None
        base = self._viewer_base_url.rstrip("/")
        if not rel.startswith("/"):
            rel = f"/{rel}"
        return f"{base}{rel}"
