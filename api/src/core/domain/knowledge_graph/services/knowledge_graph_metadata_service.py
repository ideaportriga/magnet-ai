from __future__ import annotations

from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphMetadataDiscovery,
    KnowledgeGraphMetadataExtraction,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphDiscoveredMetadataExternalSchema,
    KnowledgeGraphExtractedMetadataExternalSchema,
    KnowledgeGraphExtractedMetadataUpsertRequest,
    KnowledgeGraphMetadataExtractionRunRequest,
    KnowledgeGraphMetadataExtractionRunResponse,
    KnowledgeGraphSourceLinkExternalSchema,
)


class KnowledgeGraphMetadataService:
    async def list_discovered_metadata(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDiscoveredMetadataExternalSchema]:
        # Ensure the graph exists so we can distinguish "no fields yet" vs "graph not found".
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataDiscovery)
            .where(KnowledgeGraphMetadataDiscovery.graph_id == graph_id)
            .where(KnowledgeGraphMetadataDiscovery.origin.in_(("file", "source")))
            .options(selectinload(KnowledgeGraphMetadataDiscovery.source))
            .order_by(
                KnowledgeGraphMetadataDiscovery.value_count.desc(),
                KnowledgeGraphMetadataDiscovery.name.asc(),
                KnowledgeGraphMetadataDiscovery.created_at.desc(),
            )
        )
        rows = res.scalars().all()

        return [
            KnowledgeGraphDiscoveredMetadataExternalSchema(
                id=str(row.id),
                name=row.name,
                inferred_type=row.inferred_type,
                origin=row.origin,
                sample_values=row.sample_values,
                value_count=int(row.value_count or 0),
                source=KnowledgeGraphSourceLinkExternalSchema(
                    id=str(row.source.id),
                    name=row.source.name,
                    type=row.source.type,
                )
                if row.source is not None
                else None,
                created_at=row.created_at.isoformat() if row.created_at else None,
                updated_at=row.updated_at.isoformat() if row.updated_at else None,
            )
            for row in rows
        ]

    async def list_extracted_metadata(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphExtractedMetadataExternalSchema]:
        # Ensure the graph exists so we can distinguish "no fields yet" vs "graph not found".
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction)
            .where(KnowledgeGraphMetadataExtraction.graph_id == graph_id)
            .order_by(
                KnowledgeGraphMetadataExtraction.value_count.desc(),
                KnowledgeGraphMetadataExtraction.name.asc(),
                KnowledgeGraphMetadataExtraction.created_at.desc(),
            )
        )
        rows = res.scalars().all()

        out: list[KnowledgeGraphExtractedMetadataExternalSchema] = []
        for row in rows:
            settings = row.settings if isinstance(row.settings, dict) else {}
            allowed_values = settings.get("allowed_values")
            if not isinstance(allowed_values, list):
                allowed_values = None
            out.append(
                KnowledgeGraphExtractedMetadataExternalSchema(
                    id=str(row.id),
                    name=row.name,
                    value_type=str(settings.get("value_type") or "string"),
                    is_multiple=bool(settings.get("is_multiple")),
                    is_required=bool(settings.get("is_required")),
                    allowed_values=allowed_values,
                    llm_extraction_hint=str(settings.get("llm_extraction_hint") or "")
                    or None,
                    sample_values=row.sample_values,
                    value_count=int(row.value_count or 0),
                    created_at=row.created_at.isoformat() if row.created_at else None,
                    updated_at=row.updated_at.isoformat() if row.updated_at else None,
                )
            )
        return out

    async def upsert_extracted_metadata_field(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphExtractedMetadataUpsertRequest,
    ) -> KnowledgeGraphExtractedMetadataExternalSchema:
        # Ensure graph exists
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        name = str(getattr(data, "name", "") or "").strip()
        if not name:
            raise ClientException("Field name is required")

        value_type = (
            str(getattr(data, "value_type", "") or "string").strip() or "string"
        )
        is_multiple = bool(getattr(data, "is_multiple", False))
        is_required = bool(getattr(data, "is_required", False))
        allowed_values = getattr(data, "allowed_values", None)
        if allowed_values is not None and not isinstance(allowed_values, list):
            allowed_values = None
        llm_extraction_hint = (
            str(getattr(data, "llm_extraction_hint", "") or "").strip() or None
        )

        settings: dict[str, Any] = {
            "value_type": value_type,
            "is_multiple": is_multiple,
            "is_required": is_required,
        }
        if allowed_values is not None:
            settings["allowed_values"] = allowed_values
        if llm_extraction_hint:
            settings["llm_extraction_hint"] = llm_extraction_hint

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id,
                KnowledgeGraphMetadataExtraction.name == name,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = KnowledgeGraphMetadataExtraction(
                graph_id=graph_id,
                name=name,
                settings=settings,
                sample_values=None,
                value_count=0,
            )
            db_session.add(row)
        else:
            row.settings = settings

        await db_session.commit()
        await db_session.refresh(row)

        allowed_values_out = settings.get("allowed_values")
        if not isinstance(allowed_values_out, list):
            allowed_values_out = None

        return KnowledgeGraphExtractedMetadataExternalSchema(
            id=str(row.id),
            name=row.name,
            value_type=str(settings.get("value_type") or "string"),
            is_multiple=bool(settings.get("is_multiple")),
            is_required=bool(settings.get("is_required")),
            allowed_values=allowed_values_out,
            llm_extraction_hint=str(settings.get("llm_extraction_hint") or "") or None,
            sample_values=row.sample_values,
            value_count=int(row.value_count or 0),
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def delete_extracted_metadata_field(
        self, db_session: AsyncSession, graph_id: UUID, name: str
    ) -> None:
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        fname = str(name or "").strip()
        if not fname:
            raise ClientException("Field name is required")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id,
                KnowledgeGraphMetadataExtraction.name == fname,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            return

        await db_session.delete(row)
        await db_session.commit()

    async def run_metadata_extraction(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphMetadataExtractionRunRequest,
    ) -> KnowledgeGraphMetadataExtractionRunResponse:
        """Trigger LLM-based metadata extraction for all documents/chunks in a graph.

        This endpoint is intentionally best-effort and may take time for large graphs.
        """
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = graph_res.scalar_one_or_none()
        if not graph:
            raise NotFoundException("Graph not found")

        settings = getattr(graph, "settings", None) or {}
        metadata_settings = (
            settings.get("metadata") if isinstance(settings, dict) else {}
        )
        extraction_settings = (
            metadata_settings.get("extraction")
            if isinstance(metadata_settings, dict)
            else {}
        ) or {}

        # Determine approach (prefer request; fall back to persisted settings)
        approach_raw = (
            str(data.approach).strip()
            if getattr(data, "approach", None) is not None
            else str(extraction_settings.get("approach") or "").strip()
        )
        if approach_raw not in ("chunks", "document"):
            raise ClientException("Extraction approach must be 'chunks' or 'document'")

        prompt_template_system_name = (
            str(data.prompt_template_system_name).strip()
            if getattr(data, "prompt_template_system_name", None) is not None
            else str(
                extraction_settings.get("prompt_template_system_name") or ""
            ).strip()
        )
        if not prompt_template_system_name:
            raise ClientException("Prompt template is required to run extraction")

        segment_size = (
            int(data.segment_size)
            if getattr(data, "segment_size", None) is not None
            else int(extraction_settings.get("segment_size") or 18000)
        )
        segment_overlap = (
            float(data.segment_overlap)
            if getattr(data, "segment_overlap", None) is not None
            else float(extraction_settings.get("segment_overlap") or 0.1)
        )

        # Import locally to avoid heavy imports / circular deps at module import time
        from services.knowledge_graph.llm_metadata_extraction import (
            build_typescript_schema_from_field_definitions,
            run_graph_llm_metadata_extraction,
        )

        # Schema + aggregation whitelist come strictly from DB-stored extraction fields.
        extracted_res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id
            )
        )
        extracted_rows = extracted_res.scalars().all()
        if not extracted_rows:
            raise ClientException("No extracted metadata fields configured")

        extracted_defs: list[dict[str, Any]] = []
        extraction_field_settings: dict[str, dict[str, Any]] = {}
        for r in extracted_rows:
            settings = r.settings if isinstance(r.settings, dict) else {}
            extracted_defs.append({"name": r.name, **settings})
            extraction_field_settings[r.name] = settings

        schema_str = build_typescript_schema_from_field_definitions(extracted_defs)

        # Reset aggregated stats so the UI reflects the current extraction run.
        await db_session.execute(
            update(KnowledgeGraphMetadataExtraction)
            .where(KnowledgeGraphMetadataExtraction.graph_id == graph_id)
            .values(sample_values=None, value_count=0, updated_at=func.now())
        )
        await db_session.commit()

        result = await run_graph_llm_metadata_extraction(
            db_session,
            graph_id=graph_id,
            approach=approach_raw,  # type: ignore[arg-type]
            prompt_template_system_name=prompt_template_system_name,
            extraction_field_settings=extraction_field_settings,
            schema=schema_str,
            segment_size=segment_size,
            segment_overlap=segment_overlap,
        )

        return KnowledgeGraphMetadataExtractionRunResponse(status="ok", **result)
