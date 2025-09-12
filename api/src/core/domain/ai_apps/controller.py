from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.ai_apps.service import (
    AiAppsService,
)

from .schemas import AiApp, AiAppCreate, AiAppUpdate

if TYPE_CHECKING:
    pass


class AiAppsController(Controller):
    """AI Apps CRUD"""

    path = "/sql_ai_apps"
    tags = ["sql_AiApps"]

    dependencies = providers.create_service_dependencies(
        AiAppsService,
        "ai_apps_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_ai_apps(
        self,
        ai_apps_service: AiAppsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[AiApp]:
        """List AI apps with pagination and filtering."""
        results, total = await ai_apps_service.list_and_count(*filters)
        return ai_apps_service.to_schema(
            results, total, filters=filters, schema_type=AiApp
        )

    @post()
    async def create_ai_app(
        self, ai_apps_service: AiAppsService, data: AiAppCreate
    ) -> AiApp:
        """Create a new AI app."""
        obj = await ai_apps_service.create(data)
        return ai_apps_service.to_schema(obj, schema_type=AiApp)

    @get("/code/{code:str}")
    async def get_ai_app_by_code(
        self, ai_apps_service: AiAppsService, code: str
    ) -> AiApp:
        """Get an AI app by its system_name."""
        obj = await ai_apps_service.get_one(system_name=code)
        return ai_apps_service.to_schema(obj, schema_type=AiApp)

    @get("/{ai_app_id:uuid}")
    async def get_ai_app(
        self,
        ai_apps_service: AiAppsService,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to retrieve.",
        ),
    ) -> AiApp:
        """Get an AI app by its ID."""
        obj = await ai_apps_service.get(ai_app_id)
        return ai_apps_service.to_schema(obj, schema_type=AiApp)

    @patch("/{ai_app_id:uuid}")
    async def update_ai_app(
        self,
        ai_apps_service: AiAppsService,
        data: AiAppUpdate,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to update.",
        ),
    ) -> AiApp:
        """Update an AI app."""
        obj = await ai_apps_service.update(data, item_id=ai_app_id, auto_commit=True)
        return ai_apps_service.to_schema(obj, schema_type=AiApp)

    @delete("/{ai_app_id:uuid}")
    async def delete_ai_app(
        self,
        ai_apps_service: AiAppsService,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to delete.",
        ),
    ) -> None:
        """Delete an AI app."""
        await ai_apps_service.delete(ai_app_id)
