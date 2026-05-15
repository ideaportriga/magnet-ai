from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Dependency, Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.collections.service import (
    CollectionsService,
)
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    visibility_filter_for,
)
from storage import StorageService

from .schemas import Collection, CollectionCreate, CollectionUpdate

if TYPE_CHECKING:
    pass


_RESOURCE = "collections"


class CollectionsController(Controller):
    """Collections CRUD — tenant + record-level scoped (PR 10 rollout)."""

    path = "/sql_collections"
    tags = ["Admin / Collections"]

    dependencies = providers.create_service_dependencies(
        CollectionsService,
        "collections_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.COLLECTIONS_READ)])
    async def list_collections(
        self,
        collections_service: CollectionsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[Collection]:
        """List Collections — filtered by record-level visibility."""
        from core.db.models.collection.collection import Collection as CollectionModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            collections_service,
            request=request,
            model=CollectionModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)

        results, total = await collections_service.list_and_count(*extra_filters)
        page = collections_service.to_schema(
            results, total, filters=filters, schema_type=Collection
        )

        # Attach `_permissions` to each item via the shared helper.
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    collections_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.COLLECTIONS_WRITE)])
    async def create_collection(
        self,
        collections_service: CollectionsService,
        data: CollectionCreate,
        request: Request,
        audit_username: str | None,
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> Collection:
        """Create a new Collection. tenant_id + owner_id forced from auth."""
        from core.db.models.collection.collection import Collection as CollectionModel

        data.created_by = audit_username
        data.updated_by = audit_username

        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username

        obj = await collections_service.upsert(
            CollectionModel(**payload),
            match_fields=["tenant_id", "system_name"],
            auto_commit=True,
        )

        # Claim any temp-uploaded files and reassign them to this collection.
        if storage_service and db_session and data.source:
            uploaded_files = data.source.get("uploaded_files", [])
            file_ids = [
                uf["file_id"]
                for uf in uploaded_files
                if isinstance(uf, dict) and "file_id" in uf
            ]
            if file_ids:
                entity_id = obj.id
                for fid in file_ids:
                    try:
                        stored = await storage_service.get(db_session, UUID(str(fid)))
                        if stored and stored.entity_type == "ks_source_temp":
                            stored.entity_type = "ks_source"
                            stored.entity_id = entity_id
                            db_session.add(stored)
                    except Exception:
                        pass
                await db_session.commit()

        schema = collections_service.to_schema(obj, schema_type=Collection)
        return await attach_permissions(
            collections_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/code/{code:str}", guards=[require_permission(Permission.COLLECTIONS_READ)])
    async def get_collection_by_code(
        self,
        collections_service: CollectionsService,
        code: str,
        request: Request,
    ) -> Collection:
        """Get a Collection by its system_name."""
        obj = await collections_service.get_one(system_name=code)
        await enforce_view_or_404(
            collections_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = collections_service.to_schema(obj, schema_type=Collection)
        return await attach_permissions(
            collections_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get(
        "/{collection_id:uuid}",
        guards=[require_permission(Permission.COLLECTIONS_READ)],
    )
    async def get_collection(
        self,
        collections_service: CollectionsService,
        request: Request,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to retrieve.",
        ),
    ) -> Collection:
        """Get a Collection by its ID. 404 if the caller can't view it."""
        obj = await collections_service.get(collection_id)
        await enforce_view_or_404(
            collections_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = collections_service.to_schema(obj, schema_type=Collection)
        return await attach_permissions(
            collections_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @patch(
        "/{collection_id:uuid}",
        guards=[require_permission(Permission.COLLECTIONS_WRITE)],
    )
    async def update_collection(
        self,
        collections_service: CollectionsService,
        data: CollectionUpdate,
        request: Request,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to update.",
        ),
        audit_username: str | None = None,
    ) -> Collection:
        """Update a Collection. 404/403 per record-level access rules."""
        existing = await collections_service.get(collection_id)
        await enforce_action_or_403(
            collections_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )

        update_data = data.model_dump(exclude_unset=True)
        # Strip fields that must come from auth.
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await collections_service.update(
            update_data, item_id=collection_id, auto_commit=True
        )
        schema = collections_service.to_schema(obj, schema_type=Collection)
        return await attach_permissions(
            collections_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @delete(
        "/{collection_id:uuid}",
        guards=[require_permission(Permission.COLLECTIONS_DELETE)],
    )
    async def delete_collection(
        self,
        collections_service: CollectionsService,
        request: Request,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to delete.",
        ),
    ) -> None:
        """Delete a Collection. 404/403 per record-level access rules."""
        existing = await collections_service.get(collection_id)
        await enforce_action_or_403(
            collections_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        _ = await collections_service.delete(collection_id)
