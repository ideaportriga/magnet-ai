import logging
import re
import time
from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphSource,
)
from open_ai.utils_new import get_embeddings

from ..content_split_services import split_content
from ..models import ChunkerStrategy, ContentConfig, SourceType
from ..store_services import (
    chunks_table_name,
    docs_table_name,
    ensure_graph_tables_exist,
    insert_chunks_bulk,
    upsert_document_summary,
)

logger = logging.getLogger(__name__)


class AbstractDataSource(ABC):
    """Abstract base class for managing knowledge graph data sources."""

    def __init__(self, name: str, type: SourceType):
        self.name = name
        self.type = type

    @abstractmethod
    async def sync_source(
        self, db_session: AsyncSession, source: KnowledgeGraphSource
    ) -> dict[str, Any]: ...

    async def _refresh_documents_count(
        self, db_session: AsyncSession, source: KnowledgeGraphSource
    ) -> None:
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
        self,
        *,
        chunks: list[dict[str, Any]],
        embedding_model: str | None,
    ) -> None:
        """Populate embedding vectors for each chunk using the given embedding model.

        This mutates the provided chunks list in-place by adding an 'embedding' key.
        """
        if not chunks or not embedding_model:
            return

        for chunk in chunks:
            # Skip if embedding already present and non-empty
            existing_embedding = chunk.get("embedding")
            if existing_embedding:
                continue

            text = chunk.get("text") or ""
            if not isinstance(text, str) or not text.strip():
                continue

            try:
                vector = await get_embeddings(
                    text=text, model_system_name=embedding_model
                )
                chunk["embedding"] = vector
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to create embedding for chunk with model %s: %s",
                    embedding_model,
                    exc,
                )

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
        source: KnowledgeGraphSource,
        *,
        filename: str,
        total_pages: int | None = None,
        default_document_type: str = "txt",
        content_profile: str | None = None,
    ) -> dict[str, Any]:
        if not filename:
            raise ClientException("Filename is required")

        base_name = PurePath(filename).name
        file_ext = base_name.rsplit(".", 1)[-1].lower() if "." in base_name else ""

        # Lazily ensure per-graph tables exist
        await ensure_graph_tables_exist(db_session, source.graph_id)

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
                },
            )
            await db_session.commit()
        else:
            res = await db_session.execute(
                text(
                    f"""
                    INSERT INTO {docs_table} (
                        name, type, status, total_pages, source_id, content_profile
                    )
                    VALUES (:name, :type, 'pending', :total_pages, :source_id, :content_profile)
                    RETURNING id::text
                    """
                ),
                {
                    "name": base_name,
                    "type": (file_ext or default_document_type),
                    "total_pages": total_pages,
                    "source_id": str(source.id),
                    "content_profile": content_profile,
                },
            )
            document_id = res.scalar_one()
            await db_session.commit()

        await self._refresh_documents_count(db_session, source)

        return {"id": document_id, "graph_id": str(source.graph_id), "name": base_name}

    async def process_document(
        self,
        db_session: AsyncSession,
        document: dict[str, Any],
        *,
        extracted_text: str,
        config: ContentConfig | None,
        embedding_model: str | None = None,
    ) -> dict[str, Any]:
        """Process a document's already-extracted content and create chunks."""
        start_time = time.perf_counter()
        docs_table = docs_table_name(document["graph_id"])
        chunks_table = chunks_table_name(document["graph_id"])
        doc_id = document["id"]

        try:
            await db_session.execute(
                text(
                    f"UPDATE {docs_table} SET status = 'processing', updated_at = CURRENT_TIMESTAMP WHERE id = :id"
                ),
                {"id": doc_id},
            )
            await db_session.commit()

            if not extracted_text or not extracted_text.strip():
                logger.warning(
                    "Empty text for document %s, skipping processing", doc_id
                )
                await db_session.execute(
                    text(
                        f"""
                        UPDATE {docs_table}
                        SET status = 'completed',
                            processing_time = :ptime,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """
                    ),
                    {"id": doc_id, "ptime": float(time.perf_counter() - start_time)},
                )
                await db_session.commit()
                return {"chunks_count": 0}

            chunker_strategy = ChunkerStrategy.RECURSIVE
            if config and getattr(config, "chunker", None):
                try:
                    chunker_strategy = config.chunker.get("strategy", chunker_strategy)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Error parsing chunker config: %s, using defaults", exc
                    )

            result = await split_content(extracted_text, config)

            # Enrich chunks with embeddings using the configured model
            if embedding_model:
                try:
                    await self._add_embeddings_to_chunks(
                        chunks=result.chunks,
                        embedding_model=embedding_model,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to generate embeddings for document %s chunks: %s",
                        doc_id,
                        exc,
                    )

            if result.document_metadata:
                try:
                    title_val = result.document_metadata.title or None
                    summary_val = result.document_metadata.summary or None
                    # Generate embedding for summary if available and model provided
                    summary_embedding_val: list[float] | None = None
                    if summary_val and embedding_model:
                        try:
                            summary_embedding_val = await get_embeddings(
                                text=summary_val, model_system_name=embedding_model
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.warning(
                                "Failed to generate summary embedding for document %s: %s",
                                doc_id,
                                exc,
                            )
                    toc_val = (
                        _convert_markdown_toc_to_json(result.document_metadata.toc)
                        if result.document_metadata.toc
                        else None
                    )
                    await upsert_document_summary(
                        document["graph_id"],
                        doc_id,
                        title=title_val,
                        summary=summary_val,
                        summary_embedding=summary_embedding_val,
                        toc_json=toc_val,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to persist document metadata: %s", exc)

            # Clear existing chunks before adding new ones
            await db_session.execute(
                text(f"DELETE FROM {chunks_table} WHERE document_id = :id"),
                {"id": doc_id},
            )

            chunks_count = await insert_chunks_bulk(
                document["graph_id"], document, result.chunks
            )

            if chunks_count == 0:
                await db_session.execute(
                    text(
                        f"""
                        UPDATE {docs_table}
                        SET status = 'failed',
                            status_message = 'No chunks were generated for this document during processing.',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """
                    ),
                    {"id": doc_id},
                )
                logger.warning(
                    "No chunks generated for document '%s' (id=%s), strategy=%s",
                    document.get("name"),
                    doc_id,
                    chunker_strategy,
                )
            else:
                await db_session.execute(
                    text(
                        f"""
                        UPDATE {docs_table}
                        SET status = 'completed',
                            status_message = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """
                    ),
                    {"id": doc_id},
                )
                logger.info(
                    "Completed processing document '%s' (id=%s): %s chunks, strategy=%s",
                    document.get("name"),
                    doc_id,
                    chunks_count,
                    chunker_strategy,
                )

            await db_session.execute(
                text(
                    f"""
                    UPDATE {docs_table}
                    SET processing_time = :ptime,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {"id": doc_id, "ptime": float(time.perf_counter() - start_time)},
            )
            await db_session.commit()
            return {"chunks_count": chunks_count}

        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing document %s: %s", doc_id, exc)
            await db_session.execute(
                text(
                    f"""
                    UPDATE {docs_table}
                    SET status = 'error',
                        status_message = :msg,
                        processing_time = :ptime,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {
                    "id": doc_id,
                    "msg": str(exc),
                    "ptime": float(time.perf_counter() - start_time),
                },
            )
            await db_session.commit()
            raise ClientException(f"Failed to process document: {exc}")


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
