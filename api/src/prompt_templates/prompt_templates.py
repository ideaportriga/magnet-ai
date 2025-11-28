# TODO - think about better place for non-vector stores
# TODO - use system_name/code instead of id
from logging import getLogger

from bson import ObjectId

from core.config.app import alchemy
from core.domain.prompts.schemas import Prompt
from core.domain.prompts.service import PromptsService

logger = getLogger(__name__)


async def get_prompt_template(prompt_template_id: str) -> dict:
    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        prompt_template = await service.get_one_or_none(id=ObjectId(prompt_template_id))
        if not prompt_template:
            raise LookupError(
                f"Prompt template with id '{prompt_template_id}' not found"
            )
        prompt = service.to_schema(prompt_template, schema_type=Prompt)
        return prompt.model_dump()


async def get_prompt_template_by_system_name(prompt_template_system_name: str) -> dict:
    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        prompt_template = await service.get_one_or_none(
            system_name=prompt_template_system_name
        )
        if not prompt_template:
            raise LookupError(
                f"Prompt template with system_name '{prompt_template_system_name}' not found"
            )
        prompt = service.to_schema(prompt_template, schema_type=Prompt)
        return prompt.model_dump()


def transform_to_flat(prompt: dict, variant: str | None = None) -> dict:
    exclude_keys = {
        "active_variant",
        "description",
        "name",
        "system_name",
        "user_message",
    }

    variant = variant or prompt.get("active_variant")
    variant_object = next(
        (v for v in prompt.get("variants", []) if v["variant"] == variant),
        {},
    )

    prompt["active_variant"] = variant

    for key, value in variant_object.items():
        if key not in exclude_keys:
            prompt[key] = value

    # Ensure the id field is serialized
    if "id" in prompt:
        prompt["id"] = str(prompt["id"])
    elif "_id" in prompt:
        prompt["id"] = str(prompt["_id"])

    return prompt


async def get_prompt_template_by_system_name_flat(
    prompt_template_system_name: str,
    variant: str | None = None,
) -> dict:
    prompt = await get_prompt_template_by_system_name(prompt_template_system_name)
    return transform_to_flat(prompt, variant)
