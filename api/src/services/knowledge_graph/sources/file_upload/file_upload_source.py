from typing import Any, override
from uuid import UUID

from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_415_UNSUPPORTED_MEDIA_TYPE
from sqlalchemy.ext.asyncio import AsyncSession

from ...content_config_services import get_content_config
from ...models import SourceType, SyncCounters, SyncPipelineConfig
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

        embedding_model = await self._require_embedding_model(
            db_session, graph_id=graph_id
        )

        existing_source_id = await self._find_existing_source_id(db_session, graph_id)

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

        self.source = await self.get_or_create_source(
            db_session, graph_id, status="syncing"
        )

        self.source.status = "syncing"
        await db_session.commit()

        counters = SyncCounters()
        counters.total_found = 1

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
            counters.synced = 1
        except Exception:
            counters.failed = 1
            raise
        finally:
            await self._finalize(db_session, counters=counters)
