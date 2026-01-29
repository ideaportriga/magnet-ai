import asyncio
import logging
import mimetypes
import re
from typing import Annotated, Any
from urllib.parse import unquote, urlparse
from uuid import UUID

import httpx
from advanced_alchemy.extensions.litestar import providers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from litestar import Controller, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body, Parameter
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.agent_conversation.service import AgentConversationService
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphCreateRequest,
    KnowledgeGraphCreateResponse,
    KnowledgeGraphDiscoveredMetadataExternalSchema,
    KnowledgeGraphDocumentDetailSchema,
    KnowledgeGraphDocumentExternalSchema,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphExtractedMetadataExternalSchema,
    KnowledgeGraphExtractedMetadataUpsertRequest,
    KnowledgeGraphMetadataExtractionRunRequest,
    KnowledgeGraphMetadataExtractionRunResponse,
    KnowledgeGraphRetrievalPreviewRequest,
    KnowledgeGraphRetrievalPreviewResponse,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceScheduleSyncRequest,
    KnowledgeGraphSourceUpdateRequest,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
    KnowledgeGraphUploadUrlRequest,
)
from core.domain.knowledge_graph.service import (
    KnowledgeGraphChunkService,
    KnowledgeGraphDocumentService,
    KnowledgeGraphMetadataService,
    KnowledgeGraphService,
    KnowledgeGraphSourceService,
)
from services.knowledge_graph.retrievers.agent_retriever.agent import (
    continue_conversation,
    start_conversation,
)
from services.knowledge_graph.sources import FileUploadDataSource
from services.observability import observability_overrides, observe

logger = logging.getLogger(__name__)


class KnowledgeGraphController(Controller):
    path = "/knowledge_graphs"
    tags = ["knowledge_graphs"]
    dependencies = {
        **providers.create_service_dependencies(
            KnowledgeGraphService,
            "graph_service",
            filters={
                "pagination_type": "limit_offset",
                "id_filter": UUID,
                "search": "name",
                "search_ignore_case": True,
            },
        ),
        **providers.create_service_dependencies(
            KnowledgeGraphSourceService,
            "source_service",
        ),
        "document_service": Provide(
            KnowledgeGraphDocumentService, sync_to_thread=False
        ),
        "chunk_service": Provide(KnowledgeGraphChunkService, sync_to_thread=False),
        "metadata_service": Provide(
            KnowledgeGraphMetadataService, sync_to_thread=False
        ),
    }

    ###########################################################################
    # KNOWLEDGE GRAPH ENDPOINTS #
    ###########################################################################

    @get("/", status_code=HTTP_200_OK)
    async def list_graphs(
        self, graph_service: KnowledgeGraphService, db_session: AsyncSession
    ) -> list[KnowledgeGraphExternalSchema]:
        return await graph_service.list_graphs(db_session)

    @get("/{graph_id:uuid}", status_code=HTTP_200_OK)
    async def get_graph(
        self,
        graph_service: KnowledgeGraphService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> KnowledgeGraphExternalSchema:
        return await graph_service.get_graph(db_session, graph_id)

    @post("/", status_code=HTTP_200_OK)
    async def create_graph(
        self,
        graph_service: KnowledgeGraphService,
        document_service: KnowledgeGraphDocumentService,
        chunk_service: KnowledgeGraphChunkService,
        db_session: AsyncSession,
        data: KnowledgeGraphCreateRequest,
    ) -> KnowledgeGraphCreateResponse:
        return await graph_service.create_graph(
            db_session,
            data,
            document_service=document_service,
            chunk_service=chunk_service,
        )

    @patch("/{graph_id:uuid}", status_code=HTTP_200_OK)
    async def update_graph(
        self,
        graph_service: KnowledgeGraphService,
        document_service: KnowledgeGraphDocumentService,
        chunk_service: KnowledgeGraphChunkService,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphUpdateRequest,
    ) -> KnowledgeGraphUpdateResponse:
        return await graph_service.update_graph(
            db_session,
            graph_id,
            data,
            document_service=document_service,
            chunk_service=chunk_service,
        )

    @delete("/{graph_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_graph(
        self,
        graph_service: KnowledgeGraphService,
        document_service: KnowledgeGraphDocumentService,
        chunk_service: KnowledgeGraphChunkService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> None:
        await graph_service.delete_graph(
            db_session,
            graph_id,
            document_service=document_service,
            chunk_service=chunk_service,
        )

    @observe(
        name="Uploading file to knowledge graph",
        channel="production",
        source="production",
    )
    @post("/{graph_id:uuid}/upload", status_code=HTTP_200_OK)
    async def upload_file(
        self,
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        graph_id: UUID,
    ) -> dict[str, str]:
        try:
            file_bytes = await data.read()
            await FileUploadDataSource().upload_and_process_file(
                db_session,
                graph_id,
                filename=data.filename,
                file_bytes=file_bytes,
            )
            return {"status": "ok"}
        except ClientException:
            # Re-raise known client exceptions untouched
            raise
        except Exception as e:  # noqa: BLE001
            raise ClientException(f"File upload failed: {e}")

    @observe(
        name="Uploading URL to knowledge graph",
        channel="production",
        source="production",
    )
    @post("/{graph_id:uuid}/upload_url", status_code=HTTP_200_OK)
    async def upload_url(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphUploadUrlRequest,
    ) -> dict[str, str]:
        url = (data.url or "").strip()
        if not url:
            raise ClientException("URL is required")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ClientException("Only http(s) URLs are supported")

        def filename_from_content_disposition(header_value: str | None) -> str | None:
            if not header_value:
                return None

            # RFC 5987: filename*=UTF-8''...
            m = re.search(r"filename\*=(?:UTF-8''|utf-8'')([^;]+)", header_value)
            if m:
                return unquote(m.group(1)).strip().strip('"')

            m = re.search(r'filename="([^"]+)"', header_value)
            if m:
                return m.group(1).strip()

            m = re.search(r"filename=([^;]+)", header_value)
            if m:
                return m.group(1).strip().strip('"')

            return None

        def filename_from_url(u: str) -> str | None:
            try:
                p = urlparse(u)
                name = (p.path or "").split("/")[-1]
                name = unquote(name or "").strip()
                return name or None
            except Exception:
                return None

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                file_bytes = await resp.aread()
                content_type = (
                    (resp.headers.get("content-type") or "").split(";", 1)[0].strip()
                )
                content_disposition = resp.headers.get("content-disposition")
        except httpx.HTTPStatusError as e:
            raise ClientException(
                f"Failed to download URL (HTTP {e.response.status_code})"
            )
        except Exception as e:  # noqa: BLE001
            raise ClientException(f"Failed to download URL: {e}")

        # Best-effort filename inference (used for file type validation + document naming)
        filename = (
            filename_from_content_disposition(content_disposition)
            or filename_from_url(url)
            or "download"
        )
        filename = filename.strip() or "download"

        # Ensure we have an extension when possible (many URLs omit it)
        if "." not in filename:
            guessed_ext = (
                mimetypes.guess_extension(content_type) if content_type else None
            )
            if guessed_ext:
                filename = f"{filename}{guessed_ext}"

        await FileUploadDataSource().upload_and_process_file(
            db_session,
            graph_id,
            filename=filename,
            file_bytes=file_bytes,
        )

        return {"status": "ok"}

    @post("/{graph_id:uuid}/retrieval/preview", status_code=HTTP_200_OK)
    async def preview_retrieval(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphRetrievalPreviewRequest,
    ) -> KnowledgeGraphRetrievalPreviewResponse:
        conversation_service = AgentConversationService(session=db_session)
        conversation_record = None

        if data.conversation_id:
            conversation_record = await conversation_service.get_one_or_none(
                id=str(data.conversation_id)
            )

        if conversation_record:
            result = await continue_conversation(
                db_session,
                graph_id,
                data.query,
                conversation_record.id,
                tool_inputs=data.tool_inputs,
                **observability_overrides(trace_id=conversation_record.trace_id),
            )
            return KnowledgeGraphRetrievalPreviewResponse(**result.model_dump())
        else:
            result = await start_conversation(
                db_session, graph_id, data.query, tool_inputs=data.tool_inputs
            )
            return KnowledgeGraphRetrievalPreviewResponse(**result.model_dump())

    ###########################################################################
    # KNOWLEDGE GRAPH SOURCE ENDPOINTS #
    ###########################################################################

    @get("/{graph_id:uuid}/sources", status_code=HTTP_200_OK)
    async def list_sources(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> list[KnowledgeGraphSourceExternalSchema]:
        return await source_service.list_sources(db_session, graph_id)

    @post("/{graph_id:uuid}/sources", status_code=HTTP_200_OK)
    async def create_source(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphSourceCreateRequest,
    ) -> KnowledgeGraphSourceCreateResponse:
        return await source_service.create_source(db_session, graph_id, data)

    @patch("/{graph_id:uuid}/sources/{source_id:uuid}", status_code=HTTP_200_OK)
    async def update_source(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        data: KnowledgeGraphSourceUpdateRequest,
    ) -> KnowledgeGraphSourceExternalSchema:
        return await source_service.update_source(db_session, graph_id, source_id, data)

    @delete(
        "/{graph_id:uuid}/sources/{source_id:uuid}",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def delete_source(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        cascade: bool = Parameter(
            default=False,
            description="Delete documents and chunks for this source as well",
        ),
    ) -> None:
        await source_service.delete_source(db_session, graph_id, source_id, cascade)

    @observe(
        name="Sync knowledge graph source",
        channel="production",
        source="production",
    )
    @post("/{graph_id:uuid}/sources/{source_id:uuid}/sync", status_code=HTTP_200_OK)
    async def sync_source(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
    ) -> dict[str, Any]:
        # Update status to "syncing" synchronously before launching background task
        await source_service.set_source_status(db_session, source_id, "syncing")
        await db_session.commit()
        
        # Launch sync in background and return immediately to prevent stuck "syncing" status on page refresh
        asyncio.create_task(
            source_service.sync_source_background(graph_id, source_id)
        )
        return {"status": "started", "message": "Sync started in background"}

    @observe(
        name="Schedule syncing knowledge graph source",
        channel="production",
        source="production",
    )
    @post(
        "/{graph_id:uuid}/sources/{source_id:uuid}/schedule_sync",
        status_code=HTTP_200_OK,
    )
    async def schedule_source_sync(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        scheduler: AsyncIOScheduler,
        data: Annotated[KnowledgeGraphSourceScheduleSyncRequest | None, Body()] = None,
    ) -> dict[str, Any]:
        return await source_service.schedule_source_sync(
            db_session, graph_id, source_id, scheduler, data
        )

    @observe(
        name="Unschedule syncing knowledge graph source",
        channel="production",
        source="production",
    )
    @delete(
        "/{graph_id:uuid}/sources/{source_id:uuid}/schedule_sync",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def unschedule_source_sync(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        scheduler: AsyncIOScheduler,
    ) -> None:
        await source_service.unschedule_source_sync(
            db_session, graph_id, source_id, scheduler
        )

    ###########################################################################
    # KNOWLEDGE GRAPH DOCUMENT ENDPOINTS #
    ###########################################################################

    @get("/{graph_id:uuid}/documents", status_code=HTTP_200_OK)
    async def list_documents(
        self,
        document_service: KnowledgeGraphDocumentService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> list[KnowledgeGraphDocumentExternalSchema]:
        return await document_service.list_documents(db_session, graph_id)

    @get("/{graph_id:uuid}/documents/{document_id:uuid}", status_code=HTTP_200_OK)
    async def get_document(
        self,
        document_service: KnowledgeGraphDocumentService,
        db_session: AsyncSession,
        graph_id: UUID,
        document_id: UUID,
    ) -> KnowledgeGraphDocumentDetailSchema:
        return await document_service.get_document(db_session, graph_id, document_id)

    @delete(
        "/{graph_id:uuid}/documents/{document_id:uuid}",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def delete_document(
        self,
        document_service: KnowledgeGraphDocumentService,
        db_session: AsyncSession,
        graph_id: UUID,
        document_id: UUID,
    ) -> None:
        await document_service.delete_document(db_session, graph_id, document_id)

    ###########################################################################
    # KNOWLEDGE GRAPH CHUNK ENDPOINTS #
    ###########################################################################

    @get("/{graph_id:uuid}/chunks", status_code=HTTP_200_OK)
    async def list_all_chunks(
        self,
        chunk_service: KnowledgeGraphChunkService,
        db_session: AsyncSession,
        graph_id: UUID,
        limit: int = Parameter(default=50, ge=1, le=500),
        offset: int = Parameter(default=0, ge=0),
        q: str | None = Parameter(default=None, query="q"),
    ) -> list[KnowledgeGraphChunkExternalSchema]:
        return await chunk_service.list_chunks(db_session, graph_id, limit, offset, q)

    @get(
        "/{graph_id:uuid}/documents/{document_id:uuid}/chunks",
        status_code=HTTP_200_OK,
    )
    async def list_document_chunks(
        self,
        chunk_service: KnowledgeGraphChunkService,
        db_session: AsyncSession,
        graph_id: UUID,
        document_id: UUID,
        limit: int = Parameter(default=50, ge=1, le=500),
        offset: int = Parameter(default=0, ge=0),
    ) -> list[KnowledgeGraphChunkExternalSchema]:
        return await chunk_service.list_chunks(
            db_session, graph_id, limit, offset, None, document_id
        )

    ###########################################################################
    # KNOWLEDGE GRAPH METADATA ENDPOINTS #
    ###########################################################################

    @get("/{graph_id:uuid}/metadata/discovered", status_code=HTTP_200_OK)
    async def list_discovered_metadata(
        self,
        metadata_service: KnowledgeGraphMetadataService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> list[KnowledgeGraphDiscoveredMetadataExternalSchema]:
        return await metadata_service.list_discovered_metadata(db_session, graph_id)

    @get("/{graph_id:uuid}/metadata/extracted", status_code=HTTP_200_OK)
    async def list_extracted_metadata(
        self,
        metadata_service: KnowledgeGraphMetadataService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> list[KnowledgeGraphExtractedMetadataExternalSchema]:
        return await metadata_service.list_extracted_metadata(db_session, graph_id)

    @post("/{graph_id:uuid}/metadata/extracted", status_code=HTTP_200_OK)
    async def upsert_extracted_metadata_field(
        self,
        metadata_service: KnowledgeGraphMetadataService,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphExtractedMetadataUpsertRequest,
    ) -> KnowledgeGraphExtractedMetadataExternalSchema:
        return await metadata_service.upsert_extracted_metadata_field(
            db_session, graph_id, data
        )

    @delete(
        "/{graph_id:uuid}/metadata/extracted/{name:str}",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def delete_extracted_metadata_field(
        self,
        metadata_service: KnowledgeGraphMetadataService,
        db_session: AsyncSession,
        graph_id: UUID,
        name: str,
    ) -> None:
        await metadata_service.delete_extracted_metadata_field(
            db_session, graph_id, name
        )

    @observe(
        name="Running knowledge graph metadata/entity extraction",
        channel="production",
        source="production",
    )
    @post("/{graph_id:uuid}/metadata/extract", status_code=HTTP_200_OK)
    async def run_metadata_extraction(
        self,
        metadata_service: KnowledgeGraphMetadataService,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphMetadataExtractionRunRequest,
    ) -> KnowledgeGraphMetadataExtractionRunResponse:
        """Start (and run) metadata extraction for all documents/chunks in a graph."""
        return await metadata_service.run_metadata_extraction(
            db_session, graph_id, data
        )
