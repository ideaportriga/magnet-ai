"""Schemas for extracting AI model settings from free text (issue #466).

``ExtractedModel`` / ``ExtractedPricingOption`` double as the LLM output
contract (rendered into a strict ``response_format`` json_schema) and the API
response. Every value is nullable: the model reports only what the pasted text
actually states, and the admin UI applies non-null values on top of the model.
Field names mirror ``AIModelFieldsMixin`` so the frontend can copy them into a
create/PATCH payload as-is.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

#: Pasted docs pages are long, but not unbounded — every source goes into one
#: prompt, so cap the total well below typical context windows.
MAX_TEXT_LENGTH = 100_000
MAX_SOURCES = 10
MAX_NOTES = 10
MAX_NOTE_LENGTH = 1_000
MAX_TARGETS = 50

PRICE_FIELDS: tuple[str, ...] = (
    "price_input",
    "price_output",
    "price_cached",
    "price_cache_write",
    "price_cache_write_1h",
    "price_long_context_input",
    "price_long_context_cached",
    "price_long_context_cache_write",
    "price_long_context_cache_write_1h",
    "price_long_context_output",
)

UNIT_COUNT_FIELDS: tuple[str, ...] = (
    "price_standard_input_unit_count",
    "price_cached_input_unit_count",
    "price_standard_output_unit_count",
)


class ExtractionTarget(BaseModel):
    """A model the caller wants filled — matched by name against the text."""

    key: str = Field(..., min_length=1, description="Caller-side id of the model")
    ai_model: str = Field(
        ..., min_length=1, description="Provider model id (e.g. gpt-4.1)"
    )
    display_name: Optional[str] = Field(None, description="Human-readable name")
    type: Optional[str] = Field(None, description="Model type (e.g. prompts)")


class ExtractionSource(BaseModel):
    """One pasted page. ``site`` / ``title`` are what the admin UI inferred from
    the clipboard HTML; they help the LLM tell sources apart and label options."""

    text: str = Field(..., description="The page content, as text")
    site: Optional[str] = Field(
        None, max_length=255, description="Site the text was copied from"
    )
    title: Optional[str] = Field(
        None, max_length=300, description="Page or section heading"
    )

    @field_validator("site", "title")
    @classmethod
    def _blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        return (value or "").strip() or None


class ExtractFromTextRequest(BaseModel):
    sources: list[ExtractionSource] = Field(
        ...,
        min_length=1,
        max_length=MAX_SOURCES,
        description=(
            "Pasted pages. A model card and a pricing page are often separate "
            "pages; one page may also hold both, and several sites may price "
            "the same model."
        ),
    )
    notes: list[str] = Field(
        default_factory=list,
        max_length=MAX_NOTES,
        description="Short instructions the admin typed, e.g. 'use EU prices'",
    )
    provider: Optional[str] = Field(
        None, description="Provider name, a hint for matching"
    )
    targets: list[ExtractionTarget] = Field(..., min_length=1, max_length=MAX_TARGETS)

    @field_validator("sources")
    @classmethod
    def _validate_sources(cls, value: list[ExtractionSource]) -> list[ExtractionSource]:
        sources = [
            source.model_copy(update={"text": source.text.strip()})
            for source in value
            if source.text and source.text.strip()
        ]
        if not sources:
            raise ValueError("at least one non-empty source text is required")
        if sum(len(source.text) for source in sources) > MAX_TEXT_LENGTH:
            raise ValueError(
                f"texts are too long (more than {MAX_TEXT_LENGTH} characters in total)"
            )
        return sources

    @field_validator("notes")
    @classmethod
    def _validate_notes(cls, value: list[str]) -> list[str]:
        notes = [note.strip() for note in value if note and note.strip()]
        if any(len(note) > MAX_NOTE_LENGTH for note in notes):
            raise ValueError(f"notes are limited to {MAX_NOTE_LENGTH} characters")
        return notes


class ExtractedPricingOption(BaseModel):
    """One way the provider bills the model (standard, batch, priority, …)."""

    label: str = Field(
        ...,
        description=(
            "Short name of the pricing option as the text calls it, e.g. "
            "'Global Standard', 'Data Zone', 'Batch', 'Priority'. Never a "
            "context-length tier: long-context prices go on the same option"
        ),
    )
    source: Optional[int] = Field(
        None,
        description=(
            "Number N of the '### Source N' the prices were read from. Every "
            "price of an option comes from that one source"
        ),
    )
    price_scheme: Optional[str] = Field(
        None,
        description=(
            "Prompt-cache billing: 'basic' (no cache-write price), 'openai' "
            "(one cache-write price), 'anthropic' (5-minute and 1-hour cache writes)"
        ),
    )
    price_input: Optional[str] = Field(None, description="Price per input unit")
    price_output: Optional[str] = Field(None, description="Price per output unit")
    price_cached: Optional[str] = Field(
        None, description="Price per cached (cache read) input unit"
    )
    price_cache_write: Optional[str] = Field(
        None, description="Price per cache-write input unit (5-minute for anthropic)"
    )
    price_cache_write_1h: Optional[str] = Field(
        None, description="Price per 1-hour cache-write input unit (anthropic only)"
    )
    price_standard_input_unit_count: Optional[int] = Field(
        None, description="Input units the input price is quoted for (e.g. 1000000)"
    )
    price_cached_input_unit_count: Optional[int] = Field(
        None, description="Units the cache prices are quoted for (e.g. 1000000)"
    )
    price_standard_output_unit_count: Optional[int] = Field(
        None, description="Output units the output price is quoted for"
    )
    price_input_unit_name: Optional[str] = Field(
        None, description="'tokens', 'characters' or 'queries'"
    )
    price_output_unit_name: Optional[str] = Field(
        None, description="'tokens', 'characters' or 'queries'"
    )
    # Long context is part of the same option, not an option of its own: a
    # page quoting "<= 200K" and "> 200K" prices describes one billing mode.
    price_long_context_threshold: Optional[int] = Field(
        None,
        description=(
            "Input tokens above which the long-context prices apply (e.g. "
            "200000 for '> 200K tokens'); null when the model has one price tier"
        ),
    )
    price_long_context_input: Optional[str] = Field(
        None, description="Input price above the long-context threshold"
    )
    price_long_context_cached: Optional[str] = Field(
        None, description="Cached input price above the long-context threshold"
    )
    price_long_context_cache_write: Optional[str] = Field(
        None, description="Cache-write price above the long-context threshold"
    )
    price_long_context_cache_write_1h: Optional[str] = Field(
        None, description="1-hour cache-write price above the long-context threshold"
    )
    price_long_context_output: Optional[str] = Field(
        None, description="Output price above the long-context threshold"
    )

    @field_validator(*PRICE_FIELDS, mode="before")
    @classmethod
    def _numbers_to_strings(cls, value: Any) -> Any:
        # JSON-object fallback models often answer prices as numbers.
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        return value


class ExtractedModel(BaseModel):
    """What the text says about one target model."""

    target_key: str = Field(..., description="The `key` of the matched target")
    matched_name: Optional[str] = Field(
        None,
        description="Model name as written in the text; null when not found",
    )
    description: Optional[str] = Field(
        None, description="1-2 sentence card description of the model"
    )
    json_mode: Optional[bool] = Field(None, description="Supports JSON mode")
    json_schema: Optional[bool] = Field(
        None, description="Supports structured outputs / JSON schema"
    )
    tool_calling: Optional[bool] = Field(
        None, description="Supports tool / function calling"
    )
    reasoning: Optional[bool] = Field(None, description="Is a reasoning model")
    reasoning_effort_options: Optional[list[str]] = Field(
        None, description="Supported reasoning-effort values, e.g. low, medium, high"
    )
    supports_temperature: Optional[bool] = Field(
        None, description="Accepts the temperature parameter"
    )
    supports_top_p: Optional[bool] = Field(
        None, description="Accepts the top_p parameter"
    )
    supports_max_tokens: Optional[bool] = Field(
        None, description="Accepts the max_tokens parameter"
    )
    diarization: Optional[bool] = Field(
        None, description="Speech-to-text: supports speaker diarization"
    )
    keyterms: Optional[bool] = Field(
        None, description="Speech-to-text: supports keyterm prompting"
    )
    vector_size: Optional[int] = Field(
        None, description="Embeddings: output vector dimensions"
    )
    pricing_options: list[ExtractedPricingOption] = Field(
        default_factory=list,
        description="Every distinct pricing option the text lists for this model",
    )


class ExtractionOutput(BaseModel):
    """Root object the LLM must return."""

    results: list[ExtractedModel] = Field(default_factory=list)


class ExtractFromTextResponse(BaseModel):
    """One entry per requested target, in request order."""

    results: list[ExtractedModel]
