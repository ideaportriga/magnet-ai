"""Extract AI model settings from free text via a prompt template (issue #466).

The admin pastes one or more provider docs / pricing pages (plus optional
typed notes); the ``MODEL_CONFIG_EXTRACTION`` prompt template (its model,
temperature and instructions are tenant-editable) reads them and returns, per
requested target model, a card description, capability flags and every pricing
option the pages list — each option tagged with the page it came from, so the
admin can choose between sites. The response format is owned here, not by the
template, so the parser always matches the schema.

Nothing is persisted: the admin UI shows the result, the user picks a pricing
option and saves through the regular create / PATCH endpoints.
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError

from core.domain.ai_models.schemas import _normalize_reasoning_effort_options
from .schema_render import flatten_schema, to_strict_schema

from .schemas import (
    PRICE_FIELDS,
    UNIT_COUNT_FIELDS,
    ExtractedModel,
    ExtractedPricingOption,
    ExtractFromTextRequest,
    ExtractFromTextResponse,
    ExtractionOutput,
    ExtractionSource,
    ExtractionTarget,
)

logger = logging.getLogger(__name__)

MODEL_EXTRACTION_PROMPT_TEMPLATE = "MODEL_CONFIG_EXTRACTION"

_PRICE_SCHEMES = frozenset({"basic", "openai", "anthropic"})
_UNIT_NAMES = frozenset({"tokens", "characters", "queries"})

#: The threshold the drawer's Pricing tab switches long context on with; used
#: when a text gives long-context prices without saying where the tier starts.
DEFAULT_LONG_CONTEXT_THRESHOLD = 200_000

#: Standard price field -> its long-context counterpart.
_LONG_CONTEXT_FIELDS: dict[str, str] = {
    "price_input": "price_long_context_input",
    "price_cached": "price_long_context_cached",
    "price_cache_write": "price_long_context_cache_write",
    "price_cache_write_1h": "price_long_context_cache_write_1h",
    "price_output": "price_long_context_output",
}

#: "> 200K tokens", "Over 128K", "Long context" — a label naming the upper
#: context tier rather than a billing mode.
_LONG_TIER_RE = re.compile(
    r"(?:>|≥|\babove\b|\bover\b|\bmore than\b|\bgreater than\b|\blong[\s-]*context\b)",
    re.IGNORECASE,
)
#: "≤ 200K", "<= 128k", "up to 200K" — the lower tier's qualifier.
_TIER_QUALIFIER_RE = re.compile(
    r"[\s(\[,:–—-]*(?:<=?|≤|>=?|≥|\bup to\b|\bunder\b|\bbelow\b|\babove\b|\bover\b"
    r"|\bmore than\b|\bgreater than\b|\blong[\s-]*context\b|\bshort[\s-]*context\b).*$",
    re.IGNORECASE,
)
_TOKEN_SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*([km])\b", re.IGNORECASE)

_JSON_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*(?P<body>.+?)\s*```\s*$", re.DOTALL | re.IGNORECASE
)


class ModelExtractionError(Exception):
    """A failure the caller can act on; ``status_code`` maps to the HTTP reply."""

    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def build_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "model_config_extraction",
            "schema": to_strict_schema(flatten_schema(ExtractionOutput)),
            "strict": True,
        },
    }


def parse_llm_json(content: str | None) -> dict[str, Any]:
    """Tolerate code-fenced JSON. ``execute_prompt_template`` stringifies a
    ``None`` reply to ``"None"`` — treat that as empty too."""
    text = (content or "").strip()
    if not text or text == "None":
        raise json.JSONDecodeError("empty response", text, 0)
    match = _JSON_FENCE_RE.match(text)
    if match:
        text = match.group("body")
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("expected a JSON object", text, 0)
    return parsed


# ── Normalisation (pure) ────────────────────────────────────────────────


def _clean_price(value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip().replace("$", "").replace(",", "").strip()
    if not raw:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0:
        return None
    # ``normalize`` drops trailing zeros; format "f" avoids ``1E+1``.
    return format(number.normalize(), "f")


def _clean_positive_int(value: int | None) -> int | None:
    return value if isinstance(value, int) and value > 0 else None


def _clean_choice(value: str | None, allowed: frozenset[str]) -> str | None:
    if not value:
        return None
    token = value.strip().lower()
    return token if token in allowed else None


def _clean_source(value: int | None, source_count: int) -> int | None:
    """A 1-based source number, or ``None`` when the LLM gave none or a bad one."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if 1 <= value <= source_count else None


def _clean_pricing_option(
    option: ExtractedPricingOption, index: int, source_count: int
) -> ExtractedPricingOption | None:
    data = option.model_dump()
    data["source"] = _clean_source(data["source"], source_count)
    for field in PRICE_FIELDS:
        data[field] = _clean_price(data[field])
    if not any(data[field] for field in PRICE_FIELDS):
        return None
    for field in (*UNIT_COUNT_FIELDS, "price_long_context_threshold"):
        data[field] = _clean_positive_int(data[field])
    data["price_scheme"] = _clean_choice(data["price_scheme"], _PRICE_SCHEMES)
    data["price_input_unit_name"] = _clean_choice(
        data["price_input_unit_name"], _UNIT_NAMES
    )
    data["price_output_unit_name"] = _clean_choice(
        data["price_output_unit_name"], _UNIT_NAMES
    )
    data["label"] = (data["label"] or "").strip() or f"Option {index + 1}"
    return ExtractedPricingOption(**data)


def _has_long_context_prices(option: ExtractedPricingOption) -> bool:
    return any(getattr(option, field) for field in _LONG_CONTEXT_FIELDS.values())


def _has_standard_prices(option: ExtractedPricingOption) -> bool:
    return any(getattr(option, field) for field in _LONG_CONTEXT_FIELDS)


def _base_label(label: str) -> str:
    return _TIER_QUALIFIER_RE.sub("", label).strip(" -–—:,([") or label


def _threshold_from_label(label: str) -> int | None:
    match = _TOKEN_SIZE_RE.search(label)
    if not match:
        return None
    number = Decimal(match.group(1).replace(",", "."))
    scale = 1_000 if match.group(2).lower() == "k" else 1_000_000
    return int(number * scale)


def _tier_prices(option: ExtractedPricingOption) -> dict[str, str | None] | None:
    """Long-context prices carried by an option that is really just the upper
    context tier of another one; ``None`` when it is a billing mode of its own."""
    if not _has_standard_prices(option) and _has_long_context_prices(option):
        return {
            field: getattr(option, field) for field in _LONG_CONTEXT_FIELDS.values()
        }
    if (
        _LONG_TIER_RE.search(option.label)
        and _has_standard_prices(option)
        and not _has_long_context_prices(option)
    ):
        return {
            long_field: getattr(option, field)
            for field, long_field in _LONG_CONTEXT_FIELDS.items()
        }
    return None


def _merge_long_context_tiers(
    options: list[ExtractedPricingOption],
) -> list[ExtractedPricingOption]:
    """Fold a "> 200K tokens" tier listed as its own option into the option it
    belongs to. Long context is part of one pricing option (the drawer's Long
    context switch), never a separate option to pick."""
    result: list[ExtractedPricingOption] = []
    tiers: list[tuple[ExtractedPricingOption, dict[str, str | None]]] = []
    for option in options:
        prices = _tier_prices(option)
        if prices is None:
            result.append(option)
        else:
            tiers.append((option, prices))

    for tier, prices in tiers:
        # A tier belongs to an option of the same page: two sites pricing the
        # same model are two separate options, never one option's tiers.
        hosts = [
            o
            for o in result
            if not _has_long_context_prices(o) and o.source == tier.source
        ]
        base = _base_label(tier.label).lower()
        host = next((o for o in hosts if _base_label(o.label).lower() == base), None)
        if host is None and len(hosts) == 1:
            host = hosts[0]
        if host is None:
            # Nothing to attach it to — keep it rather than lose the prices.
            result.append(tier)
            continue
        update: dict[str, Any] = {**prices, "label": _base_label(host.label)}
        update["price_long_context_threshold"] = (
            tier.price_long_context_threshold or _threshold_from_label(tier.label)
        )
        result[result.index(host)] = host.model_copy(update=update)
    return result


def _with_long_context_threshold(
    option: ExtractedPricingOption,
) -> ExtractedPricingOption:
    """Long context is on exactly when there are long-context prices."""
    if not _has_long_context_prices(option):
        return option.model_copy(update={"price_long_context_threshold": None})
    if option.price_long_context_threshold:
        return option
    return option.model_copy(
        update={"price_long_context_threshold": DEFAULT_LONG_CONTEXT_THRESHOLD}
    )


def _clean_model(item: ExtractedModel, source_count: int) -> ExtractedModel:
    matched = (item.matched_name or "").strip()
    if not matched:
        # Not found in the text — anything else the LLM said is a guess.
        return ExtractedModel(target_key=item.target_key)

    cleaned = [
        option
        for index, raw in enumerate(item.pricing_options or [])
        if (option := _clean_pricing_option(raw, index, source_count)) is not None
    ]
    options: list[ExtractedPricingOption] = []
    # "Standard" on the Azure page and "Standard" on the OpenAI page are both
    # kept — picking between sources is the point of pasting several.
    seen: set[tuple[int | None, str]] = set()
    for option in _merge_long_context_tiers(cleaned):
        key = (option.source, option.label.lower())
        if key in seen:
            continue
        seen.add(key)
        options.append(_with_long_context_threshold(option))

    try:
        effort_options = _normalize_reasoning_effort_options(
            item.reasoning_effort_options
        )
    except ValueError:
        effort_options = None

    return item.model_copy(
        update={
            "matched_name": matched,
            "description": (item.description or "").strip() or None,
            "reasoning_effort_options": effort_options,
            "vector_size": _clean_positive_int(item.vector_size),
            "pricing_options": options,
        }
    )


def normalize_results(
    targets: list[ExtractionTarget],
    output: ExtractionOutput,
    source_count: int = 1,
) -> list[ExtractedModel]:
    """One cleaned entry per target, in request order.

    Unknown ``target_key``s are dropped, duplicates keep the first entry, and a
    target the LLM skipped comes back as "not found". A pricing option's
    ``source`` outside ``1..source_count`` becomes ``None``.
    """
    known = {target.key for target in targets}
    by_key: dict[str, ExtractedModel] = {}
    for item in output.results:
        if item.target_key not in known or item.target_key in by_key:
            continue
        by_key[item.target_key] = _clean_model(item, source_count)
    return [
        by_key.get(target.key) or ExtractedModel(target_key=target.key)
        for target in targets
    ]


# ── LLM call ────────────────────────────────────────────────────────────


def _source_heading(index: int, source: ExtractionSource) -> str:
    parts = [f"### Source {index}"]
    if source.site:
        parts.append(source.site)
    if source.title:
        parts.append(json.dumps(source.title, ensure_ascii=False))
    return " — ".join(parts)


def build_user_message(
    sources: list[ExtractionSource], notes: list[str] | None = None
) -> str:
    """One user turn with every pasted page, always numbered so each pricing
    option can say which page it came from, then the admin's notes."""
    blocks = [
        f"{_source_heading(index, source)}\n{source.text}"
        for index, source in enumerate(sources, start=1)
    ]
    if notes:
        blocks.append(
            "### Notes from the admin\n" + "\n".join(f"- {note}" for note in notes)
        )
    return "\n\n".join(blocks)


def _retry_message(error_summary: str) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "That response did not validate. Errors:\n"
            f"{error_summary.strip()}\n\n"
            "Return a corrected JSON object that satisfies the schema. JSON only."
        ),
    }


def _summarize_validation_errors(err: ValidationError, *, max_errors: int = 8) -> str:
    lines = [
        f"- {'.'.join(str(p) for p in e.get('loc', []))}: {e.get('msg', 'invalid')}"
        for e in err.errors()[:max_errors]
    ]
    return "\n".join(lines) or "validation failed"


def _is_response_format_rejection(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(key in text for key in ("json_schema", "response_format", "structured"))


async def _load_template_config() -> dict[str, Any]:
    from prompt_templates.prompt_templates import (
        get_prompt_template_by_system_name_flat,
    )

    try:
        config = await get_prompt_template_by_system_name_flat(
            MODEL_EXTRACTION_PROMPT_TEMPLATE
        )
    except LookupError as exc:
        raise ModelExtractionError(
            f"Prompt template '{MODEL_EXTRACTION_PROMPT_TEMPLATE}' not found. "
            "Seed it in Settings → Seed or create a prompt template with this "
            "system name."
        ) from exc
    if not config.get("system_name_for_model"):
        raise ModelExtractionError(
            f"Prompt template '{MODEL_EXTRACTION_PROMPT_TEMPLATE}' has no model. "
            "Pick a model on the prompt template and try again."
        )
    return dict(config)


async def _execute(
    config: dict[str, Any],
    template_values: dict[str, str],
    messages: list[dict[str, str]],
) -> str:
    from services.prompt_templates import execute_prompt_template

    try:
        result = await execute_prompt_template(
            system_name_or_config=config,
            template_values=template_values,
            template_additional_messages=messages,
        )
    except LookupError as exc:
        # The model configured on the template doesn't exist in this tenant.
        raise ModelExtractionError(
            f"Prompt template '{MODEL_EXTRACTION_PROMPT_TEMPLATE}': {exc}"
        ) from exc
    return result.content


async def extract_models_from_text(
    request: ExtractFromTextRequest,
) -> ExtractFromTextResponse:
    config = await _load_template_config()
    config["response_format"] = build_response_format()

    template_values = {
        "provider": request.provider or "unknown",
        "targets": json.dumps(
            [target.model_dump(exclude_none=True) for target in request.targets],
            ensure_ascii=False,
        ),
        "output_schema": json.dumps(flatten_schema(ExtractionOutput)),
    }
    messages: list[dict[str, str]] = [
        {
            "role": "user",
            "content": build_user_message(request.sources, request.notes),
        }
    ]

    for attempt in (1, 2):
        try:
            content = await _execute(config, template_values, messages)
        except ModelExtractionError:
            raise
        except Exception as exc:  # noqa: BLE001
            if config["response_format"].get(
                "type"
            ) == "json_schema" and _is_response_format_rejection(exc):
                logger.info(
                    "Model extraction: provider rejected json_schema; "
                    "falling back to json_object"
                )
                config["response_format"] = {"type": "json_object"}
                try:
                    content = await _execute(config, template_values, messages)
                except ModelExtractionError:
                    raise
                except Exception as exc2:  # noqa: BLE001
                    raise ModelExtractionError(
                        f"LLM call failed: {exc2}", status_code=502
                    ) from exc2
            else:
                raise ModelExtractionError(
                    f"LLM call failed: {exc}", status_code=502
                ) from exc

        try:
            output = ExtractionOutput.model_validate(parse_llm_json(content))
        except json.JSONDecodeError as exc:
            error_summary = f"response was not valid JSON: {exc.msg}"
        except ValidationError as exc:
            error_summary = _summarize_validation_errors(exc)
        else:
            return ExtractFromTextResponse(
                results=normalize_results(request.targets, output, len(request.sources))
            )

        if attempt == 2:
            raise ModelExtractionError(
                f"The model returned an unusable response: {error_summary}",
                status_code=502,
            )
        messages = [
            *messages,
            {"role": "assistant", "content": content or ""},
            _retry_message(error_summary),
        ]

    raise AssertionError("unreachable")  # pragma: no cover
