import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override
from uuid import UUID

from atlassian import Confluence
from litestar.exceptions import ClientException

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .confluence_models import (
    ConfluenceListingPageTask,
    ConfluencePageFetchTask,
    ConfluenceProcessDocumentTask,
    ConfluenceRuntimeConfig,
)

if TYPE_CHECKING:
    from .confluence_source import ConfluenceSource

logger = logging.getLogger(__name__)

ConfluencePipelineContext = SyncPipelineContext[
    ConfluenceListingPageTask, ConfluencePageFetchTask, ConfluenceProcessDocumentTask
]


class ConfluenceSyncPipeline(
    SyncPipeline[
        ConfluenceListingPageTask,
        ConfluencePageFetchTask,
        ConfluenceProcessDocumentTask,
    ]
):
    """Confluence pages sync pipeline.

    Stage overview:
    - **Listing** (1 worker): paginates through ``get_all_pages_from_space`` and fans
      out one :class:`ConfluencePageFetchTask` per page.  Self-enqueues next-page
      listing tasks until the space is exhausted.
    - **Content-fetch** (N workers): resolves the optional root-ancestor title prefix
      (one extra API call per page when ``include_root_prefix=True``) and produces a
      :class:`ConfluenceProcessDocumentTask`.
    - **Document-processing** (N workers): stores the HTML body via
      :meth:`~SyncPipeline.store_document` (partial-sync hash gate), then delegates
      to :meth:`~AbstractDataSource.process_document` for chunking + embedding.
    """

    def __init__(
        self,
        source: "ConfluenceSource",
        pipeline_config: SyncPipelineConfig,
        confluence_config: ConfluenceRuntimeConfig,
        embedding_model: str,
    ) -> None:
        super().__init__(config=pipeline_config)
        self._source = source
        self._graph_id = str(source.source.graph_id)
        self._source_id = str(source.source.id)
        self._confluence_config = confluence_config
        self._embedding_model = embedding_model

        # Atlassian client — constructed synchronously (no network call at init time)
        self._confluence = Confluence(
            url=confluence_config.endpoint,
            username=confluence_config.username,
            password=confluence_config.token,
        )

        # Resolved lazily in run() before any workers start.  For Confluence Cloud
        # this will be ``https://host/wiki``; for Server/DC it will be
        # ``https://host``.  Using ``_links.base`` from the API avoids the need to
        # hard-code the ``/wiki`` prefix ourselves.
        self._base_link: str = ""

    # ------------------------------------------------------------------
    # Pipeline entry-points
    # ------------------------------------------------------------------

    @override
    async def bootstrap(self, ctx: ConfluencePipelineContext) -> None:
        await ctx.listing_queue.put(ConfluenceListingPageTask(start=0, limit=100))

    @override
    async def run(self) -> SyncCounters:
        # Resolve the Confluence base URL (e.g. ``https://host/wiki`` for Cloud,
        # ``https://host`` for Server/DC) so that ``_links.webui`` paths can be
        # turned into correct absolute URLs.
        await self._resolve_base_link()

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
                "Confluence: orphaned document cleanup failed",
                extra=self._log_extra(error=str(cleanup_exc)),
            )

        return counters

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_base_link(self) -> None:
        """Fetch ``_links.base`` from the Confluence API and cache it.

        Confluence Cloud returns something like ``https://host/wiki``; Confluence
        Server / Data Center returns ``https://host`` (no ``/wiki`` suffix).  The
        value is used in :meth:`_content_fetch_worker` to build absolute page URLs
        from the relative ``_links.webui`` paths returned by the content API.
        """
        cfg = self._confluence_config
        try:
            result: dict[str, Any] = await asyncio.to_thread(
                self._confluence.get,
                "rest/api/content",
                params={"spaceKey": cfg.space_key, "limit": 1},
            )
            base = (result.get("_links") or {}).get("base") or ""
            self._base_link = base.rstrip("/")
            logger.debug(
                "Confluence: resolved base link '%s'",
                self._base_link,
                extra=self._log_extra(),
            )
        except Exception as exc:  # noqa: BLE001
            # Non-fatal: fall back to cfg.endpoint (same behaviour as before)
            logger.warning(
                "Confluence: could not resolve base link, falling back to endpoint: %s",
                exc,
                extra=self._log_extra(),
            )
            self._base_link = cfg.endpoint.rstrip("/")

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    async def _listing_worker(
        self, ctx: ConfluencePipelineContext, worker_id: int
    ) -> None:
        """Paginate through the Confluence space and fan out page tasks."""

        async for task in ctx.iter_listing_tasks():
            cfg = self._confluence_config

            logger.info(
                "Confluence: fetching pages from space '%s' (start=%s, limit=%s)",
                cfg.space_key,
                task.start,
                task.limit,
                extra=self._log_extra(),
            )

            try:
                pages: list[dict[str, Any]] = await asyncio.to_thread(
                    self._confluence.get_all_pages_from_space,
                    cfg.space_key,
                    task.start,
                    task.limit,
                    None,
                    "history,version,body.storage",
                    "page",
                )
            except Exception as exc:
                raise ClientException(
                    f"Confluence: failed to list pages from space '{cfg.space_key}': {exc}"
                ) from exc

            if not pages:
                logger.info(
                    "Confluence: no more pages at start=%s — listing complete",
                    task.start,
                    extra=self._log_extra(),
                )
                break

            await ctx.inc("total_found", len(pages))

            for raw in pages:
                body_storage = ((raw.get("body") or {}).get("storage") or {}).get(
                    "value"
                ) or ""

                version_when: str = (raw.get("version") or {}).get("when") or ""
                created_date: str = (raw.get("history") or {}).get("createdDate") or ""
                web_ui: str = (raw.get("_links") or {}).get("webui") or ""

                await ctx.content_fetch_queue.put(
                    ConfluencePageFetchTask(
                        page_id=str(raw.get("id") or ""),
                        title=str(raw.get("title") or raw.get("id") or ""),
                        html_body=body_storage,
                        last_modified=version_when,
                        created_at=created_date,
                        web_url=web_ui,
                    )
                )

            # If the batch was full, there may be more pages — schedule next batch
            if len(pages) >= task.limit:
                await ctx.listing_queue.put(
                    ConfluenceListingPageTask(
                        start=task.start + task.limit,
                        limit=task.limit,
                    )
                )

    async def _content_fetch_worker(
        self, ctx: ConfluencePipelineContext, worker_id: int
    ) -> None:
        """Resolve the optional root-ancestor title prefix, then pass downstream."""

        async for task in ctx.iter_content_fetch_tasks():
            cfg = self._confluence_config

            title = task.title
            if cfg.include_root_prefix and task.page_id:
                try:
                    ancestors: list[dict[str, Any]] = await asyncio.to_thread(
                        self._confluence.get_page_ancestors,
                        task.page_id,
                    )
                    # Mirror legacy: filter out subType ancestors, take first
                    root_ancestors = [a for a in ancestors if "subType" not in a]
                    if root_ancestors:
                        root_title = root_ancestors[0].get("title") or ""
                        if root_title:
                            title = f"{root_title}___{title}"
                except Exception as exc:  # noqa: BLE001
                    # Non-fatal: log and continue with the original title
                    logger.warning(
                        "Confluence: could not resolve root ancestor for page %s: %s",
                        task.page_id,
                        exc,
                        extra=self._log_extra(),
                    )

            # Resolve full source URL.
            # ``self._base_link`` is ``https://host/wiki`` for Confluence Cloud and
            # ``https://host`` for Server/DC (resolved once before listing starts).
            # ``task.web_url`` is the relative ``_links.webui`` path, e.g.
            # ``/spaces/SPACE/pages/ID/Title`` — prepending the base gives the
            # correct absolute URL for both deployment types.
            base = self._base_link or cfg.endpoint.rstrip("/")
            web_url = f"{base}{task.web_url}" if task.web_url else cfg.endpoint

            await ctx.document_processing_queue.put(
                ConfluenceProcessDocumentTask(
                    page_id=task.page_id,
                    title=title,
                    html_body=task.html_body,
                    last_modified=task.last_modified,
                    created_at=task.created_at,
                    web_url=web_url,
                )
            )

    async def _document_processing_worker(
        self, ctx: ConfluencePipelineContext, worker_id: int
    ) -> None:
        """Store and embed each Confluence page."""

        async for task in ctx.iter_document_processing_tasks():
            cfg = self._confluence_config

            source_modified_at = (
                datetime.fromisoformat(task.last_modified)
                .astimezone(UTC)
                .replace(tzinfo=None)
                if task.last_modified
                else None
            )

            # Build document metadata from resolved fields
            source_metadata: dict[str, Any] = {}
            available_meta = {
                "title": task.title,
                "version_when": task.last_modified,
                "created_date": task.created_at,
                "web_url": task.web_url,
            }
            for field in cfg.metadata_fields_list:
                if field in available_meta and available_meta[field]:
                    source_metadata[field] = available_meta[field]

            async with async_session_maker() as session:
                try:
                    store_result = await self.store_document(
                        session,
                        self._source.source,
                        content=task.html_body,
                        graph_id=self._graph_id,
                        filename=f"{task.page_id}.html",
                        source_document_id=task.page_id,
                        source_modified_at=source_modified_at,
                        source_metadata=source_metadata,
                        title=task.title,
                        external_link=task.web_url or None,
                    )

                    # Only mark as seen after the document is confirmed in the DB
                    await self.track_source_document_id(task.page_id)

                    if store_result.document is None:
                        # Content unchanged — metadata already updated by store_document
                        await ctx.inc("metadata_only_updated")
                        continue

                    await ctx.inc("content_changed")
                    content_config = await get_content_config(
                        session,
                        UUID(self._graph_id),
                        f"{task.page_id}.html",
                        source_id=self._source_id,
                        source_type=self._source.source.type,
                    )
                    await self._source.process_document(
                        session,
                        store_result.document,
                        extracted_text=task.html_body,
                        config=content_config,
                        document_title=task.title,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Confluence: failed to process page %s: %s",
                        task.page_id,
                        exc,
                        extra=self._log_extra(),
                        exc_info=True,
                    )
                    await ctx.inc("failed")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log_extra(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "graph_id": self._graph_id,
            "source_id": self._source_id,
            **kwargs,
        }
