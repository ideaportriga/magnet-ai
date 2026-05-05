"""MCP tool: fetch a Magnet prompt template by its system_name.

Read-only example tool that exercises the existing prompt-templates service.

Why a Pydantic output model: FastMCP introspects the function's return type
to generate the tool's JSON-Schema `outputSchema`. Returning `dict[str, Any]`
gives clients a useless schema (`additionalProperties: true` blob); returning
a typed model gives them a usable, self-describing contract.
"""

from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Optional

from pydantic import BaseModel, Field

from prompt_templates.prompt_templates import get_prompt_template_by_system_name

logger = getLogger(__name__)


class PromptTemplateVariantOut(BaseModel):
    """One variant of a prompt template (e.g. 'default', 'experimental-v2')."""

    variant: str = Field(..., description="Variant name")
    display_name: Optional[str] = Field(None, description="Human-readable label")
    description: Optional[str] = Field(None, description="What this variant is for")
    text: Optional[str] = Field(None, description="The prompt text itself")
    model: Optional[str] = Field(
        None,
        description="Model system_name this variant requests (None = system default)",
        alias="system_name_for_model",
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Sampling temperature"
    )
    top_p: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Top-p (nucleus sampling)", alias="topP"
    )

    model_config = {"populate_by_name": True}


class PromptTemplateOut(BaseModel):
    """A Magnet prompt template — name, description, and all variants."""

    system_name: str = Field(..., description="Stable identifier for the template")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="What the template is for")
    active_variant: Optional[str] = Field(
        None,
        description="Name of the variant currently used in production "
        "(matches one of the `variants[].variant` values)",
    )
    variants: list[PromptTemplateVariantOut] = Field(
        default_factory=list,
        description="All variants defined for this template",
    )
    created_at: Optional[datetime] = Field(None, description="When created")
    updated_at: Optional[datetime] = Field(None, description="When last updated")


async def get_prompt_template_details(system_name: str) -> PromptTemplateOut:
    """Fetch a Magnet prompt template by its system_name.

    Returns the full template — name, description, active variant, and every
    variant's text + model + sampling parameters.
    """
    try:
        raw = await get_prompt_template_by_system_name(system_name)
    except LookupError as e:
        # Surface as a clean tool error rather than an internal exception.
        raise ValueError(str(e)) from e
    return PromptTemplateOut.model_validate(raw)
