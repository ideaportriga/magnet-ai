import logging
from typing import Annotated, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import providers
from litestar import Controller, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
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
    KnowledgeGraphDocumentExternalSchema,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphRetrievalPreviewRequest,
    KnowledgeGraphRetrievalPreviewResponse,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceUpdateRequest,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
)
from core.domain.knowledge_graph.service import (
    KnowledgeGraphChunkService,
    KnowledgeGraphDocumentService,
    KnowledgeGraphService,
    KnowledgeGraphSourceService,
)
from services.observability import observe, observability_overrides

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
        db_session: AsyncSession,
        data: KnowledgeGraphCreateRequest,
    ) -> KnowledgeGraphCreateResponse:
        return await graph_service.create_graph(db_session, data)

    @patch("/{graph_id:uuid}", status_code=HTTP_200_OK)
    async def update_graph(
        self,
        graph_service: KnowledgeGraphService,
        graph_id: UUID,
        data: KnowledgeGraphUpdateRequest,
    ) -> KnowledgeGraphUpdateResponse:
        return await graph_service.update_graph(graph_id, data)

    @delete("/{graph_id:uuid}", status_code=HTTP_204_NO_CONTENT)
    async def delete_graph(
        self,
        graph_service: KnowledgeGraphService,
        db_session: AsyncSession,
        graph_id: UUID,
    ) -> None:
        await graph_service.delete_graph(db_session, graph_id)

    @observe(
        name="Uploading file to knowledge graph",
        channel="production",
        source="production",
    )
    @post("/{graph_id:uuid}/upload", status_code=HTTP_200_OK)
    async def upload_file(
        self,
        graph_service: KnowledgeGraphService,
        db_session: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        graph_id: UUID,
    ) -> dict[str, str]:
        file_bytes = await data.read()
        return await graph_service.upload_file(
            db_session, graph_id, data.filename, file_bytes
        )

    @post("/{graph_id:uuid}/retrieval/preview", status_code=HTTP_200_OK)
    async def preview_retrieval(
        self,
        graph_service: KnowledgeGraphService,
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
            return await graph_service.continue_conversation(
                db_session,
                graph_id,
                data.query,
                conversation_record.id,
                **observability_overrides(trace_id=conversation_record.trace_id),
            )
        else:
            return await graph_service.start_conversation(
                db_session, graph_id, data.query
            )

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

    @post("/{graph_id:uuid}/sources/{source_id:uuid}/sync", status_code=HTTP_200_OK)
    async def sync_source(
        self,
        source_service: KnowledgeGraphSourceService,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
    ) -> dict[str, Any]:
        return await source_service.sync_source(db_session, graph_id, source_id)

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
    ) -> KnowledgeGraphDocumentExternalSchema:
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
