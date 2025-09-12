from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.prompts.service import (
    PromptsService,
)

from .schemas import Prompt, PromptCreate, PromptUpdate

if TYPE_CHECKING:
    pass


class PromptsController(Controller):
    """Prompts CRUD"""

    path = "/sql_prompts"
    tags = ["sql_Prompts"]

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
