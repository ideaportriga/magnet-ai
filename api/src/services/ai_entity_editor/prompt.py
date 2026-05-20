"""Prompt construction for the AI entity editor.

The contract we ask the LLM to follow:

  System
    * "You're editing a JSON config of type ``{entity_type}``."
    * Human description of the entity (from the registry).
    * JSON Schema with the field-level constraints.
    * Hard rules: return only valid JSON; preserve fields the user didn't
      ask to change; never invent new fields outside the schema.

  User
    * Current state JSON (the read-side view, after stripping forbidden
      fields so the LLM doesn't even see them).
    * The natural-language instruction.

Output: a single JSON object the LLM produces in ``response_format=
json_schema`` mode (when the provider supports it) or as plain JSON
(otherwise).
"""

from __future__ import annotations

import json
from typing import Any

from openai.types.chat import ChatCompletionMessageParam

from .registry import AIEditableDescriptor
from .schema_render import flatten_schema


_SYSTEM_TEMPLATE = """You are an editor for JSON-configured entities of type "{entity_type}".

Entity description:
{entity_description}

You receive (1) the entity's current state as JSON, (2) a JSON Schema describing
the allowed shape, and (3) a natural-language instruction from the user.

Rules:
- Return a SINGLE JSON object that conforms to the schema.
- Preserve every field the user did NOT explicitly ask to change.
- Do NOT invent new fields. Do NOT include fields that are not in the schema.
- Never modify the following keys (they will be stripped anyway): {forbidden_list}.
- Respond with JSON only — no prose, no markdown fences, no comments.

JSON Schema (constraints you must satisfy):
```json
{schema_json}
```"""


_USER_TEMPLATE = """Current state:
```json
{current_state}
```

Instruction: {instruction}"""


def build_messages(
    *,
    descriptor: AIEditableDescriptor,
    current_state: dict[str, Any],
    instruction: str,
) -> tuple[list[ChatCompletionMessageParam], dict[str, Any]]:
    """Return ``(messages, schema)`` ready to pass to the LLM.

    ``schema`` is also returned so the caller can plug it into
    ``response_format`` for providers that support structured output.
    """
    schema = flatten_schema(descriptor.editable_schema)
    forbidden_list = ", ".join(sorted(descriptor.forbidden_fields)) or "(none)"

    system_msg = _SYSTEM_TEMPLATE.format(
        entity_type=descriptor.entity_type,
        entity_description=descriptor.human_description.strip(),
        forbidden_list=forbidden_list,
        schema_json=json.dumps(schema, ensure_ascii=False, indent=2),
    )
    user_msg = _USER_TEMPLATE.format(
        current_state=json.dumps(current_state, ensure_ascii=False, indent=2),
        instruction=instruction.strip(),
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    return messages, schema


def build_retry_message(error_summary: str) -> ChatCompletionMessageParam:
    """A short retry message used after a schema-validation failure.

    The previous assistant turn (the invalid JSON) stays in the
    conversation so the LLM can see what it produced; we only nudge it
    with the validator's complaint.
    """
    return {
        "role": "user",
        "content": (
            "That response did not validate. Errors:\n"
            f"{error_summary.strip()}\n\n"
            "Return a corrected JSON object that satisfies the schema. "
            "Same rules as before: JSON only, preserve untouched fields, "
            "no extra keys."
        ),
    }
