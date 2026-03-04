from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, override
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource, docs_table_name
from services.observability import observability_context, observe

from ...metadata_services import accumulate_discovered_metadata_fields
from ...models import SourceType, SyncCounters
from ..abstract_source import AbstractDataSource
from .salesforce_models import (
    SALESFORCE_DEFAULT_METADATA_FIELDS,
    SalesforceRuntimeConfig,
)
from .salesforce_utils import (
    build_soql_query,
    create_salesforce_connection,
    extract_template_fields,
    resolve_salesforce_credentials,
    validate_salesforce_runtime_config,
)

logger = logging.getLogger(__name__)


class SalesforceDataSource(AbstractDataSource):
    """Salesforce Knowledge Base source for Knowledge Graph.

    Queries Salesforce Knowledge Article View objects via SOQL and ingests each article
    as a Knowledge Graph document. Content is rendered using a single configurable
    format-string template; an optional SOQL WHERE filter narrows the record set.
    """

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.SALESFORCE:
            raise ValueError("Source must be a Salesforce source")
        super().__init__(source)

    @override
    def extract_source_document_id(self, source_item: Any) -> str | None:
        if isinstance(source_item, dict):
            return source_item.get("Id") or None
        return None

    @override
    def extract_source_modified_at(self, source_item: Any) -> datetime | None:
        if isinstance(source_item, dict):
            modified = source_item.get("LastModifiedDate")
            if isinstance(modified, datetime):
                return modified
            if isinstance(modified, str):
                try:
                    return datetime.fromisoformat(modified.replace("Z", "+00:00"))
                except Exception:  # noqa: BLE001
                    return None
        return None

    @override
    @observe(name="Sync Salesforce source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Synchronize Salesforce Knowledge articles into the Knowledge Graph."""

        logger.info(
            "Salesforce KG sync started",
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        cfg = await self._get_sync_config()
        embedding_model = await self._require_embedding_model(db_session)

        observability_context.update_current_span(
            input={
                "source_id": str(self.source.id),
                "object_api_name": cfg.object_api_name,
            }
        )

        counters = SyncCounters()
        seen_source_document_ids: set[str] = set()

        try:
            # --- 1. Fetch all records from Salesforce ---
            records = await self._fetch_records(cfg)
            counters.total_found = len(records)

            logger.info(
                "Salesforce SOQL returned %d records",
                len(records),
                extra={
                    "graph_id": str(self.source.graph_id),
                    "source_id": str(self.source.id),
                },
            )

            # --- 2. Load existing documents for change detection ---
            existing_docs = await self._load_existing_doc_map(db_session)

            # --- 3. Process each record ---
            for record in records:
                record_id: str | None = record.get("Id")
                if not record_id:
                    logger.warning("Skipping Salesforce record without Id")
                    counters.skipped += 1
                    continue

                seen_source_document_ids.add(record_id)

                try:
                    await self._process_record(
                        db_session=db_session,
                        record=record,
                        cfg=cfg,
                        embedding_model=embedding_model,
                        existing_docs=existing_docs,
                        counters=counters,
                    )
                except Exception as exc:  # noqa: BLE001
                    title = record.get("Title", record_id)
                    logger.error(
                        "Failed to process Salesforce record '%s': %s",
                        title,
                        exc,
                        exc_info=True,
                        extra={
                            "graph_id": str(self.source.graph_id),
                            "source_id": str(self.source.id),
                            "record_id": record_id,
                        },
                    )
                    counters.failed += 1

            # --- 4. Orphan cleanup ---
            try:
                counters.deleted = await self._cleanup_orphaned_documents(
                    db_session, seen_source_document_ids
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.warning(
                    "Salesforce orphan cleanup failed: %s",
                    cleanup_exc,
                    exc_info=True,
                )

        finally:
            await self._finalize(db_session, counters=counters)

        summary: dict[str, Any] = {
            "source_id": str(self.source.id),
            "object_api_name": cfg.object_api_name,
            "total_found": counters.total_found,
            "synced": counters.synced,
            "unchanged_skipped": counters.unchanged_skipped,
            "failed": counters.failed,
            "skipped": counters.skipped,
            "deleted": counters.deleted,
            "status": self.source.status,
            "last_sync_at": self.source.last_sync_at,
        }

        logger.info("Salesforce KG sync completed", extra=summary)
        observability_context.update_current_span(output=summary)
        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_records(
        self, cfg: SalesforceRuntimeConfig
    ) -> list[dict[str, Any]]:
        """Connect to Salesforce and execute the SOQL query."""
        sf = await create_salesforce_connection(cfg)
        query = build_soql_query(cfg)

        logger.debug(
            "Executing SOQL: %s",
            query,
            extra={"source_id": str(self.source.id)},
        )

        result = await asyncio.to_thread(sf.query_all, query)
        return result.get("records", [])

    async def _load_existing_doc_map(
        self, db_session: AsyncSession
    ) -> dict[str, dict[str, Any]]:
        """Return a map of source_document_id → {id, source_modified_at} for this source."""
        docs_table = docs_table_name(self.source.graph_id)
        result = await db_session.execute(
            text(
                f"""
                SELECT id::text, source_document_id, source_modified_at
                FROM {docs_table}
                WHERE source_id = :sid AND source_document_id IS NOT NULL
                """
            ),
            {"sid": str(self.source.id)},
        )
        return {
            row.source_document_id: {
                "id": row.id,
                "source_modified_at": row.source_modified_at,
            }
            for row in result.all()
            if row.source_document_id
        }

    async def _process_record(
        self,
        *,
        db_session: AsyncSession,
        record: dict[str, Any],
        cfg: SalesforceRuntimeConfig,
        embedding_model: str,
        existing_docs: dict[str, dict[str, Any]],
        counters: SyncCounters,
    ) -> None:
        record_id: str = record["Id"]
        title: str = record.get("Title") or record_id
        source_modified_at = self.extract_source_modified_at(record)

        # --- Change detection: skip if not modified ---
        existing = existing_docs.get(record_id)
        if existing and source_modified_at:
            existing_modified = existing.get("source_modified_at")
            if isinstance(existing_modified, datetime) and _datetimes_equal(
                existing_modified, source_modified_at
            ):
                counters.unchanged_skipped += 1
                return

        # --- Render content ---
        content_text = self._render_content(record, cfg.content_template)
        if not content_text or not content_text.strip():
            logger.warning(
                "Skipping record '%s': rendered content is empty",
                title,
                extra={"source_id": str(self.source.id), "record_id": record_id},
            )
            counters.skipped += 1
            return

        # --- Build metadata dicts ---
        source_metadata = self._extract_metadata(record, cfg.metadata_fields)
        content_hash = _sha256(content_text)

        # --- Create/update document ---
        document = await self.create_document_for_source(
            db_session,
            filename=f"{record_id}.txt",
            source_document_id=record_id,
            source_modified_at=source_modified_at,
            content_hash=content_hash,
            source_metadata=source_metadata,
            default_document_type="txt",
        )

        # --- Process (chunk + embed) ---
        await self.process_document(
            db_session,
            document,
            extracted_text=content_text,
            embedding_model=embedding_model,
            document_title=title,
        )

        # --- Accumulate metadata for discovery ---
        try:
            await accumulate_discovered_metadata_fields(
                db_session,
                graph_id=self.source.graph_id,
                source_id=self.source.id,
                metadata=source_metadata,
                origin="source",
            )
        except Exception as meta_exc:  # noqa: BLE001
            logger.debug(
                "Metadata discovery accumulation failed for record %s: %s",
                record_id,
                meta_exc,
            )

        counters.synced += 1

    def _render_content(self, record: dict[str, Any], template: str) -> str:
        """Render the content template using record field values."""
        try:
            # Filter record to only include keys referenced in the template
            fields = extract_template_fields(template)
            safe_record = {f: (record.get(f) or "") for f in fields}
            return template.format(**safe_record)
        except (KeyError, ValueError) as exc:
            raise ClientException(
                f"Failed to render content template for record '{record.get('Id')}': {exc}"
            ) from exc

    def _extract_metadata(
        self, record: dict[str, Any], metadata_fields: tuple[str, ...]
    ) -> dict[str, Any]:
        """Extract configured metadata fields from the record."""
        result: dict[str, Any] = {}
        for field_name in metadata_fields:
            value = record.get(field_name)
            if value is not None:
                result[field_name] = value
        # Always include these base fields
        for base_field in ("Title", "ArticleNumber", "UrlName", "KnowledgeArticleId"):
            if base_field in record and base_field not in result:
                value = record.get(base_field)
                if value is not None:
                    result[base_field] = value
        return result

    async def _cleanup_orphaned_documents(
        self, db_session: AsyncSession, seen_ids: set[str]
    ) -> int:
        """Delete KG documents whose Salesforce record was not seen in this sync run."""
        docs_table = docs_table_name(self.source.graph_id)
        result = await db_session.execute(
            text(
                f"""
                SELECT id::text, source_document_id, name
                FROM {docs_table}
                WHERE source_id = :sid
                """
            ),
            {"sid": str(self.source.id)},
        )

        existing_docs = result.all()
        orphaned: list[tuple[str, str, str]] = []

        for doc_id, source_doc_id, doc_name in existing_docs:
            if source_doc_id and source_doc_id not in seen_ids:
                orphaned.append((doc_id, source_doc_id, doc_name))

        if not orphaned:
            return 0

        logger.info(
            "Deleting %d orphaned Salesforce documents",
            len(orphaned),
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        from core.domain.knowledge_graph.service import KnowledgeGraphDocumentService

        doc_service = KnowledgeGraphDocumentService()
        deleted = 0
        for doc_id, source_doc_id, doc_name in orphaned:
            try:
                await doc_service.delete_document(
                    db_session,
                    graph_id=self.source.graph_id,
                    id=UUID(doc_id),
                )
                deleted += 1
                logger.debug(
                    "Deleted orphaned Salesforce document '%s' (source_document_id=%s)",
                    doc_name,
                    source_doc_id,
                    extra={"source_id": str(self.source.id)},
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to delete orphaned document '%s': %s",
                    doc_id,
                    exc,
                )

        return deleted

    async def _get_sync_config(self) -> SalesforceRuntimeConfig:
        cfg = self.source.config or {}

        object_api_name = str(cfg.get("object_api_name") or "").strip()
        content_template = str(cfg.get("content_template") or "").strip()
        provider_system_name = str(cfg.get("provider_system_name") or "").strip()

        # Metadata fields: prefer explicitly configured list, fall back to defaults
        raw_metadata_fields = cfg.get("metadata_fields")
        if isinstance(raw_metadata_fields, list) and raw_metadata_fields:
            metadata_fields = tuple(
                str(f).strip() for f in raw_metadata_fields if str(f).strip()
            )
        else:
            metadata_fields = SALESFORCE_DEFAULT_METADATA_FIELDS

        creds = await resolve_salesforce_credentials(cfg)

        runtime_cfg = SalesforceRuntimeConfig(
            object_api_name=object_api_name,
            content_template=content_template,
            metadata_fields=metadata_fields,
            provider_system_name=provider_system_name,
            username=creds.get("username", ""),
            password=creds.get("password", ""),
            security_token=creds.get("security_token", ""),
            client_id=creds.get("client_id", ""),
            client_secret=creds.get("client_secret", ""),
            domain=creds.get("domain", "login"),
        )

        validate_salesforce_runtime_config(runtime_cfg)
        return runtime_cfg


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _datetimes_equal(a: datetime, b: datetime) -> bool:
    """Compare two datetimes ignoring timezone info (compare UTC values)."""
    a_utc = a.astimezone(timezone.utc).replace(tzinfo=None) if a.tzinfo else a
    b_utc = b.astimezone(timezone.utc).replace(tzinfo=None) if b.tzinfo else b
    return a_utc == b_utc
