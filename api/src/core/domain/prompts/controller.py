from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, delete, get, patch, post
from litestar.exceptions import ClientException
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_200_OK

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.prompts.service import (
    PromptsService,
)
from guards.permissions import Permission, require_permission
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    tenant_system_name_filter,
    visibility_filter_for,
)
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from services.prompt_templates.models import (
    PromptTemplateConfig,
    PromptTemplateExecuteRequest,
    PromptTemplateExecutionResponse,
    PromptTemplatePreviewRequest,
)

from .schemas import Prompt, PromptCreate, PromptUpdate

_RESOURCE = "prompts"

if TYPE_CHECKING:
    pass


class PromptsController(Controller):
    """Prompts CRUD"""

    path = "/prompt_templates"
    tags = ["Admin / Prompt Templates"]

    dependencies = providers.create_service_dependencies(
        PromptsService,
        "prompts_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
            "in_fields": [
                providers.FieldNameType("system_name", str),
            ],
        },
    )

    @get(guards=[require_permission(Permission.PROMPTS_READ)])
    async def list_prompts(
        self,
        prompts_service: PromptsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[Prompt]:
        """List prompts — filtered by record-level visibility (PR 10)."""
        from core.db.models.prompt.prompt import Prompt as PromptModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            prompts_service,
            request=request,
            model=PromptModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await prompts_service.list_and_count(*extra_filters)
        page = prompts_service.to_schema(
            results, total, filters=filters, schema_type=Prompt
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    prompts_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.PROMPTS_WRITE)])
    async def create_prompt(
        self,
        prompts_service: PromptsService,
        data: PromptCreate,
        request: Request,
        audit_username: str | None,
    ) -> Prompt:
        """Create a new prompt. tenant_id + owner_id forced from auth."""
        from core.db.models.prompt.prompt import Prompt as PromptModel

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await prompts_service.create(PromptModel(**payload), auto_commit=True)
        schema = prompts_service.to_schema(obj, schema_type=Prompt)
        return await attach_permissions(
            prompts_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/code/{code:str}", guards=[require_permission(Permission.PROMPTS_READ)])
    async def get_prompt_by_code(
        self, prompts_service: PromptsService, code: str, request: Request
    ) -> Prompt:
        """Get a prompt by its system_name."""
        from core.db.models.prompt.prompt import Prompt as PromptModel

        obj = await prompts_service.get_one(
            tenant_system_name_filter(request, PromptModel, code)
        )
        await enforce_view_or_404(
            prompts_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = prompts_service.to_schema(obj, schema_type=Prompt)
        return await attach_permissions(
            prompts_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/{prompt_id:uuid}", guards=[require_permission(Permission.PROMPTS_READ)])
    async def get_prompt(
        self,
        prompts_service: PromptsService,
        request: Request,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to retrieve.",
        ),
    ) -> Prompt:
        """Get a prompt by its ID. 404 if caller can't view it."""
        obj = await prompts_service.get(prompt_id)
        await enforce_view_or_404(
            prompts_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = prompts_service.to_schema(obj, schema_type=Prompt)
        return await attach_permissions(
            prompts_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @patch("/{prompt_id:uuid}", guards=[require_permission(Permission.PROMPTS_WRITE)])
    async def update_prompt(
        self,
        prompts_service: PromptsService,
        data: PromptUpdate,
        request: Request,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to update.",
        ),
        audit_username: str | None = None,
    ) -> Prompt:
        """Update a prompt. 404/403 per record-level access rules."""
        existing = await prompts_service.get(prompt_id)
        await enforce_action_or_403(
            prompts_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await prompts_service.update(
            update_data, item_id=prompt_id, auto_commit=True
        )
        schema = prompts_service.to_schema(obj, schema_type=Prompt)
        return await attach_permissions(
            prompts_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @delete("/{prompt_id:uuid}", guards=[require_permission(Permission.PROMPTS_DELETE)])
    async def delete_prompt(
        self,
        prompts_service: PromptsService,
        request: Request,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to delete.",
        ),
    ) -> None:
        """Delete a prompt. 404/403 per record-level access rules."""
        existing = await prompts_service.get(prompt_id)
        await enforce_action_or_403(
            prompts_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        _ = await prompts_service.delete(prompt_id)

    @observe(name="Previewing Prompt Template", channel="preview", source="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def preview(
        self,
        data: Annotated[PromptTemplatePreviewRequest, Body()],
    ) -> PromptTemplateExecutionResponse:
        """Preview a prompt template with test configuration."""
        observability_context.update_current_trace(
            name=data.name, type="prompt-template"
        )

        try:
            result = await execute_prompt_template(
                system_name_or_config=data.system_name_for_prompt_template,
                template_variant=data.prompt_template_variant,
                config_override=PromptTemplateConfig(
                    messages=data.messages,
                    llm_name=data.model,
                    temperature=data.temperature,
                    top_p=data.top_p,
                    max_tokens=data.max_tokens,
                    response_format=data.response_format,
                    model=data.system_name_for_model,
                ),
            )
        except ValueError as exc:
            error_message = str(exc)
            if "provider_system_name configured" not in error_message:
                raise
            if "Model 'None'" in error_message:
                error_message = "LLM model is required to preview a prompt template."
            raise ClientException(error_message) from exc

        return result

    # This is duplicated in user routes. TODO - delete after verifying it's not used in admin panel
    @observe(name="Executing Prompt Template", channel="production")
    @post("/execute", status_code=HTTP_200_OK)
    async def execute(
        self,
        data: Annotated[PromptTemplateExecuteRequest, Body()],
    ) -> PromptTemplateExecutionResponse:
        """Execute a prompt template."""
        prompt_template_config = await get_prompt_template_by_system_name_flat(
            data.system_name,
        )
        observability_context.update_current_trace(
            name=prompt_template_config.get("name"), type="prompt-template"
        )

        result = await execute_prompt_template(
            system_name_or_config=prompt_template_config,
            template_values=data.system_message_values,
            template_additional_messages=[
                {
                    "role": "user",
                    "content": data.user_message,
                },
            ],
        )

        return result
