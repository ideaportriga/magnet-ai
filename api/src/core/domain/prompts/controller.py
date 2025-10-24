from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_200_OK

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.prompts.service import (
    PromptsService,
)
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from services.prompt_templates.models import (
    PromptTemplateConfig,
    PromptTemplateExecuteRequest,
    PromptTemplateExecutionResponse,
    PromptTemplatePreviewRequest,
)

from .schemas import Prompt, PromptCreate, PromptUpdate

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
            "in_fields": [
                providers.FieldNameType("system_name", str),
            ],
        },
    )

    @get()
    async def list_prompts(
        self,
        prompts_service: PromptsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Prompt]:
        """List prompts with pagination and filtering."""
        results, total = await prompts_service.list_and_count(*filters)
        return prompts_service.to_schema(
            results, total, filters=filters, schema_type=Prompt
        )

    @post()
    async def create_prompt(
        self, prompts_service: PromptsService, data: PromptCreate
    ) -> Prompt:
        """Create a new prompt."""
        obj = await prompts_service.create(data)
        return prompts_service.to_schema(obj, schema_type=Prompt)

    @get("/code/{code:str}")
    async def get_prompt_by_code(
        self, prompts_service: PromptsService, code: str
    ) -> Prompt:
        """Get a prompt by its system_name."""
        obj = await prompts_service.get_one(system_name=code)
        return prompts_service.to_schema(obj, schema_type=Prompt)

    @get("/{prompt_id:uuid}")
    async def get_prompt(
        self,
        prompts_service: PromptsService,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to retrieve.",
        ),
    ) -> Prompt:
        """Get a prompt by its ID."""
        obj = await prompts_service.get(prompt_id)
        return prompts_service.to_schema(obj, schema_type=Prompt)

    @patch("/{prompt_id:uuid}")
    async def update_prompt(
        self,
        prompts_service: PromptsService,
        data: PromptUpdate,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to update.",
        ),
    ) -> Prompt:
        """Update a prompt."""
        obj = await prompts_service.update(data, item_id=prompt_id, auto_commit=True)
        return prompts_service.to_schema(obj, schema_type=Prompt)

    @delete("/{prompt_id:uuid}")
    async def delete_prompt(
        self,
        prompts_service: PromptsService,
        prompt_id: UUID = Parameter(
            title="Prompt ID",
            description="The prompt to delete.",
        ),
    ) -> None:
        """Delete a prompt from the system."""
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
