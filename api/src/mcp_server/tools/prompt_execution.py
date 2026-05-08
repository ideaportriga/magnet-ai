"""MCP tool: execute a prompt template against the live LLM.

This tool makes a real LLM call and incurs cost. It is intentionally separate
from the read-only prompt template inspection tools.
"""

from __future__ import annotations

from logging import getLogger
from typing import Optional

from pydantic import BaseModel, Field

from services.prompt_templates.models import PromptTemplateConfig
from services.prompt_templates.services import execute_prompt_template

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------


class PromptRunOut(BaseModel):
    """Result of executing a prompt template."""

    content: str = Field(description="LLM response text")
    cost: Optional[float] = Field(None, description="Total cost in USD")
    latency: Optional[float] = Field(None, description="Latency in milliseconds")
    input_tokens: Optional[int] = Field(None, description="Prompt tokens consumed")
    output_tokens: Optional[int] = Field(
        None, description="Completion tokens generated"
    )
    total_tokens: Optional[int] = Field(None, description="Total tokens consumed")


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


async def prompt_template_run(
    system_name: str,
    user_message: str,
    variant: Optional[str] = None,
    system_prompt_override: Optional[str] = None,
) -> PromptRunOut:
    """Execute a prompt template with a user message and return the LLM response.

    ``variant`` selects which variant to use (defaults to the active variant).

    ``system_prompt_override`` replaces the template's saved system prompt for
    this call only — the template itself is not modified. Use this to test
    prompt improvements before committing them to the template.

    Returns the response text, cost in USD, latency in milliseconds, and token
    counts. Each call incurs real LLM cost.
    """
    try:
        if system_prompt_override:
            config_override = PromptTemplateConfig(
                messages=[
                    {"role": "system", "content": system_prompt_override},
                    {"role": "user", "content": user_message},
                ]
            )
            result = await execute_prompt_template(
                system_name_or_config=system_name,
                template_variant=variant,
                config_override=config_override,
            )
        else:
            result = await execute_prompt_template(
                system_name_or_config=system_name,
                template_variant=variant,
                template_additional_messages=[
                    {"role": "user", "content": user_message}
                ],
            )
    except LookupError as e:
        raise ValueError(str(e)) from e

    usage = result.usage or {}
    return PromptRunOut(
        content=result.content,
        cost=result.cost,
        latency=result.latency,
        input_tokens=usage.get("prompt_tokens"),
        output_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )
