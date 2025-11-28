import logging
import re
import time
from abc import ABC, abstractmethod
from pathlib import PurePath
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraphChunk,
    KnowledgeGraphDocument,
    KnowledgeGraphSource,
)

from ..content_split_services import split_content
from ..models import ChunkerStrategy, ContentConfig, SourceType

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
            count_result = await db_session.execute(
                select(func.count(KnowledgeGraphDocument.id)).where(
                    KnowledgeGraphDocument.source_id == source.id
                )
            )
            source.documents_count = int(count_result.scalar_one() or 0)
            await db_session.commit()
        except Exception:
            logger.warning(
                "Failed to update documents_count for source %s", str(source.id)
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
    ) -> KnowledgeGraphDocument:
        if not filename:
            raise ClientException("Filename is required")

        base_name = PurePath(filename).name
        file_ext = base_name.rsplit(".", 1)[-1].lower() if "." in base_name else ""

        # Check for existing document
        result = await db_session.execute(
            select(KnowledgeGraphDocument)
            .where(KnowledgeGraphDocument.source_id == source.id)
            .where(KnowledgeGraphDocument.name == base_name)
        )
        document = result.scalar_one_or_none()

        if document:
            document.status = "pending"
            document.status_message = None
            document.total_pages = total_pages
            document.type = file_ext or default_document_type
            document.content_profile = content_profile
            document.processing_time = None
        else:
            document = KnowledgeGraphDocument(
                name=base_name,
                type=(file_ext or default_document_type),
                status="pending",
                total_pages=total_pages,
                source_id=source.id,
                graph_id=source.graph_id,
                content_profile=content_profile,
            )
            db_session.add(document)

        await db_session.commit()
        await db_session.refresh(document)

        await self._refresh_documents_count(db_session, source)

        return document

    async def process_document(
        self,
        db_session: AsyncSession,
        document: KnowledgeGraphDocument,
        *,
        extracted_text: str,
        config: ContentConfig | None,
    ) -> dict[str, Any]:
        """Process a document's already-extracted content and create chunks."""
        start_time = time.perf_counter()
        try:
            document.status = "processing"
            await db_session.commit()

            if not extracted_text or not extracted_text.strip():
                logger.warning(
                    "Empty text for document %s, skipping processing", document.id
                )
                document.status = "completed"
                document.processing_time = time.perf_counter() - start_time
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

            if result.document_metadata:
                try:
                    if result.document_metadata.title:
                        document.title = result.document_metadata.title
                    if result.document_metadata.summary:
                        document.summary = result.document_metadata.summary
                    if result.document_metadata.toc:
                        document.toc = _convert_markdown_toc_to_json(
                            result.document_metadata.toc
                        )
                    await db_session.commit()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to persist document metadata: %s", exc)

            # Clear existing chunks before adding new ones
            await db_session.execute(
                delete(KnowledgeGraphChunk).where(
                    KnowledgeGraphChunk.document_id == document.id
                )
            )

            chunks_count = await _store_chunks_in_db(
                db_session, document, result.chunks
            )

            if chunks_count == 0:
                document.status = "failed"
                document.status_message = (
                    "No chunks were generated for this document during processing."
                )
                logger.warning(
                    "No chunks generated for document '%s' (id=%s), strategy=%s",
                    document.name,
                    document.id,
                    chunker_strategy,
                )
            else:
                document.status = "completed"
                document.status_message = None
                logger.info(
                    "Completed processing document '%s' (id=%s): %s chunks, strategy=%s",
                    document.name,
                    document.id,
                    chunks_count,
                    chunker_strategy,
                )

            document.processing_time = time.perf_counter() - start_time
            await db_session.commit()
            return {"chunks_count": chunks_count}

        except Exception as exc:  # noqa: BLE001
            logger.error("Error processing document %s: %s", document.id, exc)
            document.status = "error"
            document.status_message = str(exc)
            document.processing_time = time.perf_counter() - start_time
            await db_session.commit()
            raise ClientException(f"Failed to process document: {exc}")


async def _store_chunks_in_db(
    db_session: AsyncSession,
    document: KnowledgeGraphDocument,
    chunks: list[dict[str, Any]],
) -> int:
    if not chunks:
        return 0

    chunk_records = []
    for idx, chunk_data in enumerate(chunks):
        chunk_record = KnowledgeGraphChunk(
            name=f"{document.name}_chunk_{idx + 1}",
            index=idx,
            title=chunk_data.get("title", ""),
            toc_reference=chunk_data.get("toc_reference", ""),
            page=chunk_data.get("page", -1) if chunk_data.get("page", -1) > 0 else None,
            text=chunk_data.get("text", ""),
            embedding=chunk_data.get("embedding", []),
            chunk_type=chunk_data.get("type", "TEXT"),
            document_id=document.id,
        )
        chunk_records.append(chunk_record)

    db_session.add_all(chunk_records)
    await db_session.commit()

    logger.info("Stored %s chunks for document %s", len(chunk_records), document.id)
    return len(chunk_records)


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
