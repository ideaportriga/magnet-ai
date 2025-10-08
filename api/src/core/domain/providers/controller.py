from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.providers.service import (
    ProvidersService,
)

from .schemas import Provider, ProviderCreate, ProviderUpdate

if TYPE_CHECKING:
    pass


class ProvidersController(Controller):
    """Providers CRUD"""

    path = "/sql_providers"
    tags = ["sql_Providers"]

    dependencies = providers.create_service_dependencies(
        ProvidersService,
        "providers_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_providers(
        self,
        providers_service: ProvidersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Provider]:
        """List Providers with pagination and filtering."""
        results, total = await providers_service.list_and_count(*filters)
        return providers_service.to_schema(
            results, total, filters=filters, schema_type=Provider
        )

    @post()
    async def create_provider(
        self, providers_service: ProvidersService, data: ProviderCreate
    ) -> Provider:
        """Create a new Provider."""
        obj = await providers_service.create(data)
        return providers_service.to_schema(obj, schema_type=Provider)

    @get("/code/{code:str}")
    async def get_provider_by_code(
        self, providers_service: ProvidersService, code: str
    ) -> Provider:
        """Get a Provider by its system_name."""
        obj = await providers_service.get_one(system_name=code)
        return providers_service.to_schema(obj, schema_type=Provider)

    @get("/{provider_id:uuid}")
    async def get_provider(
        self,
        providers_service: ProvidersService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to retrieve.",
        ),
    ) -> Provider:
        """Get a Provider by its ID."""
        obj = await providers_service.get(provider_id)
        return providers_service.to_schema(obj, schema_type=Provider)

    @patch("/{provider_id:uuid}")
    async def update_provider(
        self,
        providers_service: ProvidersService,
        data: ProviderUpdate,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to update.",
        ),
    ) -> Provider:
        """Update a Provider."""
        obj = await providers_service.update(
            data, item_id=provider_id, auto_commit=True
        )
        return providers_service.to_schema(obj, schema_type=Provider)

    @delete("/{provider_id:uuid}")
    async def delete_provider(
        self,
        providers_service: ProvidersService,
        provider_id: UUID = Parameter(
            title="Provider ID",
            description="The Provider to delete.",
        ),
    ) -> None:
        """Delete a Provider from the system."""
        _ = await providers_service.delete(provider_id)
