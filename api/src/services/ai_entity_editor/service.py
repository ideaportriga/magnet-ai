"""Main entry point: ``ai_edit_entity``.

Pipeline (kept linear for readability):

  1. Resolve descriptor by ``entity_type``; load entity from DB; check
     tenant ownership.
  2. Build the read-side snapshot (the same shape the audit listener
     produces — secret fields masked, server-controlled fields stripped).
  3. Build prompt messages + flattened schema.
  4. Call the LLM with ``response_format=json_schema`` when supported,
     else plain JSON mode.
  5. Parse and ``model_validate`` against the editable Pydantic schema.
     On failure, give the LLM **one** retry with the validator's errors.
  6. Strip forbidden paths from the validated dump.
  7. Compute the diff vs the current snapshot (re-using the audit
     ``compute_diff`` so the diff renderer is identical to history).
  8. Persist an ``AIEditRequest`` row for tracking; return the result.

This service does **not** apply the new state to the entity. The caller
(controller) hands the result to the client, which puts it into the
editBuffer and lets the user save via a regular PATCH.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit.snapshot import compute_diff, snapshot_current
from core.audit.mixin import Auditable
from open_ai.utils_new import create_chat_completion

from .models import AIEditFailure, AIEditResult, AIEditStatus, AIEditUsage
from .prompt import build_messages, build_retry_message
from .registry import AIEditableDescriptor, get_ai_editable

logger = logging.getLogger(__name__)


async def _resolve_default_model(session) -> str | None:
    """Pick a model system_name when the caller didn't specify one.

    Strategy (first match wins):
      1. The ``AIModel`` row with ``type='prompts'`` and ``is_default=True``
         (same convention the AI Models admin uses to mark the tenant's
         "preferred" chat model).
      2. Any active ``AIModel`` with ``type='prompts'``.

    Returns ``None`` when no usable model exists — the caller surfaces a
    friendly 422 rather than letting ``create_chat_completion`` raise a
    raw ``ValueError`` deep in the stack.
    """
    # Lazy import to avoid the same circular pull as the rest of this module.
    from core.domain.ai_models.service import AIModelsService

    svc = AIModelsService(session=session)
    candidate = await svc.get_one_or_none(
        type="prompts", is_default=True, is_active=True
    )
    if candidate is None:
        # Fall back to any active prompts model — the user can later mark
        # one as default in /admin/models. Better than a hard 422.
        candidate = await svc.get_one_or_none(type="prompts", is_active=True)
    return candidate.system_name if candidate is not None else None


_JSON_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*(?P<body>.+?)\s*```\s*$", re.DOTALL | re.IGNORECASE
)


def _parse_llm_json(content: str) -> dict[str, Any]:
    """Tolerate code-fenced JSON ('```json ... ```'). Anything that
    doesn't decode cleanly raises ``json.JSONDecodeError`` to the caller.
    """
    text = content.strip()
    match = _JSON_FENCE_RE.match(text)
    if match:
        text = match.group("body")
    return json.loads(text)


def _build_snapshot(entity: Any, descriptor: AIEditableDescriptor) -> dict[str, Any]:
    """Snapshot the entity (using the audit serializer so secrets are masked).

    Then strip forbidden fields so the LLM never sees ``tenant_id``,
    ``owner_id``, internal audit columns, etc.
    """
    if isinstance(entity, Auditable):
        raw = snapshot_current(entity)
    else:
        # The audit snapshot needs the Auditable mixin to honour
        # ``__audit_secret_fields__``. If the registered model isn't
        # auditable for some reason, fall back to a generic column dump.
        from sqlalchemy import inspect as sa_inspect
        from core.audit.snapshot import serialize_value

        mapper = sa_inspect(entity.__class__)
        raw = {
            col.key: serialize_value(getattr(entity, col.key, None))
            for col in mapper.columns
        }

    clean = {k: v for k, v in raw.items() if k not in descriptor.forbidden_fields}
    return _select_editable_state(clean, descriptor)


def _select_editable_state(
    snapshot: dict[str, Any], descriptor: AIEditableDescriptor
) -> dict[str, Any]:
    """Return the exact JSON shape the registered schema edits."""
    if descriptor.variant_shape == "entity":
        return snapshot

    variants = snapshot.get("variants")
    active = snapshot.get("active_variant")
    if not isinstance(variants, list) or not active:
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message="Entity has no active variant to edit",
        )

    for variant in variants:
        if not isinstance(variant, dict) or variant.get("variant") != active:
            continue
        if descriptor.variant_shape == "wrapped":
            value = variant.get("value")
            if not isinstance(value, dict):
                raise AIEditFailure(
                    status=AIEditStatus.LLM_ERROR,
                    message="Active variant has no editable value payload",
                )
            return value
        return variant

    raise AIEditFailure(
        status=AIEditStatus.LLM_ERROR,
        message="Active variant not found",
    )


def _filter_new_state(
    payload: dict[str, Any], descriptor: AIEditableDescriptor
) -> dict[str, Any]:
    """Final safety net: strip forbidden keys at the top level of the result.

    Pydantic validation already enforces the schema (so unknown keys are
    rejected if ``model_config.extra="forbid"``), but we duplicate the
    forbidden-path stripping here — the editable schema might use
    ``extra="allow"`` and we never want to surface secrets back to the
    client side of the call.
    """
    return {k: v for k, v in payload.items() if k not in descriptor.forbidden_fields}


def _summarize_validation_errors(err: ValidationError, *, max_errors: int = 8) -> str:
    """Human-readable summary of the first N pydantic errors, capped to
    keep the retry prompt from ballooning."""
    lines: list[str] = []
    for e in err.errors()[:max_errors]:
        loc = ".".join(str(p) for p in e.get("loc", []))
        msg = e.get("msg", "invalid")
        lines.append(f"- {loc}: {msg}")
    if len(err.errors()) > max_errors:
        lines.append(f"- … and {len(err.errors()) - max_errors} more")
    return "\n".join(lines) or "validation failed"


async def ai_edit_entity(
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    tenant_id: UUID,
    instruction: str,
    model_system_name: str | None,
    on_persist: "Persister | None" = None,
) -> AIEditResult:
    """Run the AI-edit pipeline. Caller commits.

    ``on_persist`` is an optional async hook that receives the resolved
    descriptor + result and is expected to record an ``AIEditRequest``
    row. The hook is decoupled from this module so the LLM service
    itself stays orthogonal to its tracking storage — the controller
    wires it up.
    """
    descriptor = get_ai_editable(entity_type)
    if descriptor is None:
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message=f"Entity type '{entity_type}' is not registered for AI editing",
        )

    if not instruction or not instruction.strip():
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message="Instruction cannot be empty",
        )

    # ── Load entity ─────────────────────────────────────────────────
    entity = await session.get(descriptor.model, entity_id)
    if entity is None:
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message="Entity not found",
        )
    if getattr(entity, "tenant_id", None) and getattr(entity, "tenant_id") != tenant_id:
        # Tenant mismatch — treat as not-found to avoid existence disclosure.
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message="Entity not found",
        )

    snapshot_before = _build_snapshot(entity, descriptor)
    messages, schema = build_messages(
        descriptor=descriptor,
        current_state=snapshot_before,
        instruction=instruction,
    )
    # Build the strict variant once — providers that support
    # ``response_format=json_schema`` (OpenAI, Azure OpenAI) get a
    # guaranteed shape, others fall back to JSON-object mode.
    from .schema_render import to_strict_schema

    strict_schema = to_strict_schema(schema)
    response_format: dict[str, Any] = {
        "type": "json_schema",
        "json_schema": {
            "name": f"{entity_type}_edit",
            "schema": strict_schema,
            "strict": True,
        },
    }

    # Resolve the model lazily if the caller didn't pin one. We can't
    # let ``model_system_name=None`` fall through to ``create_chat_completion``
    # because it requires either a model system_name or an explicit ``llm``.
    if not model_system_name:
        model_system_name = await _resolve_default_model(session)
    if not model_system_name:
        raise AIEditFailure(
            status=AIEditStatus.LLM_ERROR,
            message=(
                "No AI model is available for the AI editor. "
                "Configure a model with type='prompts' (and ideally mark it "
                "as default) in /admin/models, then try again."
            ),
            snapshot_before=snapshot_before,
        )

    # ── LLM call (with one schema-validation retry) ─────────────────
    usage = AIEditUsage(model=model_system_name)
    total_start = time.monotonic()

    new_state: dict[str, Any] | None = None
    last_error_summary: str | None = None

    for attempt in (1, 2):
        try:
            completion = await create_chat_completion(
                model_system_name=model_system_name,
                llm=None,
                messages=messages,
                response_format=response_format,
            )
        except Exception as exc:  # noqa: BLE001
            # Models without structured-output support reject
            # `json_schema`. Retry once with the looser `json_object` so
            # the editor keeps working on local/community models.
            err_text = str(exc).lower()
            if response_format.get("type") == "json_schema" and (
                "json_schema" in err_text
                or "response_format" in err_text
                or "structured" in err_text
            ):
                logger.info(
                    "AI-edit: provider rejected json_schema; falling back to json_object"
                )
                response_format = {"type": "json_object"}
                try:
                    completion = await create_chat_completion(
                        model_system_name=model_system_name,
                        llm=None,
                        messages=messages,
                        response_format=response_format,
                    )
                except Exception as exc2:  # noqa: BLE001
                    logger.error("AI-edit fallback (json_object) also failed: %r", exc2)
                    raise AIEditFailure(
                        status=AIEditStatus.LLM_ERROR,
                        message=f"LLM call failed: {exc2}",
                        usage=usage,
                        snapshot_before=snapshot_before,
                    ) from exc2
            else:
                # Plain `.error()` (not `.exception()`) — structlog's JSON
                # serializer can't encode some objects that end up in
                # ``exc_info`` (e.g. pydantic error metadata classes); we
                # captured the diagnostic in the message string already.
                logger.error("AI-edit LLM call failed: %r", exc)
                raise AIEditFailure(
                    status=AIEditStatus.LLM_ERROR,
                    message=f"LLM call failed: {exc}",
                    usage=usage,
                    snapshot_before=snapshot_before,
                ) from exc

        # Accumulate token usage across attempts so the tracker reflects
        # the full cost of producing the final answer (including retry).
        completion_usage = getattr(completion, "usage", None)
        if completion_usage is not None:
            usage.prompt_tokens += getattr(completion_usage, "prompt_tokens", 0) or 0
            usage.completion_tokens += (
                getattr(completion_usage, "completion_tokens", 0) or 0
            )
            usage.total_tokens += getattr(completion_usage, "total_tokens", 0) or 0

        message = completion.choices[0].message
        raw_content = message.content or ""

        try:
            parsed = _parse_llm_json(raw_content)
        except json.JSONDecodeError as exc:
            last_error_summary = f"response was not valid JSON: {exc.msg}"
            if attempt == 2:
                raise AIEditFailure(
                    status=AIEditStatus.SCHEMA_INVALID,
                    message=f"LLM returned invalid JSON after retry: {exc.msg}",
                    usage=usage,
                    snapshot_before=snapshot_before,
                ) from exc
            # Keep the bad assistant turn so the model can self-correct.
            messages = [*messages, {"role": "assistant", "content": raw_content}]
            messages.append(build_retry_message(last_error_summary))
            continue

        # ── Pydantic schema validation ──────────────────────────────
        try:
            validated = descriptor.editable_schema.model_validate(parsed)
        except ValidationError as exc:
            last_error_summary = _summarize_validation_errors(exc)
            if attempt == 2:
                raise AIEditFailure(
                    status=AIEditStatus.SCHEMA_INVALID,
                    message=f"LLM response failed schema validation: {last_error_summary}",
                    usage=usage,
                    details={"validation_errors": exc.errors()},
                    snapshot_before=snapshot_before,
                ) from exc
            messages = [*messages, {"role": "assistant", "content": raw_content}]
            messages.append(build_retry_message(last_error_summary))
            continue

        new_state = _filter_new_state(
            validated.model_dump(mode="json", by_alias=False),
            descriptor,
        )
        break

    assert new_state is not None  # loop either returns or raises

    usage.latency_ms = int((time.monotonic() - total_start) * 1000)

    diff = compute_diff(snapshot_before, new_state)

    # ── Persist tracking row (delegated) ────────────────────────────
    ai_request_id: UUID | None = None
    if on_persist is not None:
        ai_request_id = await on_persist(
            descriptor=descriptor,
            entity_id=entity_id,
            tenant_id=tenant_id,
            instruction=instruction,
            snapshot_before=snapshot_before,
            snapshot_after=new_state,
            usage=usage,
        )

    return AIEditResult(
        ai_request_id=ai_request_id or UUID(int=0),
        entity_type=entity_type,
        entity_id=entity_id,
        status=AIEditStatus.SUCCEEDED,
        new_state=new_state,
        diff=diff,
        usage=usage,
    )


# Persister protocol; the controller supplies a callable that writes
# ``AIEditRequest`` rows. Kept as a typing-only Protocol to avoid an
# extra import dependency in this module.
from typing import Protocol  # noqa: E402


class Persister(Protocol):
    async def __call__(
        self,
        *,
        descriptor: AIEditableDescriptor,
        entity_id: UUID,
        tenant_id: UUID,
        instruction: str,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
        usage: AIEditUsage,
    ) -> UUID: ...
