"""MCP tools: prompt template discovery and inspection.

Three tools with escalating detail:
  1. prompt_templates_list  — lightweight scan (name, system_name, description only)
  2. prompt_template_get    — one template; active variant has full text, others lean
  3. prompt_template_variant_get — full details for one specific variant
"""

from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Optional

from pydantic import BaseModel, Field

from prompt_templates.prompt_templates import get_prompt_template_by_system_name
from core.config.app import alchemy
from core.domain.prompts.service import PromptsService

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class PromptTemplateSummaryOut(BaseModel):
    """Lightweight prompt template entry — for discovery only."""

    name: str
    system_name: str
    description: Optional[str] = None


class PromptTemplateVariantOut(BaseModel):
    """One variant of a prompt template.

    Fields ``text``, ``model``, ``temperature``, ``top_p``, and
    ``observability_level`` are populated only for the active (or requested)
    variant when ``include_all_variants`` is False.
    """

    variant: str = Field(..., description="Variant identifier")
    display_name: Optional[str] = Field(None, description="Human-readable label")
    description: Optional[str] = Field(None, description="What this variant is for")
    text: Optional[str] = Field(None, description="Prompt text (system message)")
    model: Optional[str] = Field(
        None, description="Model system_name override (None = system default)"
    )
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    observability_level: Optional[str] = Field(
        None, description="'none' | 'metadata-only' | 'full'"
    )


class PromptTemplateOut(BaseModel):
    """Full prompt template with variant list."""

    system_name: str
    name: str
    description: Optional[str] = None
    active_variant: Optional[str] = Field(
        None,
        description="Identifier of the variant currently used in production",
    )
    variants: list[PromptTemplateVariantOut] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_variant_out(
    v: dict,
    *,
    include_details: bool,
) -> PromptTemplateVariantOut:
    if include_details:
        return PromptTemplateVariantOut(
            variant=v.get("variant", ""),
            display_name=v.get("display_name"),
            description=v.get("description"),
            text=v.get("text"),
            model=v.get("system_name_for_model"),
            temperature=v.get("temperature"),
            top_p=v.get("topP"),
            observability_level=v.get("observability_level"),
        )
    return PromptTemplateVariantOut(
        variant=v.get("variant", ""),
        display_name=v.get("display_name"),
        description=v.get("description"),
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def prompt_templates_list() -> list[PromptTemplateSummaryOut]:
    """List all prompt templates with name, system_name, and description.

    Returns lightweight entries only — no variant text or model parameters.
    Use this to discover which template to fetch, then call
    ``prompt_template_get`` with the matching system_name.
    """
    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        results, _ = await service.list_and_count()
        return [
            PromptTemplateSummaryOut(
                name=r.name,
                system_name=r.system_name,
                description=r.description,
            )
            for r in results
        ]


async def prompt_template_get(
    system_name: str,
    include_all_variants: bool = False,
) -> PromptTemplateOut:
    """Get a prompt template by its system_name.

    The active variant is returned with its full prompt text and model
    parameters. All other variants include only name and description to keep
    the response lean.

    Set ``include_all_variants=True`` to include full text and parameters for
    every variant — the response may be significantly larger.
    """
    try:
        raw = await get_prompt_template_by_system_name(system_name)
    except LookupError as e:
        raise ValueError(str(e)) from e

    active = raw.get("active_variant")
    variants = [
        _build_variant_out(
            v, include_details=(v.get("variant") == active or include_all_variants)
        )
        for v in (raw.get("variants") or [])
    ]

    return PromptTemplateOut(
        system_name=raw.get("system_name", system_name),
        name=raw.get("name", ""),
        description=raw.get("description"),
        active_variant=active,
        variants=variants,
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


async def prompt_template_variant_get(
    system_name: str,
    variant: str,
) -> PromptTemplateVariantOut:
    """Get full details for one specific variant of a prompt template.

    Returns the variant's prompt text, model system_name, temperature, top_p,
    and observability level. Use this when you already know which variant you
    want, instead of fetching the entire template.

    Raises an error if the variant name does not exist on the template.
    """
    try:
        raw = await get_prompt_template_by_system_name(system_name)
    except LookupError as e:
        raise ValueError(str(e)) from e

    variants = raw.get("variants") or []
    match = next((v for v in variants if v.get("variant") == variant), None)
    if match is None:
        available = [v.get("variant") for v in variants]
        raise ValueError(
            f"Variant {variant!r} not found in template {system_name!r}. "
            f"Available variants: {available}"
        )

    return _build_variant_out(match, include_details=True)
