from __future__ import annotations

import logging
from pathlib import PurePath
from typing import Any, Protocol, override
from uuid import UUID

from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_415_UNSUPPORTED_MEDIA_TYPE
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from core.db.session import async_session_maker

from ...content_config_services import get_content_config
from ...content_load_services import load_content_from_bytes
from ...models import SourceType, SyncCounters
from ..abstract_source import AbstractDataSource

logger = logging.getLogger(__name__)


class _IngestItemLike(Protocol):
    kind: str
    filename: str
    text: str | None
    file_bytes: bytes | None


class ApiIngestDataSource(AbstractDataSource):
    """Data source for external system ingestion via Runtime API.

    This source is intended for "push" ingestion (API calls) from external systems
    and does not support scheduled syncing.
    """

    def __init__(
        self,
        source: KnowledgeGraphSource | None = None,
        *,
        source_name: str | None = None,
    ) -> None:
        super().__init__(source=source)

        # When constructing without an ORM source instance, configure defaults.
        if source is None:
            self.name = (source_name or "API Ingest").strip() or "API Ingest"
            self.type = SourceType.API_INGEST

    @override
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        raise NotImplementedError("ApiIngestDataSource does not support syncing.")

    @override
    async def get_or_create_source(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        status: str = "not_synced",
    ) -> KnowledgeGraphSource:
        """Get or create a source by (graph_id, type, name).

        Unlike the base implementation (which is unique per type), api ingestion
        needs to support multiple sources of the same type differentiated by name.
        """
        result = await db_session.execute(
            select(KnowledgeGraphSource)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == self.type)
            .where(KnowledgeGraphSource.name == self.name)
        )
        source_entity = result.scalar_one_or_none()

        if not source_entity:
            source_entity = KnowledgeGraphSource(
                name=self.name,
                type=self.type,
                graph_id=graph_id,
                config={},
                status=status,
                documents_count=0,
            )
            db_session.add(source_entity)
            await db_session.commit()
            await db_session.refresh(source_entity)

        return source_entity

    async def ingest_text(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        filename: str,
        text: str,
        file_metadata: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Ingest plain text into a Knowledge Graph as a document."""
        if not isinstance(text, str) or not text.strip():
            raise ClientException("Text content is empty.")

        embedding_model = await self._require_embedding_model(
            db_session, graph_id=graph_id
        )

        resolved_filename = (filename or "").strip()
        if not resolved_filename:
            raise ClientException("filename is required for text ingestion.")

        config = await get_content_config(
            db_session,
            graph_id,
            resolved_filename,
            source_type=str(self.type),
        )
        if not config:
            raise ClientException(
                f"Knowledge Graph does not support content type '{resolved_filename}'.",
                status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        if not self.source:
            self.source = await self.get_or_create_source(
                db_session, graph_id, status="syncing"
            )

        # Mark syncing (best-effort)
        self.source.status = "syncing"
        await db_session.commit()

        document = await self.create_document_for_source(
            db_session,
            filename=resolved_filename,
            total_pages=None,
            file_metadata=file_metadata,
            source_metadata=source_metadata,
            default_document_type="txt",
            content_profile=config.name if config else None,
        )

        doc_name = str(document.get("name") or resolved_filename or "").strip()
        await self.process_document(
            db_session,
            document,
            extracted_text=text,
            config=config,
            document_title=PurePath(doc_name).stem if doc_name else doc_name,
            embedding_model=embedding_model,
        )

    async def ingest_file(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        filename: str,
        file_bytes: bytes,
        source_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Ingest a file (bytes) into a Knowledge Graph as a document."""
        if not isinstance(file_bytes, (bytes, bytearray)) or len(file_bytes) == 0:
            raise ClientException("File is empty.")

        embedding_model = await self._require_embedding_model(
            db_session, graph_id=graph_id
        )

        resolved_filename = (filename or "").strip()
        if not resolved_filename:
            raise ClientException("filename is required for file ingestion.")

        config = await get_content_config(
            db_session,
            graph_id,
            resolved_filename,
            source_type=str(self.type),
        )
        if not config:
            raise ClientException(
                f"Knowledge Graph does not support file type '{resolved_filename}'.",
                status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        if not self.source:
            self.source = await self.get_or_create_source(
                db_session, graph_id, status="syncing"
            )

        # Mark syncing (best-effort)
        self.source.status = "syncing"
        await db_session.commit()

        content = load_content_from_bytes(bytes(file_bytes), config)
        total_pages = (
            content.get("metadata", {}).get("total_pages")
            if isinstance(content, dict)
            else None
        )

        document = await self.create_document_for_source(
            db_session,
            filename=resolved_filename,
            total_pages=total_pages if isinstance(total_pages, int) else None,
            file_metadata=content.get("metadata")
            if isinstance(content, dict)
            else None,
            source_metadata=source_metadata,
            default_document_type="txt",
            content_profile=config.name if config else None,
        )

        doc_name = str(document.get("name") or resolved_filename or "").strip()
        await self.process_document(
            db_session,
            document,
            extracted_text=content["text"],
            config=config,
            document_title=PurePath(doc_name).stem if doc_name else doc_name,
            embedding_model=embedding_model,
        )


async def run_background_ingest(
    *,
    ingestion_id: str,
    graph_id: UUID,
    source_id: UUID,
    items: list[_IngestItemLike],
) -> None:
    """Background ingestion runner.

    Uses a fresh DB session to avoid leaking request-scoped sessions into long jobs.
    """
    if not items:
        return

    try:
        async with async_session_maker() as session:
            source = await session.get(KnowledgeGraphSource, source_id)
            if not source or source.graph_id != graph_id:
                logger.error(
                    "Knowledge graph ingest failed: source not found or graph mismatch",
                    extra={
                        "ingestion_id": ingestion_id,
                        "graph_id": str(graph_id),
                        "source_id": str(source_id),
                    },
                )
                return

            data_source = ApiIngestDataSource(source)

            # Mark syncing best-effort
            try:
                source.status = "syncing"
                await session.commit()
            except Exception:
                pass

            counters = SyncCounters()
            counters.total_found = len(items)

            try:
                for item in items:
                    try:
                        if item.kind == "text":
                            await data_source.ingest_text(
                                session,
                                graph_id,
                                filename=item.filename,
                                text=item.text or "",
                            )
                        elif item.kind == "file":
                            await data_source.ingest_file(
                                session,
                                graph_id,
                                filename=item.filename,
                                file_bytes=item.file_bytes or b"",
                            )
                        else:
                            raise ValueError(f"Unknown ingest kind: {item.kind!r}")

                        counters.synced += 1
                    except Exception as exc:  # noqa: BLE001
                        counters.failed += 1
                        logger.exception(
                            "Knowledge graph ingest item failed",
                            extra={
                                "ingestion_id": ingestion_id,
                                "graph_id": str(graph_id),
                                "source_id": str(source_id),
                                "kind": item.kind,
                                "doc_filename": item.filename,
                                "error": str(exc),
                                "error_type": type(exc).__name__,
                            },
                        )
                        try:
                            await session.rollback()
                        except Exception:
                            pass
            finally:
                # Finalize source status and doc counters based on run outcome
                try:
                    await data_source._finalize(session, counters=counters)  # noqa: SLF001
                except Exception:  # noqa: BLE001
                    logger.exception(
                        "Failed to finalize knowledge graph ingest source",
                        extra={
                            "ingestion_id": ingestion_id,
                            "graph_id": str(graph_id),
                            "source_id": str(source_id),
                        },
                    )

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Knowledge graph ingest crashed",
            extra={
                "ingestion_id": ingestion_id,
                "graph_id": str(graph_id),
                "source_id": str(source_id),
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
        )
