from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.collections.service import (
    CollectionsService,
)

from .schemas import Collection, CollectionCreate, CollectionUpdate

if TYPE_CHECKING:
    pass


class CollectionsController(Controller):
    """Collections CRUD"""

    path = "/sql_collections"
    tags = ["sql_Collections"]

    dependencies = providers.create_service_dependencies(
        CollectionsService,
        "collections_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_collections(
        self,
        collections_service: CollectionsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Collection]:
        """List Collections with pagination and filtering."""
        results, total = await collections_service.list_and_count(*filters)
        return collections_service.to_schema(
            results, total, filters=filters, schema_type=Collection
        )

    @post()
    async def create_collection(
        self, collections_service: CollectionsService, data: CollectionCreate
    ) -> Collection:
        """Create a new Collection."""
        obj = await collections_service.create(data)
        return collections_service.to_schema(obj, schema_type=Collection)

    @get("/code/{code:str}")
    async def get_collection_by_code(
        self, collections_service: CollectionsService, code: str
    ) -> Collection:
        """Get a Collection by its system_name."""
        obj = await collections_service.get_one(system_name=code)
        return collections_service.to_schema(obj, schema_type=Collection)

    @get("/{collection_id:uuid}")
    async def get_collection(
        self,
        collections_service: CollectionsService,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to retrieve.",
        ),
    ) -> Collection:
        """Get a Collection by its ID."""
        obj = await collections_service.get(collection_id)
        return collections_service.to_schema(obj, schema_type=Collection)

    @patch("/{collection_id:uuid}")
    async def update_collection(
        self,
        collections_service: CollectionsService,
        data: CollectionUpdate,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to update.",
        ),
    ) -> Collection:
        """Update a Collection."""
        obj = await collections_service.update(
            data, item_id=collection_id, auto_commit=True
        )
        return collections_service.to_schema(obj, schema_type=Collection)

    @delete("/{collection_id:uuid}")
    async def delete_collection(
        self,
        collections_service: CollectionsService,
        collection_id: UUID = Parameter(
            title="Collection ID",
            description="The Collection to delete.",
        ),
    ) -> None:
        """Delete a Collection from the system."""
        _ = await collections_service.delete(collection_id)
