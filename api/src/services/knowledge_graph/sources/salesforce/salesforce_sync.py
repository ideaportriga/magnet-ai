import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override
from uuid import UUID

from litestar.exceptions import ClientException
from simple_salesforce import Salesforce

from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...models import SyncCounters, SyncPipelineConfig
from ..sync_pipeline import SyncPipeline, SyncPipelineContext
from .salesforce_models import (
    SalesforceListingTask,
    SalesforceRecordTask,
    SalesforceRuntimeConfig,
)

if TYPE_CHECKING:
    from .salesforce_source import SalesforceSource

logger = logging.getLogger(__name__)

SalesforcePipelineContext = SyncPipelineContext[
    SalesforceListingTask, SalesforceRecordTask, SalesforceRecordTask
]


class SalesforceSyncPipeline(
    SyncPipeline[SalesforceListingTask, SalesforceRecordTask, SalesforceRecordTask]
):
    """Salesforce Knowledge Articles sync pipeline.

    Stage overview:
    - **Listing** (1 worker): issues a single SOQL ``query_all`` call and fans out each
      Knowledge Article record into the content-fetch queue.
    - **Content-fetch** (1 worker): trivial pass-through — Salesforce returns the full
      record payload in the listing response, so no additional fetch is needed.
    - **Document-processing** (N workers): formats each record using the ``output_config``
      template, detects unchanged content via SHA-256 hashing (partial-sync), and
      embeds + stores new/changed documents.
    """

    def __init__(
        self,
        source: "SalesforceSource",
        pipeline_config: SyncPipelineConfig,
        salesforce_config: SalesforceRuntimeConfig,
        embedding_model: str,
    ) -> None:
        super().__init__(config=pipeline_config)
        self._source = source
        self._graph_id = str(source.source.graph_id)
        self._source_id = str(source.source.id)
        self._salesforce_config = salesforce_config
        self._embedding_model = embedding_model

    @override
    async def bootstrap(self, ctx: SalesforcePipelineContext) -> None:
        await ctx.listing_queue.put(SalesforceListingTask())

    @override
    async def run(self) -> SyncCounters:
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

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    async def _listing_worker(
        self, ctx: SalesforcePipelineContext, worker_id: int
    ) -> None:
        """Issue the SOQL query and fan out records into the content-fetch queue."""

        async for _ in ctx.iter_listing_tasks():
            cfg = self._salesforce_config

            cols = cfg.columns_to_select
            if not cols:
                raise ClientException(
                    "Salesforce output_config contains no field placeholders. "
                    "Use {FieldName} syntax, e.g. '{Question__c}\\n{Answer__c}'."
                )

            # Build deduplicated SELECT column list:
            # Always include CreatedDate, LastModifiedDate,
            # the stable article_id_field and title_field, then
            # any fields referenced in output_config, then metadata_fields.
            _system = ["Id", "CreatedDate", "LastModifiedDate"]
            _extra = list(
                dict.fromkeys(
                    [cfg.article_id_field, cfg.title_field]
                    + cols
                    + cfg.metadata_fields_list
                )
            )
            _all_cols = _system + [c for c in _extra if c not in _system]
            soql = (
                f"SELECT {', '.join(_all_cols)} "
                f"FROM {cfg.object_api_name} "
                f"WHERE PublishStatus = 'Online'"
            )

            logger.info(
                "Salesforce: executing SOQL query",
                extra={**self._log_extra(), "object_api_name": cfg.object_api_name},
            )

            try:
                if cfg.auth_flow == "client_credentials":
                    logger.debug(
                        "Salesforce: connecting via Client Credentials flow",
                        extra=self._log_extra(),
                    )
                    sf = await asyncio.to_thread(
                        lambda: Salesforce(
                            consumer_key=cfg.client_id,
                            consumer_secret=cfg.client_secret,
                            domain=cfg.domain,
                        )
                    )
                else:
                    logger.debug(
                        "Salesforce: connecting via Password flow",
                        extra=self._log_extra(),
                    )
                    sf = await asyncio.to_thread(
                        lambda: Salesforce(
                            username=cfg.username,
                            password=cfg.password,
                            security_token=cfg.security_token,
                            domain=cfg.domain,
                        )
                    )
                result = await asyncio.to_thread(sf.query_all, soql)
            except Exception as exc:
                raise ClientException(f"Salesforce SOQL query failed: {exc}") from exc

            records: list[dict[str, Any]] = result.get("records", [])
            total = len(records)

            logger.info(
                "Salesforce: query returned %s records",
                total,
                extra=self._log_extra(),
            )

            await ctx.inc("total_found", total)

            for record in records:
                await ctx.content_fetch_queue.put(SalesforceRecordTask(record=record))

    async def _content_fetch_worker(
        self, ctx: SalesforcePipelineContext, worker_id: int
    ) -> None:
        """Pass-through worker — Salesforce already returns all field data in the listing."""

        async for task in ctx.iter_content_fetch_tasks():
            await ctx.document_processing_queue.put(task)

    async def _document_processing_worker(
        self, ctx: SalesforcePipelineContext, worker_id: int
    ) -> None:
        """Format article content and upsert into the Knowledge Graph."""

        async for task in ctx.iter_document_processing_tasks():
            record = task.record
            cfg = self._salesforce_config
            record_id: str = str(
                record.get(cfg.article_id_field) or record.get("Id") or ""
            )
            title: str = str(record.get(cfg.title_field) or record_id)

            content = self._salesforce_config.format_record(record)

            last_modified_str: str | None = record.get("LastModifiedDate")
            source_modified_at = (
                datetime.fromisoformat(last_modified_str)
                .astimezone(UTC)
                .replace(tzinfo=None)
                if last_modified_str
                else None
            )

            async with async_session_maker() as session:
                try:
                    store_result = await self.store_document(
                        session,
                        self._source.source,
                        content=content,
                        graph_id=self._graph_id,
                        filename=f"{record_id}.txt",
                        source_document_id=record_id,
                        source_modified_at=source_modified_at,
                        source_metadata={
                            field: record.get(field)
                            for field in cfg.metadata_fields_list
                            if record.get(field) is not None
                        },
                        title=title,
                    )

                    # Only mark as seen once the document is confirmed in the DB
                    await self.track_source_document_id(record_id)

                    if store_result.document is None:
                        await ctx.inc("metadata_only_updated")
                        continue

                    await ctx.inc("content_changed")
                    content_config = await get_content_config(
                        session,
                        UUID(self._graph_id),
                        f"{record_id}.txt",
                        source_id=self._source_id,
                        source_type=self._source.source.type,
                    )
                    await self._source.process_document(
                        session,
                        store_result.document,
                        extracted_text=content,
                        config=content_config,
                        document_title=title,
                        embedding_model=self._embedding_model,
                    )
                    await ctx.inc("synced")

                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Salesforce: failed to process record %s: %s",
                        record_id,
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
