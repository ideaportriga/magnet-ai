import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphSource,
    docs_table_name,
    resolve_vector_size_for_embedding_model,
)
from core.domain.knowledge_graph.services import (
    KnowledgeGraphChunkService,
    KnowledgeGraphDocumentService,
)
from open_ai.utils_new import get_embeddings

from ..chunk_indexing import get_indexing_config, prepare_embedding_parts
from ..content_config_services import get_graph_embedding_model
from ..content_split_services import split_content
from ..models import ChunkerStrategy, ContentConfig, SourceType, SyncCounters
from ..utils import convert_markdown_toc_to_json

logger = logging.getLogger(__name__)

_UNSET: object = object()


class AbstractDataSource(ABC):
    """Abstract base class for managing knowledge graph data sources."""

    document_service = KnowledgeGraphDocumentService()
    chunk_service = KnowledgeGraphChunkService()

    def __init__(self, source: KnowledgeGraphSource | None = None):
        self.source = source
        if source:
            self.name = source.name
            self.type = SourceType(source.type)

    @abstractmethod
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]: ...

    async def get_or_create_source(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        status: str = "not_synced",
    ) -> KnowledgeGraphSource:
        """Get or create a source uniquely identified by (graph_id, type, name)."""
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

    async def _find_existing_source_id(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> str | None:
        """Find existing source ID by (graph_id, type, name) without creating one."""
        if self.source:
            return str(self.source.id)
        result = await db_session.execute(
            select(KnowledgeGraphSource.id)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == self.type)
            .where(KnowledgeGraphSource.name == self.name)
        )
        sid = result.scalar_one_or_none()
        return str(sid) if sid else None

    async def _add_embeddings_to_chunks(
        self,
        chunks: list[KnowledgeGraphChunk],
        embedding_model: str | None,
        config: ContentConfig | None = None,
    ) -> dict[int, list[tuple[str, list[float]]]]:
        """Create embedding vectors for each chunk's content.

        Vectors are stored exclusively in the per-graph vector table (not on
        the chunk row itself).  The returned dict maps every chunk list-index
        to its ``(text, vector)`` tuples so that the caller can forward them
        to ``insert_vectors_bulk``.

        Returns:
            A mapping of chunk list-index → list of (part_text, part_vector).
        """
        embedding_map: dict[int, list[tuple[str, list[float]]]] = {}

        if not chunks or not embedding_model:
            return embedding_map

        # Resolve indexing configuration from the content profile.
        chunker_options: dict[str, Any] = {}
        if config and isinstance(config.chunker, dict):
            chunker_options = config.chunker.get("options") or {}
        indexing_cfg = get_indexing_config(chunker_options)

        for idx, chunk in enumerate(chunks):
            embedded_content = chunk.embedded_content or ""
            if not isinstance(embedded_content, str) or not embedded_content.strip():
                continue

            parts = prepare_embedding_parts(embedded_content, indexing_cfg)
            if not parts:
                continue

            try:
                indexing_parts: list[tuple[str, list[float]]] = []
                for part_text in parts:
                    part_vector = await get_embeddings(
                        text=part_text, model_system_name=embedding_model
                    )
                    indexing_parts.append((part_text, part_vector))
                embedding_map[idx] = indexing_parts
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to create embedding for chunk with model %s: %s",
                    embedding_model,
                    exc,
                )

        return embedding_map

    async def _require_embedding_model(
        self, db_session: AsyncSession, *, graph_id: UUID | None = None
    ) -> str:
        """Return the configured embedding model for a graph or raise.

        This is a small shared helper used across sources to:
        - validate graph settings before doing any ingestion work
        - avoid repeating the same error message in every source implementation
        """
        resolved_graph_id = graph_id or (self.source.graph_id if self.source else None)
        if not resolved_graph_id:
            raise ClientException("graph_id is required to resolve embedding model.")

        embedding_model = await get_graph_embedding_model(db_session, resolved_graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )
        return embedding_model

    async def _update_document_status(
        self,
        db_session: AsyncSession,
        *,
        docs_table: str,
        doc_id: str,
        status: str,
        status_message: str | None | object = _UNSET,
        processing_time: float | object = _UNSET,
        content_plaintext: str | None | object = _UNSET,
    ) -> None:
        """Update processing status for a single document row.

        We intentionally accept a sentinel for optional fields so callers can:
        - leave `status_message` untouched (sentinel),
        - set it to a string,
        - or explicitly clear it by passing None.
        """
        set_clauses = ["status = :status", "updated_at = CURRENT_TIMESTAMP"]
        params: dict[str, Any] = {"id": doc_id, "status": status}

        if status_message is not _UNSET:
            set_clauses.append("status_message = :msg")
            params["msg"] = status_message

        if processing_time is not _UNSET:
            set_clauses.append("processing_time = :ptime")
            params["ptime"] = float(processing_time)

        if content_plaintext is not _UNSET:
            set_clauses.append("content_plaintext = :content_plaintext")
            params["content_plaintext"] = content_plaintext

        await db_session.execute(
            text(f"UPDATE {docs_table} SET {', '.join(set_clauses)} WHERE id = :id"),
            params,
        )

    def _get_chunker_options(self, config: ContentConfig | None) -> dict[str, Any]:
        if not config or not getattr(config, "chunker", None):
            return {}

        options = config.chunker.get("options")
        return options if isinstance(options, dict) else {}

    def _format_pattern(self, pattern: str, values: dict[str, Any]) -> str:
        if not pattern:
            return ""

        return re.sub(
            r"{(\w+)}",
            lambda match: str(values.get(match.group(1), "") or ""),
            pattern,
        )

    def _apply_pre_chunked_config(
        self,
        *,
        chunks: list[KnowledgeGraphChunk],
        config: ContentConfig | None,
        document: dict[str, Any],
        document_title: str | None,
        source_modified_at: datetime | None,
    ) -> tuple[str | None, list[KnowledgeGraphChunk]]:
        options = self._get_chunker_options(config)
        if not options:
            return document_title, chunks

        source_name = self.source.name if self.source else ""
        source_date = (
            source_modified_at.date().isoformat()
            if isinstance(source_modified_at, datetime)
            else ""
        )
        filename = str(document.get("name") or "").strip()

        document_pattern_values = {
            "filename": filename,
            "title": document_title or "",
            "date": source_date,
            "source": source_name,
        }
        document_title_pattern = str(
            options.get("document_title_pattern") or ""
        ).strip()
        if document_title_pattern:
            formatted_title = self._format_pattern(
                document_title_pattern, document_pattern_values
            ).strip()
            if formatted_title:
                document_title = formatted_title
                document_pattern_values["title"] = formatted_title

        chunk_title_pattern = str(options.get("chunk_title_pattern") or "").strip()
        normalized_chunks: list[KnowledgeGraphChunk] = []
        for index, chunk in enumerate(chunks, start=1):
            content = chunk.content or chunk.embedded_content or ""
            embedded_content = chunk.embedded_content or content
            chunk.content = content
            chunk.embedded_content = embedded_content

            if (
                not isinstance(chunk.embedded_content, str)
                or not chunk.embedded_content.strip()
            ):
                continue

            if not isinstance(chunk.content, str) or not chunk.content.strip():
                chunk.content = chunk.embedded_content

            if chunk_title_pattern:
                formatted_chunk_title = self._format_pattern(
                    chunk_title_pattern,
                    {
                        **document_pattern_values,
                        "index": index,
                        "page": chunk.page or "",
                    },
                ).strip()
                if formatted_chunk_title:
                    chunk.title = formatted_chunk_title

            normalized_chunks.append(chunk)

        return document_title, normalized_chunks

    @staticmethod
    def _sanitize_extracted_text(value: str | None) -> str:
        normalized = (value or "").strip()
        # Strip non-UTF-8 characters and NULL bytes (PostgreSQL rejects 0x00 in text)
        return (
            normalized.encode("utf-8", errors="ignore")
            .decode("utf-8", errors="ignore")
            .replace("\x00", "")
        )

    async def process_document(
        self,
        db_session: AsyncSession,
        document: dict[str, Any],
        *,
        extracted_text: str | None = None,
        raw_text: str | None = None,
        config: ContentConfig | None = None,
        chunks: list[KnowledgeGraphChunk] | None = None,
        document_title: str | None = None,
        document_summary: str | None = None,
        external_link: str | None = None,
        source_modified_at: datetime | None = None,
        toc_json: dict | list | None = None,
        embedding_model: str | None = None,
        delete_existing_chunks: bool = True,
    ) -> dict[str, Any]:
        """Process a document and create chunks.

        This method supports two ingestion modes:

        - **Split mode** (default): pass `extracted_text` (and optional `config`) and we will
          chunk it using the configured chunker.
        - **Pre-chunked mode**: pass `chunks` when the upstream system already provides
          semantically meaningful chunk boundaries (e.g. Fluid Topics topic content).
        """
        start_time = time.perf_counter()
        docs_table = docs_table_name(document["graph_id"])
        doc_id = document["id"]
        extracted_text = self._sanitize_extracted_text(extracted_text)
        raw_text = (
            self._sanitize_extracted_text(raw_text) if raw_text is not None else None
        )

        try:
            # Mark processing early so the UI / callers can observe progress even if
            # chunking + embedding generation takes a long time.
            await self._update_document_status(
                db_session,
                docs_table=docs_table,
                doc_id=doc_id,
                status="processing",
                content_plaintext=extracted_text,
            )
            await db_session.commit()

            # ----------------------------
            # Build the chunks to ingest
            # ----------------------------
            #
            # We either:
            # - take chunks as-is (pre-chunked mode), or
            # - split delimiter-preserving extracted text (split mode).
            #
            # The rest of the pipeline (embeddings, metadata, DB writes) is shared.
            # We keep a string label for logs. For split mode, it's the configured chunker
            # strategy; for pre-chunked mode it's a special marker.
            chunker_strategy: str = "pre_chunked"
            chunks_to_insert: list[KnowledgeGraphChunk] = []
            is_pre_chunked = chunks is not None

            if is_pre_chunked:
                # Sources can send empty/placeholder chunks; we filter them out to avoid:
                # - embedding calls with empty text
                # - storing meaningless chunks in the DB
                for ch in chunks or []:
                    content = ch.content
                    embedded_content = ch.embedded_content
                    if isinstance(embedded_content, str) and embedded_content.strip():
                        ch.content = content or embedded_content
                        chunks_to_insert.append(ch)

                document_title, chunks_to_insert = self._apply_pre_chunked_config(
                    chunks=chunks_to_insert,
                    config=config,
                    document=document,
                    document_title=document_title,
                    source_modified_at=source_modified_at,
                )

                if len(chunks_to_insert) == 0:
                    logger.warning(
                        "No valid chunks for document %s, skipping processing", doc_id
                    )
                    await self._update_document_status(
                        db_session,
                        docs_table=docs_table,
                        doc_id=doc_id,
                        status="completed",
                        status_message=None,
                        processing_time=float(time.perf_counter() - start_time),
                    )
                    await db_session.commit()
                    return {"chunks_count": 0}

            else:
                # Skip safely when the delimiter-free text is empty, even if the
                # delimiter-preserving variant still contains synthetic markers.
                skip_check_text = raw_text if raw_text is not None else extracted_text
                if not skip_check_text:
                    logger.warning(
                        "Empty text for document %s, skipping processing", doc_id
                    )
                    # Still persist document-level metadata (title, link, etc.)
                    # so the document is not left without a title.
                    try:
                        await self.document_service.update_document(
                            db_session,
                            graph_id=document["graph_id"],
                            document_id=doc_id,
                            fields={
                                "title": document_title,
                                "external_link": external_link,
                            },
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Failed to persist document metadata: %s", exc)
                    await self._update_document_status(
                        db_session,
                        docs_table=docs_table,
                        doc_id=doc_id,
                        status="completed",
                        status_message=None,
                        processing_time=float(time.perf_counter() - start_time),
                    )
                    await db_session.commit()
                    return {"chunks_count": 0}

                # Strategy is only used for logging; split_content applies config internally.
                chunker_strategy = str(ChunkerStrategy.RECURSIVE)
                if config and getattr(config, "chunker", None):
                    try:
                        chunker_strategy = str(
                            config.chunker.get("strategy", chunker_strategy)
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Error parsing chunker config: %s, using defaults", exc
                        )

                # `split_content()` returns:
                # - a list of chunk dicts (stored in chunks table)
                # - optional document metadata (stored in documents table)
                result = await split_content(
                    extracted_text,
                    config,
                    document_title=document_title,
                    source_url=external_link,
                )
                chunks_to_insert = result.chunks

                if len(chunks_to_insert) == 0:
                    status_msg = (
                        "No chunks were generated for this document during processing."
                    )
                    await self._update_document_status(
                        db_session,
                        docs_table=docs_table,
                        doc_id=doc_id,
                        status="failed",
                        status_message=status_msg,
                        processing_time=float(time.perf_counter() - start_time),
                    )
                    await db_session.commit()
                    logger.warning(
                        "No chunks generated for document '%s' (id=%s), strategy=%s",
                        document.get("name"),
                        doc_id,
                        chunker_strategy,
                    )
                    return {"chunks_count": 0}

                # Prefer explicit metadata provided by the caller. Otherwise take the
                # chunker-produced document metadata (title/summary/toc).
                if result.document_metadata:
                    if document_title is None:
                        document_title = result.document_metadata.title or None
                    if document_summary is None:
                        document_summary = result.document_metadata.summary or None
                    if toc_json is None and result.document_metadata.toc:
                        toc_json = convert_markdown_toc_to_json(
                            result.document_metadata.toc
                        )

            # Defensive guard: empty-chunk cases should already return above, but
            # avoid any downstream work if a future change misses that early exit.
            if not chunks_to_insert:
                return {"chunks_count": 0}

            chunks_count = len(chunks_to_insert)

            # Enrich chunks with embeddings
            multi_part_map = await self._add_embeddings_to_chunks(
                chunks_to_insert, embedding_model, config=config
            )

            # updated document title, summary and toc
            try:
                summary_embedding: list[float] | None = None
                if document_summary and embedding_model:
                    try:
                        summary_embedding = await get_embeddings(
                            text=document_summary, model_system_name=embedding_model
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Failed to generate summary embedding for document %s: %s",
                            doc_id,
                            exc,
                        )

                await self.document_service.update_document(
                    db_session,
                    graph_id=document["graph_id"],
                    document_id=doc_id,
                    fields={
                        "title": document_title,
                        "external_link": external_link,
                        "summary": document_summary,
                        "summary_embedding": summary_embedding,
                        "toc": toc_json,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to persist document metadata: %s", exc)

            # Clear existing chunks before inserting new ones. This keeps re-sync idempotent
            # (a map/document won't accumulate duplicate chunks across runs).
            if delete_existing_chunks:
                await self.chunk_service.delete_chunks(
                    db_session,
                    graph_id=UUID(document["graph_id"]),
                    document_id=UUID(document["id"]),
                )

            # Resolve vector size for the per-graph vector table.
            vec_size: int | None = None
            if embedding_model:
                try:
                    vec_size = await resolve_vector_size_for_embedding_model(
                        embedding_model
                    )
                except Exception:  # noqa: BLE001
                    pass

            await self.chunk_service.insert_chunks_bulk(
                db_session,
                graph_id=document["graph_id"],
                document=document,
                chunks=chunks_to_insert,
                vector_size=vec_size,
                embedding_map=multi_part_map,
            )

            await self._update_document_status(
                db_session,
                docs_table=docs_table,
                doc_id=doc_id,
                status="completed",
                status_message=None,  # clear any previous error message
                processing_time=float(time.perf_counter() - start_time),
            )
            logger.info(
                "Completed processing document '%s' (id=%s): %s chunks, strategy=%s",
                document.get("name"),
                doc_id,
                chunks_count,
                chunker_strategy,
            )

            await db_session.commit()
            return {"chunks_count": chunks_count}

        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing document %s: %s", doc_id, exc)
            await self._update_document_status(
                db_session,
                docs_table=docs_table,
                doc_id=doc_id,
                status="error",
                status_message=str(exc),
                processing_time=float(time.perf_counter() - start_time),
            )
            await db_session.commit()
            raise ClientException(f"Failed to process document: {exc}")

    async def _mark_document_error(
        self, db_session: AsyncSession, filename: str, error: Exception
    ) -> None:
        """Mark a Knowledge Graph document (by source + name) as errored (best-effort)."""

        # Best-effort: sync should continue even if we fail to update status.
        try:
            docs_table = docs_table_name(self.source.graph_id)
            # Find document by name and source
            result = await db_session.execute(
                text(
                    f"""
                    SELECT id::text FROM {docs_table}
                    WHERE source_id = :sid AND name = :name
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"sid": str(self.source.id), "name": filename},
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
            logger.error("Failed to update document error status for '%s'", filename)
            return

    async def _finalize(
        self, db_session: AsyncSession, *, counters: SyncCounters
    ) -> None:
        """Finalize source status, timestamps, and document count after a sync run."""

        # Determine final status based on sync results.
        #
        # This status is used by the UI to show whether a source is healthy:
        # - completed: everything we attempted succeeded (or nothing to sync)
        # - partial: some succeeded, some failed
        # - failed: nothing succeeded and at least one failed
        if counters.synced > 0 and counters.failed == 0:
            self.source.status = "completed"
        elif counters.synced > 0 and counters.failed > 0:
            self.source.status = "partial"
        elif counters.synced == 0 and counters.failed > 0:
            self.source.status = "failed"
        elif counters.synced == 0 and counters.failed == 0:
            # Nothing found or everything skipped
            self.source.status = "completed"

        self.source.last_sync_at = datetime.now(timezone.utc).isoformat()
        try:
            docs_table = docs_table_name(self.source.graph_id)
            count_result = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {docs_table} WHERE source_id = :sid"),
                {"sid": str(self.source.id)},
            )
            self.source.documents_count = int(count_result.scalar_one() or 0)
        except Exception:
            logger.warning(
                "Failed to recalculate documents_count for source %s",
                str(self.source.id),
            )

        await db_session.commit()
