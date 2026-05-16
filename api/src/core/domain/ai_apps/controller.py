from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.ai_apps.service import (
    AiAppsService,
)
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    tenant_system_name_filter,
    visibility_filter_for,
)

from .schemas import AiApp, AiAppCreate, AiAppUpdate

if TYPE_CHECKING:
    pass


_RESOURCE = "ai_apps"


class AiAppsController(Controller):
    """AI Apps CRUD — tenant + record-level scoped (PR 10 rollout)."""

    path = "/ai_apps"
    tags = ["Admin / AI Apps"]

    dependencies = providers.create_service_dependencies(
        AiAppsService,
        "ai_apps_service",
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

    @get(guards=[require_permission(Permission.AI_APPS_READ)])
    async def list_ai_apps(
        self,
        ai_apps_service: AiAppsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[AiApp]:
        """List AI apps — filtered by record-level visibility."""
        from core.db.models.ai_app.ai_app import AIApp as AIAppModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            ai_apps_service,
            request=request,
            model=AIAppModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await ai_apps_service.list_and_count(*extra_filters)
        page = ai_apps_service.to_schema(
            results, total, filters=filters, schema_type=AiApp
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    ai_apps_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.AI_APPS_WRITE)])
    async def create_ai_app(
        self,
        ai_apps_service: AiAppsService,
        data: AiAppCreate,
        request: Request,
        audit_username: str | None,
    ) -> AiApp:
        """Create a new AI app. tenant_id + owner_id forced from auth."""
        from core.db.models.ai_app.ai_app import AIApp as AIAppModel

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await ai_apps_service.create(AIAppModel(**payload), auto_commit=True)
        schema = ai_apps_service.to_schema(obj, schema_type=AiApp)
        return await attach_permissions(
            ai_apps_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/code/{code:str}", guards=[require_permission(Permission.AI_APPS_READ)])
    async def get_ai_app_by_code(
        self, ai_apps_service: AiAppsService, code: str, request: Request
    ) -> AiApp:
        """Get an AI app by its system_name."""
        from core.db.models.ai_app.ai_app import AIApp as AIAppModel

        obj = await ai_apps_service.get_one(
            tenant_system_name_filter(request, AIAppModel, code)
        )
        await enforce_view_or_404(
            ai_apps_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = ai_apps_service.to_schema(obj, schema_type=AiApp)
        return await attach_permissions(
            ai_apps_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/{ai_app_id:uuid}", guards=[require_permission(Permission.AI_APPS_READ)])
    async def get_ai_app(
        self,
        ai_apps_service: AiAppsService,
        request: Request,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to retrieve.",
        ),
    ) -> AiApp:
        """Get an AI app by its ID. 404 if caller can't view it."""
        obj = await ai_apps_service.get(ai_app_id)
        await enforce_view_or_404(
            ai_apps_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = ai_apps_service.to_schema(obj, schema_type=AiApp)
        return await attach_permissions(
            ai_apps_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @patch("/{ai_app_id:uuid}", guards=[require_permission(Permission.AI_APPS_WRITE)])
    async def update_ai_app(
        self,
        ai_apps_service: AiAppsService,
        data: AiAppUpdate,
        request: Request,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to update.",
        ),
        audit_username: str | None = None,
    ) -> AiApp:
        """Update an AI app. 404/403 per record-level access rules."""
        existing = await ai_apps_service.get(ai_app_id)
        await enforce_action_or_403(
            ai_apps_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await ai_apps_service.update(
            update_data, item_id=ai_app_id, auto_commit=True
        )
        schema = ai_apps_service.to_schema(obj, schema_type=AiApp)
        return await attach_permissions(
            ai_apps_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @delete("/{ai_app_id:uuid}", guards=[require_permission(Permission.AI_APPS_DELETE)])
    async def delete_ai_app(
        self,
        ai_apps_service: AiAppsService,
        request: Request,
        ai_app_id: UUID = Parameter(
            title="AI App ID",
            description="The AI app to delete.",
        ),
    ) -> None:
        """Delete an AI app. 404/403 per record-level access rules."""
        existing = await ai_apps_service.get(ai_app_id)
        await enforce_action_or_403(
            ai_apps_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        await ai_apps_service.delete(ai_app_id)
