from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import NotFoundException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphSource,
    resolve_vector_size_for_embedding_model,
)
from core.domain.ai_models.service import AIModelsService
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphCreateRequest,
    KnowledgeGraphCreateResponse,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
)
from services.knowledge_graph import (
    get_default_content_configs,
    get_default_entity_extraction_settings,
    get_default_metadata_settings,
    get_default_retrieval_settings,
)
from services.knowledge_graph.content_config_services import (
    build_graph_settings_with_virtual_last_resort_profile,
    clone_graph_settings,
    ensure_fluid_topics_structured_profile,
    remove_auto_managed_fluid_topics_structured_profiles,
    sanitize_graph_settings_content_profiles,
    validate_unique_content_profile_names,
)
from services.knowledge_graph.models import SourceType

if TYPE_CHECKING:
    from .knowledge_graph_chunk_service import KnowledgeGraphChunkService
    from .knowledge_graph_document_service import KnowledgeGraphDocumentService
    from .knowledge_graph_edge_service import KnowledgeGraphEdgeService
    from .knowledge_graph_entity_service import KnowledgeGraphEntityService


class KnowledgeGraphService(service.SQLAlchemyAsyncRepositoryService[KnowledgeGraph]):
    """Service for Knowledge Graph operations."""

    @staticmethod
    def _documents_count_subquery():
        return (
            select(
                KnowledgeGraphSource.graph_id.label("graph_id"),
                func.coalesce(func.sum(KnowledgeGraphSource.documents_count), 0).label(
                    "documents_count"
                ),
            )
            .group_by(KnowledgeGraphSource.graph_id)
            .subquery()
        )

    async def _has_sources_of_type(
        self, db_session: AsyncSession, *, graph_id: UUID, source_type: str
    ) -> bool:
        result = await db_session.execute(
            select(KnowledgeGraphSource.id)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == source_type)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_graphs(
        self, db_session: AsyncSession
    ) -> list[KnowledgeGraphExternalSchema]:
        documents_count_sq = self._documents_count_subquery()

        result = await db_session.execute(
            select(
                KnowledgeGraph,
                func.coalesce(documents_count_sq.c.documents_count, 0).label(
                    "documents_count"
                ),
            )
            .outerjoin(
                documents_count_sq, documents_count_sq.c.graph_id == KnowledgeGraph.id
            )
            .order_by(KnowledgeGraph.created_at.desc())
        )
        rows = result.all()

        return [
            KnowledgeGraphExternalSchema(
                id=str(graph.id),
                name=graph.name,
                system_name=getattr(graph, "system_name", None),
                description=getattr(graph, "description", None),
                documents_count=int(documents_count or 0),
                created_at=graph.created_at.isoformat() if graph.created_at else None,
                updated_at=graph.updated_at.isoformat() if graph.updated_at else None,
            )
            for graph, documents_count in rows
        ]

    async def get_graph(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> KnowledgeGraphExternalSchema:
        documents_count_sq = self._documents_count_subquery()
        graph_res = await db_session.execute(
            select(
                KnowledgeGraph,
                func.coalesce(documents_count_sq.c.documents_count, 0).label(
                    "documents_count"
                ),
            )
            .outerjoin(
                documents_count_sq, documents_count_sq.c.graph_id == KnowledgeGraph.id
            )
            .where(KnowledgeGraph.id == graph_id)
        )
        row = graph_res.one_or_none()
        if not row:
            raise NotFoundException("Graph not found")
        graph, documents_count = row
        settings = (
            build_graph_settings_with_virtual_last_resort_profile(
                getattr(graph, "settings", None)
            )
            if hasattr(graph, "settings")
            else None
        )
        return KnowledgeGraphExternalSchema(
            id=str(graph.id),
            name=graph.name,
            system_name=getattr(graph, "system_name", None),
            description=getattr(graph, "description", None),
            documents_count=int(documents_count or 0),
            settings=settings,
            state=getattr(graph, "state", None),
            created_at=graph.created_at.isoformat() if graph.created_at else None,
            updated_at=graph.updated_at.isoformat() if graph.updated_at else None,
        )

    async def create_graph(
        self,
        db_session: AsyncSession,
        data: KnowledgeGraphCreateRequest,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
        entity_service: KnowledgeGraphEntityService | None = None,
        edge_service: KnowledgeGraphEdgeService | None = None,
    ) -> KnowledgeGraphCreateResponse:
        system_name = (
            (data.system_name or data.name)
            .upper()
            .replace(" ", "_")
            .replace(".", "_")
            .strip(" _")
        )

        default_configs = get_default_content_configs()
        retrieval_settings = get_default_retrieval_settings()
        metadata_settings = get_default_metadata_settings()
        entity_extraction_settings = get_default_entity_extraction_settings()
        settings: dict[str, Any] | None = {
            "chunking": {
                "content_settings": [cfg.model_dump() for cfg in default_configs],
            },
            **retrieval_settings,
            **metadata_settings,
            **entity_extraction_settings,
        }

        # Set default embedding model if it exists
        try:
            models_service = AIModelsService(session=db_session)
            default_embedding = await models_service.get_one_or_none(
                type="embeddings", is_default=True
            )
            if default_embedding:
                indexing_cfg = dict((settings.get("indexing") or {}))
                indexing_cfg["embedding_model"] = default_embedding.system_name
                settings["indexing"] = indexing_cfg
        except Exception:
            # Non-fatal: proceed without default embedding if lookup fails
            pass

        created = await self.create(
            {
                "name": data.name,
                "system_name": system_name,
                "description": data.description,
                "settings": settings,
            }
        )

        from .knowledge_graph_chunk_service import KnowledgeGraphChunkService
        from .knowledge_graph_document_service import KnowledgeGraphDocumentService
        from .knowledge_graph_edge_service import KnowledgeGraphEdgeService
        from .knowledge_graph_entity_service import KnowledgeGraphEntityService

        entity_svc = entity_service or KnowledgeGraphEntityService()
        await entity_svc.create_table(db_session, graph_id=created.id)

        edge_svc = edge_service or KnowledgeGraphEdgeService()
        await edge_svc.create_table(db_session, graph_id=created.id)

        # Create per-graph tables only when an embedding model is configured.
        embedding_model = (
            ((settings or {}).get("indexing") or {}).get("embedding_model")
            if isinstance(settings, dict)
            else None
        )
        if isinstance(embedding_model, str) and embedding_model.strip():
            vector_size = await resolve_vector_size_for_embedding_model(embedding_model)
            doc_svc = document_service or KnowledgeGraphDocumentService()
            ch_svc = chunk_service or KnowledgeGraphChunkService()
            await doc_svc.create_table(
                db_session, graph_id=created.id, vector_size=vector_size
            )
            await ch_svc.create_table(
                db_session, graph_id=created.id, vector_size=vector_size
            )

        return KnowledgeGraphCreateResponse(id=str(created.id))

    async def update_graph(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphUpdateRequest,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
    ) -> KnowledgeGraphUpdateResponse:
        from .knowledge_graph_chunk_service import KnowledgeGraphChunkService
        from .knowledge_graph_document_service import KnowledgeGraphDocumentService

        existing = await self.repository.get(graph_id)
        prev_settings = getattr(existing, "settings", None) or {}
        prev_indexing = (
            prev_settings.get("indexing") if isinstance(prev_settings, dict) else None
        )
        prev_embedding_model = (
            (prev_indexing or {}).get("embedding_model")
            if isinstance(prev_indexing, dict)
            else None
        )

        update_payload: dict[str, Any] = {}

        if data.name is not None:
            update_payload["name"] = data.name
        if data.description is not None:
            update_payload["description"] = data.description

        # Base settings start from explicit payload if provided, otherwise existing
        settings_to_apply: dict[str, Any] | None = None
        if data.settings is not None:
            settings_to_apply = clone_graph_settings(data.settings)
        else:
            current_settings = getattr(existing, "settings", None) or {}
            if isinstance(current_settings, dict):
                settings_to_apply = clone_graph_settings(current_settings)

        if data.content_configs is not None:
            if settings_to_apply is None:
                settings_to_apply = {}
            chunking = dict(settings_to_apply.get("chunking") or {})
            chunking["content_settings"] = data.content_configs or []
            settings_to_apply["chunking"] = chunking

        if settings_to_apply is not None:
            sanitize_graph_settings_content_profiles(settings_to_apply)
            has_fluid_topics_sources = await self._has_sources_of_type(
                db_session,
                graph_id=graph_id,
                source_type=str(SourceType.FLUID_TOPICS),
            )
            if has_fluid_topics_sources:
                ensure_fluid_topics_structured_profile(settings_to_apply)
            else:
                remove_auto_managed_fluid_topics_structured_profiles(settings_to_apply)
            validate_unique_content_profile_names(settings_to_apply)
            update_payload["settings"] = settings_to_apply

        updated = await self.update(
            update_payload,
            item_id=graph_id,
            auto_commit=True,
            auto_refresh=True,
        )

        # If embedding model is configured (and changed), ensure per-graph tables exist.
        new_settings = getattr(updated, "settings", None) or {}
        new_indexing = (
            new_settings.get("indexing") if isinstance(new_settings, dict) else None
        )
        new_embedding_model = (
            (new_indexing or {}).get("embedding_model")
            if isinstance(new_indexing, dict)
            else None
        )
        if (
            isinstance(new_embedding_model, str)
            and new_embedding_model.strip()
            and new_embedding_model != prev_embedding_model
        ):
            vector_size = await resolve_vector_size_for_embedding_model(
                new_embedding_model
            )
            doc_svc = document_service or KnowledgeGraphDocumentService()
            ch_svc = chunk_service or KnowledgeGraphChunkService()
            await doc_svc.create_table(
                db_session, graph_id=graph_id, vector_size=vector_size
            )
            await ch_svc.create_table(
                db_session, graph_id=graph_id, vector_size=vector_size
            )

        return KnowledgeGraphUpdateResponse(
            id=str(updated.id),
            name=updated.name,
            system_name=getattr(updated, "system_name", None),
            description=getattr(updated, "description", None),
        )

    async def delete_graph(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
        entity_service: KnowledgeGraphEntityService | None = None,
        edge_service: KnowledgeGraphEdgeService | None = None,
    ) -> None:
        """Delete a graph and drop its per-graph tables."""

        from .knowledge_graph_chunk_service import KnowledgeGraphChunkService
        from .knowledge_graph_document_service import KnowledgeGraphDocumentService
        from .knowledge_graph_edge_service import KnowledgeGraphEdgeService
        from .knowledge_graph_entity_service import KnowledgeGraphEntityService

        # Drop dynamic tables (edges first, then entities, chunks, docs)
        edge_svc = edge_service or KnowledgeGraphEdgeService()
        await edge_svc.drop_table(db_session, graph_id=graph_id)
        doc_svc = document_service or KnowledgeGraphDocumentService()
        ch_svc = chunk_service or KnowledgeGraphChunkService()
        entity_svc = entity_service or KnowledgeGraphEntityService()
        await entity_svc.drop_table(db_session, graph_id=graph_id)
        await ch_svc.drop_table(db_session, graph_id=graph_id)
        await doc_svc.drop_table(db_session, graph_id=graph_id)
        await db_session.commit()

        # Remove graph record
        await self.delete(item_id=graph_id, auto_commit=True)

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraph]):
        model_type = KnowledgeGraph

    repository_type = Repo
