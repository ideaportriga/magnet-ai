from datetime import datetime, timezone
from typing import Any, override
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.knowledge_graph import get_graph_embedding_model
from litestar.exceptions import ClientException

from ..models import ContentConfig, SourceType
from ..store_services import docs_table_name
from .abstract_source import AbstractDataSource


class ManualUploadDataSource(AbstractDataSource):
    """Data source for manual uploads of local files."""

    def __init__(self) -> None:
        super().__init__("Uploaded Local Files", SourceType.UPLOAD)

    @override
    async def sync_source(
        self, db_session: AsyncSession, source: KnowledgeGraphSource
    ) -> dict[str, Any]:
        raise NotImplementedError("ManualUploadDataSource does not support syncing.")

    async def upload_and_process_document(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        filename: str,
        extracted_text: str,
        total_pages: int | None = None,
        config: ContentConfig | None = None,
    ) -> None:
        """Upload a document and process it."""
        # Validate embedding model before creating any source or documents
        embedding_model = await get_graph_embedding_model(db_session, graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )

        source = await self.get_or_create_source(db_session, graph_id, status="syncing")

        source.status = "syncing"
        await db_session.commit()

        document = await self.create_document_for_source(
            db_session,
            source,
            filename=filename,
            total_pages=total_pages,
            default_document_type="txt",
            content_profile=config.name if config else None,
        )
        try:
            await self.process_document(
                db_session,
                document,
                extracted_text=extracted_text,
                config=config,
                embedding_model=embedding_model,
            )
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
