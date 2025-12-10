from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, override

from office365.sharepoint.files.file import File
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from data_sources.sharepoint.source_documents import SharePointDocumentsDataSource
from data_sources.sharepoint.types import SharePointRootFolder
from data_sources.sharepoint.utils import create_sharepoint_client
from services.knowledge_graph import (
    get_content_config,
    get_graph_embedding_model,
    load_content_from_bytes,
)

from ..models import SourceType
from .abstract_source import AbstractDataSource
from ..store_services import docs_table_name
from litestar.exceptions import ClientException

logger = logging.getLogger(__name__)


async def _download_file_bytes(file: File) -> bytes:
    content = await asyncio.to_thread(lambda: file.get_content().execute_query())
    raw = getattr(content, "value", b"")
    return bytes(raw) if not isinstance(raw, (bytes, bytearray)) else raw


class SharePointDataSource(AbstractDataSource):
    def __init__(self) -> None:
        super().__init__("SharePoint", SourceType.SHAREPOINT)

    @override
    async def sync_source(
        self, db_session: AsyncSession, source: KnowledgeGraphSource
    ) -> dict[str, Any]:
        """Synchronize PDF documents from SharePoint into the Knowledge Graph."""
        if not source or source.type != self.type:
            raise ValueError("Source must be a SharePoint source")

        cfg = source.config or {}
        site_url = (cfg.get("sharepoint_site_url") or cfg.get("site_url") or "").strip()
        if not site_url:
            raise ValueError("SharePoint site URL is required in source.config")

        library, folder, recursive = self._resolve_location(cfg)

        logger.info(
            "Starting SharePoint sync for source %s (site=%s, library=%s, folder=%s, recursive=%s)",
            str(source.id),
            site_url,
            library,
            folder,
            recursive,
        )

        ctx = create_sharepoint_client(site_url)
        sp_source = SharePointDocumentsDataSource(
            ctx=ctx, library=library, folder=folder, recursive=recursive
        )

        files = await sp_source.get_data()
        pdf_files: list[File] = [
            f for f in files if (getattr(f, "name", "") or "").lower().endswith(".pdf")
        ]

        # Pre-fetch embedding model for the graph to avoid repeated queries
        embedding_model = await get_graph_embedding_model(db_session, source.graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )

        synced = 0
        failed = 0
        skipped = 0

        for f in pdf_files:
            filename = (getattr(f, "name", None) or "").strip()
            if not filename:
                skipped += 1
                continue

            try:
                config = await get_content_config(
                    db_session, source.graph_id, filename, source_type=source.type
                )
                if not config:
                    skipped += 1
                    continue

                file_bytes = await _download_file_bytes(f)
                content = load_content_from_bytes(file_bytes, config)
                total_pages = content["metadata"].get("total_pages")
                document = await self.create_document_for_source(
                    db_session,
                    source=source,
                    filename=filename,
                    total_pages=total_pages,
                    default_document_type="pdf",
                    content_profile=config.name if config else None,
                )
                await self.process_document(
                    db_session,
                    document,
                    extracted_text=content["text"],
                    config=config,
                    embedding_model=embedding_model,
                )
                synced += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                await self._mark_document_error(db_session, source, filename, e)

        await self._finalize_source(db_session, source, synced=synced, failed=failed)

        summary: dict[str, Any] = {
            "source_id": str(source.id),
            "site_url": site_url,
            "synced": synced,
            "failed": failed,
            "skipped": skipped,
            "total_found": len(pdf_files),
            "status": source.status,
            "last_sync_at": source.last_sync_at,
        }
        logger.info(
            "Completed SharePoint sync for source %s: %s",
            str(source.id),
            summary,
        )
        return summary

    @staticmethod
    def _resolve_location(cfg: dict[str, Any]) -> tuple[str, str | None, bool]:
        library = cfg.get("library")
        folder = cfg.get("folder")
        folder_path = cfg.get("folder_path")
        recursive = bool(cfg.get("recursive", False))

        if not library and folder_path:
            parts = [p for p in str(folder_path).split("/") if p]
            if parts:
                library = parts[0]
                folder = "/".join(parts[1:]) if len(parts) > 1 else None

        if not library:
            library = SharePointRootFolder.DOCUMENTS.value

        return library, folder, recursive

    async def _mark_document_error(
        self,
        db_session: AsyncSession,
        source: KnowledgeGraphSource,
        filename: str,
        error: Exception,
    ) -> None:
        try:
            docs_table = docs_table_name(source.graph_id)
            result = await db_session.execute(
                text(
                    f"""
                    SELECT id::text FROM {docs_table}
                    WHERE source_id = :sid AND name = :name
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"sid": str(source.id), "name": filename},
            )
            doc_id = result.scalar_one_or_none()
            if doc_id:
                await db_session.execute(
                    text(
                        f"""
                        UPDATE {docs_table}
                        SET status = 'error',
                            status_message = :msg,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """
                    ),
                    {"id": doc_id, "msg": str(error)},
                )
                await db_session.commit()
        except Exception:
            logger.warning("Failed to update document error status for '%s'", filename)
        logger.error("Failed to sync file '%s' from SharePoint: %s", filename, error)

    async def _finalize_source(
        self,
        db_session: AsyncSession,
        source: KnowledgeGraphSource,
        *,
        synced: int,
        failed: int,
    ) -> None:
        # Determine final status based on sync results
        if synced > 0 and failed == 0:
            source.status = "completed"
        elif synced > 0 and failed > 0:
            source.status = "partial"
        elif synced == 0 and failed > 0:
            source.status = "failed"
        else:
            source.status = "completed"

        source.last_sync_at = datetime.now(timezone.utc).isoformat()
        try:
            docs_table = docs_table_name(source.graph_id)
            count_result = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {docs_table} WHERE source_id = :sid"),
                {"sid": str(source.id)},
            )
            source.documents_count = int(count_result.scalar_one() or 0)
        except Exception:
            logger.warning(
                "Failed to recalculate documents_count for source %s", str(source.id)
            )

        await db_session.commit()
