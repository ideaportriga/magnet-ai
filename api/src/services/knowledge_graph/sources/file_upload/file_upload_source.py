from datetime import datetime, timezone
from typing import Any, override
from uuid import UUID

from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_415_UNSUPPORTED_MEDIA_TYPE
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource, docs_table_name

from ...content_config_services import get_content_config
from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from .file_upload_sync import FileUploadSyncPipeline


class FileUploadDataSource(AbstractDataSource):
    """Data source for manual uploads of local files.

    This is a specialized source that does not support `sync_source()`.
    Instead, callers should use `upload_and_process_file()` which accepts raw
    file bytes and handles content loading internally.
    """

    def __init__(self) -> None:
        super().__init__(source=None)
        self.name = "Uploaded Files"
        self.type = SourceType.UPLOAD

    # Pipeline tuning (single-file upload; keep tight bounds)
    LISTING_QUEUE_MAX = 0
    CONTENT_FETCH_QUEUE_MAX = 1
    DOCUMENT_PROCESSING_QUEUE_MAX = 1

    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 1
    DOCUMENT_PROCESSING_WORKERS = 1

    @override
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        raise NotImplementedError("FileUploadDataSource does not support syncing.")

    async def upload_and_process_file(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        filename: str,
        file_bytes: bytes,
    ) -> None:
        """Upload a file and ingest it into the Knowledge Graph.

        This method is used by the upload endpoint and mirrors the ingestion
        steps used by other sources:
        - resolve content config
        - load/extract text from bytes
        - create/update document row
        - process document (chunking + embeddings + persistence)
        - finalize source status based on document outcomes
        """

        # Validate embedding model before creating any source or documents
        embedding_model = await self._require_embedding_model(
            db_session, graph_id=graph_id
        )

        existing_source_id: str | None = None
        result = await db_session.execute(
            select(KnowledgeGraphSource.id)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == self.type)
        )
        sid = result.scalar_one_or_none()
        existing_source_id = str(sid) if sid else None

        config = await get_content_config(
            db_session,
            graph_id,
            filename,
            source_id=existing_source_id,
            source_type=str(self.type),
        )
        if not config:
            raise ClientException(
                f"Knowledge Graph does not support file type '{filename}'.",
                status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        source = await self.get_or_create_source(db_session, graph_id, status="syncing")
        self.source = source

        source.status = "syncing"
        await db_session.commit()

        try:
            pipeline = FileUploadSyncPipeline(
                source=self,
                pipeline_config=SyncPipelineConfig(
                    name="file_upload",
                    listing_queue_max=int(self.LISTING_QUEUE_MAX),
                    content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                    document_processing_queue_max=int(
                        self.DOCUMENT_PROCESSING_QUEUE_MAX
                    ),
                    listing_workers=max(1, int(self.LISTING_WORKERS)),
                    content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                    document_processing_workers=max(
                        1, int(self.DOCUMENT_PROCESSING_WORKERS)
                    ),
                    semaphores={},
                ),
                embedding_model=embedding_model,
                filename=filename,
                file_bytes=file_bytes,
                content_config=config,
            )

            await pipeline.run()
        finally:
            # Finalize source status based on document outcomes across the source
            try:
                docs_table = docs_table_name(graph_id)
                completed_count_result = await db_session.execute(
                    text(
                        f"SELECT COUNT(*) FROM {docs_table} WHERE source_id = :sid AND status = 'completed'"
                    ),
                    {"sid": str(source.id)},
                )
                failed_count_result = await db_session.execute(
                    text(
                        f"SELECT COUNT(*) FROM {docs_table} WHERE source_id = :sid AND status IN ('failed','error')"
                    ),
                    {"sid": str(source.id)},
                )
                completed_count = int(completed_count_result.scalar_one() or 0)
                failed_count = int(failed_count_result.scalar_one() or 0)

                if completed_count > 0 and failed_count == 0:
                    source.status = "completed"
                elif completed_count > 0 and failed_count > 0:
                    source.status = "partial"
                elif completed_count == 0 and failed_count > 0:
                    source.status = "failed"
                else:
                    # No documents found or indeterminate -> treat as completed
                    source.status = "completed"

                source.last_sync_at = datetime.now(timezone.utc).isoformat()
                await db_session.commit()
            except Exception:
                # In case of any unexpected error while finalizing, mark as failed
                source.status = "failed"
                source.last_sync_at = datetime.now(timezone.utc).isoformat()
                await db_session.commit()
