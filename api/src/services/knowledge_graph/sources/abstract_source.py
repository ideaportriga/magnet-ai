import json
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphSource,
    docs_table_name,
)
from core.domain.knowledge_graph.service import (
    KnowledgeGraphChunkService,
    KnowledgeGraphDocumentService,
)
from open_ai.utils_new import get_embeddings

from ..content_config_services import get_graph_embedding_model
from ..content_split_services import split_content
from ..models import ChunkerStrategy, ContentConfig, SourceType, SyncCounters

logger = logging.getLogger(__name__)

_UNSET: object = object()


class AbstractDataSource(ABC):
    """Abstract base class for managing knowledge graph data sources."""

    def __init__(self, source: KnowledgeGraphSource | None = None):
        self.source = source
        if source:
            self.name = source.name
            self.type = SourceType(source.type)

    @abstractmethod
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]: ...

    async def _refresh_documents_count(self, db_session: AsyncSession) -> None:
        source = self.source
        if not source:
            return

        try:
            table = docs_table_name(source.graph_id)
            res = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE source_id = :sid"),
                {"sid": str(source.id)},
            )
            source.documents_count = int(res.scalar_one() or 0)
            await db_session.commit()
        except Exception:
            logger.warning(
                "Failed to update documents_count for source %s", str(source.id)
            )

    async def _add_embeddings_to_chunks(
        self, chunks: list[KnowledgeGraphChunk], embedding_model: str | None
    ) -> None:
        """Populate embedding vectors for each chunk using the given embedding model.

        This mutates the provided chunks list in-place by setting `content_embedding`.
        """
        if not chunks or not embedding_model:
            return

        for chunk in chunks:
            # Skip if embedding already present and non-empty
            existing_embedding = chunk.content_embedding
            if existing_embedding:
                continue

            embedded_content = chunk.embedded_content or ""
            if not isinstance(embedded_content, str) or not embedded_content.strip():
                continue

            try:
                vector = await get_embeddings(
                    text=embedded_content, model_system_name=embedding_model
                )
                chunk.content_embedding = vector
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to create embedding for chunk with model %s: %s",
                    embedding_model,
                    exc,
                )

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

    async def get_or_create_source(
        self, db_session: AsyncSession, graph_id: UUID, *, status: str = "not_synced"
    ) -> KnowledgeGraphSource:
        result = await db_session.execute(
            select(KnowledgeGraphSource)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == self.type)
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

    async def create_document_for_source(
        self,
        db_session: AsyncSession,
        *,
        filename: str,
        total_pages: int | None = None,
        file_metadata: dict[str, Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        default_document_type: str = "txt",
        content_profile: str | None = None,
    ) -> dict[str, Any]:
        source = self.source
        if not source:
            raise ClientException("Source is required to create a document")

        if not filename:
            raise ClientException("Filename is required")

        base_name = PurePath(filename).name
        file_ext = base_name.rsplit(".", 1)[-1].lower() if "." in base_name else ""

        doc_metadata_json: str | None = None
        doc_metadata_payload: dict[str, Any] = {}
        if isinstance(file_metadata, dict) and file_metadata:
            doc_metadata_payload["file"] = file_metadata
        if isinstance(source_metadata, dict) and source_metadata:
            doc_metadata_payload["source"] = source_metadata
        if doc_metadata_payload:
            try:
                doc_metadata_json = json.dumps(
                    doc_metadata_payload, ensure_ascii=False, default=str
                )
            except Exception:  # noqa: BLE001
                # Best-effort: do not fail document creation if metadata cannot be serialized.
                doc_metadata_json = None

        docs_table = docs_table_name(source.graph_id)
        # Check for existing document by source_id + name
        existing = await db_session.execute(
            text(
                f"""
                SELECT id::text
                FROM {docs_table}
                WHERE source_id = :sid AND name = :name
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"sid": str(source.id), "name": base_name},
        )
        document_id = existing.scalar_one_or_none()
        if document_id:
            await db_session.execute(
                text(
                    f"""
                    UPDATE {docs_table}
                    SET status = 'pending',
                    status_message = NULL,
                    total_pages = :total_pages,
                    type = :type,
                    content_profile = :content_profile,
                    metadata = CASE
                        WHEN CAST(:metadata_json AS jsonb) IS NULL THEN metadata
                        ELSE COALESCE(metadata, '{{}}'::jsonb) || CAST(:metadata_json AS jsonb)
                    END,
                    processing_time = NULL,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {
                    "id": document_id,
                    "total_pages": total_pages,
                    "type": (file_ext or default_document_type),
                    "content_profile": content_profile,
                    "metadata_json": doc_metadata_json,
                },
            )
            await db_session.commit()
        else:
            res = await db_session.execute(
                text(
                    f"""
                    INSERT INTO {docs_table} (
                    name, type, status, total_pages, source_id, content_profile, metadata
                    )
                    VALUES (
                        :name,
                        :type,
                        'pending',
                        :total_pages,
                        :source_id,
                        :content_profile,
                        COALESCE(CAST(:metadata_json AS jsonb), '{{}}'::jsonb)
                    )
                    RETURNING id::text
                    """
                ),
                {
                    "name": base_name,
                    "type": (file_ext or default_document_type),
                    "total_pages": total_pages,
                    "source_id": str(source.id),
                    "content_profile": content_profile,
                    "metadata_json": doc_metadata_json,
                },
            )
            document_id = res.scalar_one()
            await db_session.commit()

        await self._refresh_documents_count(db_session)

        return {"id": document_id, "graph_id": str(source.graph_id), "name": base_name}

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

    async def process_document(
        self,
        db_session: AsyncSession,
        document: dict[str, Any],
        *,
        extracted_text: str | None = None,
        config: ContentConfig | None = None,
        chunks: list[KnowledgeGraphChunk] | None = None,
        document_title: str | None = None,
        document_summary: str | None = None,
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
            # - split raw extracted text (split mode).
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
                # Split mode: chunk raw extracted text.
                if not extracted_text or not extracted_text.strip():
                    logger.warning(
                        "Empty text for document %s, skipping processing", doc_id
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
                    extracted_text, config, document_title=document_title
                )
                chunks_to_insert = result.chunks

                # Prefer explicit metadata provided by the caller. Otherwise take the
                # chunker-produced document metadata (title/summary/toc).
                if result.document_metadata:
                    if document_title is None:
                        document_title = result.document_metadata.title or None
                    if document_summary is None:
                        document_summary = result.document_metadata.summary or None
                    if toc_json is None and result.document_metadata.toc:
                        toc_json = _convert_markdown_toc_to_json(
                            result.document_metadata.toc
                        )

            # Enrich chunks with embeddings
            await self._add_embeddings_to_chunks(chunks_to_insert, embedding_model)

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

                await KnowledgeGraphDocumentService().update_document(
                    db_session,
                    graph_id=document["graph_id"],
                    document_id=doc_id,
                    fields={
                        "title": document_title,
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
                await KnowledgeGraphChunkService().delete_chunks(
                    db_session,
                    graph_id=UUID(document["graph_id"]),
                    document_id=UUID(document["id"]),
                )

            chunks_count = await KnowledgeGraphChunkService().insert_chunks_bulk(
                db_session,
                graph_id=document["graph_id"],
                document=document,
                chunks=chunks_to_insert,
            )

            if chunks_count == 0:
                # Split mode reaching 0 means the chunker produced no output; that's a real failure
                # because we had non-empty extracted text.
                status_msg = (
                    "No chunks were generated for this document during processing."
                    if not is_pre_chunked
                    else "No chunks were inserted for this document during processing."
                )
                await self._update_document_status(
                    db_session,
                    docs_table=docs_table,
                    doc_id=doc_id,
                    status="failed",
                    status_message=status_msg,
                    processing_time=float(time.perf_counter() - start_time),
                )
                if is_pre_chunked:
                    logger.warning(
                        "No chunks inserted for pre-chunked document '%s' (id=%s)",
                        document.get("name"),
                        doc_id,
                    )
                else:
                    logger.warning(
                        "No chunks generated for document '%s' (id=%s), strategy=%s",
                        document.get("name"),
                        doc_id,
                        chunker_strategy,
                    )
            else:
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


def _convert_markdown_toc_to_json(markdown: str) -> list[dict[str, Any]]:
    """Convert a markdown TOC-like content into a JSON tree structure.

    Rules:
    - Only ATX headings (# .. ######) are treated as section delimiters.
    - Text lines are associated with the most recent heading at the current depth.
    - Nested headings create children of the nearest ancestor with a lower level.
    - Content before the first heading is ignored.

    Returns a list of root-level nodes, each with: { name, text, children }.
    """
    if not markdown:
        return []

    try:
        root: list[dict[str, Any]] = []
        stack: list[tuple[int, dict[str, Any]]] = []  # (level, node)
        in_fenced_block = False

        heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
        fence_re = re.compile(r"^```+")

        for raw_line in markdown.splitlines():
            line = raw_line.rstrip("\n")

            # Toggle fenced code blocks to avoid parsing headings inside code
            if fence_re.match(line):
                in_fenced_block = not in_fenced_block
            if in_fenced_block:
                # Treat code as regular text if within a section
                if stack:
                    stack[-1][1].setdefault("text_lines", []).append(line)
                continue

            m = heading_re.match(line)
            if m:
                level = len(m.group(1))
                title = (
                    m.group(2).strip().rstrip("#").strip()
                )  # trim trailing #'s if present

                node: dict[str, Any] = {"name": title, "text_lines": [], "children": []}

                # Find parent by popping until the stack top has lower level
                while stack and stack[-1][0] >= level:
                    stack.pop()

                if stack:
                    stack[-1][1]["children"].append(node)
                else:
                    root.append(node)

                stack.append((level, node))
            else:
                # Regular text goes to the current section (last heading)
                if stack:
                    stack[-1][1].setdefault("text_lines", []).append(line)
                else:
                    # Ignore text before the first heading
                    continue

        def _finalize_nodes(nodes: list[dict[str, Any]]):
            for node in nodes:
                lines: list[str] = node.pop("text_lines", [])
                # Preserve intra-paragraph newlines but trim leading/trailing whitespace
                text = "\n".join(lines).strip()
                node["text"] = text
                children = node.get("children", []) or []
                if children:
                    _finalize_nodes(children)

        # Finalize text fields
        _finalize_nodes(root)
        return root
    except Exception as e:
        logger.error(f"Failed to convert markdown TOC to JSON: {e}")
        return []
