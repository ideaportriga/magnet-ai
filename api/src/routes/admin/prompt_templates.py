from typing import Annotated

from litestar import post
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK

from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from services.prompt_templates.models import (
    PromptTemplateConfig,
    PromptTemplateExecuteRequest,
    PromptTemplateExecutionResponse,
    PromptTemplatePreviewRequest,
)

from .create_entity_controller import create_entity_controller

PromptTemplatesBaseController = create_entity_controller(
    path_param="/prompt_templates",
    collection_name="prompts",
)


class PromptTemplatesController(PromptTemplatesBaseController):
    tags = ["prompt_templates"]

    @observe(name="Previewing Prompt Template", channel="preview", source="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def preview(
        self,
        data: Annotated[PromptTemplatePreviewRequest, Body()],
    ) -> PromptTemplateExecutionResponse:
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
