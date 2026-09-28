"""Flatten a Pydantic JSON Schema for LLM consumption.

``Pydantic.model_json_schema()`` emits a ``$defs`` block with ``$ref``
pointers, which is correct for schema validators but verbose for LLM
prompts (and OpenAI's ``response_format=json_schema`` rejects external
``$ref`` chains in some setups). This module inlines refs and strips
fields that don't carry information for the LLM:

* ``title``  — duplicates field name in 99% of cases.
* ``additionalProperties: false``  — kept (it's a real constraint);
  ``additionalProperties: true``  — dropped (the default).
* ``anyOf: [{type:"X"}, {type:"null"}]``  — collapsed to
  ``{type: ["X", "null"]}``  so the schema reads more like a typed
  contract.

The output is still a valid JSON Schema, just considerably smaller.
"""

from __future__ import annotations

import copy
from typing import Any, Type

from pydantic import BaseModel


def flatten_schema(model: Type[BaseModel]) -> dict[str, Any]:
    """Return a slim, ref-free JSON Schema for ``model``."""
    raw = model.model_json_schema(mode="serialization")
    defs = raw.pop("$defs", {}) or raw.pop("definitions", {}) or {}
    cleaned = _resolve_refs(raw, defs, seen=set())
    return _strip_noise(cleaned)


def to_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert a JSON Schema to the OpenAI ``response_format=json_schema``
    strict-mode contract:

      * Every object explicitly sets ``additionalProperties: false``.
      * Every property is listed in ``required`` (strict mode forbids
        partial keys).
      * Originally-optional properties (those that weren't in the source
        ``required`` set OR had a ``default``) get their type broadened
        to include ``"null"`` so the model can produce them as null
        when the user's instruction doesn't touch them.
      * Originally-required, non-nullable properties keep their type as
        is — the LLM must produce a real value (e.g. a topic must have
        a non-null ``name``).
      * ``default`` values are stripped — strict schemas don't allow
        defaults on required keys.

    Anthropic / Gemini / providers without a strict JSON-schema mode
    fall back to JSON-object mode via the service-side retry; the slim
    schema in the system prompt still guides the model.
    """
    return _strictify(schema, parent_required=True)


def _strictify(node: Any, *, parent_required: bool) -> Any:
    """Recursive strict transform.

    ``parent_required`` is ``True`` when this node sits in its parent's
    ``required`` list — used to decide whether to broaden its type to
    nullable when descending. Defaults to ``True`` at the root.
    """
    if isinstance(node, dict):
        # Object-shaped subschema → enforce strict closure on this level.
        if node.get("type") == "object" and isinstance(node.get("properties"), dict):
            return _strictify_object(node)

        # Array → recurse into ``items``.
        if node.get("type") == "array" and "items" in node:
            result = {k: v for k, v in node.items() if k != "default"}
            # Array items are always "required" (no concept of optional element).
            result["items"] = _strictify(node["items"], parent_required=True)
            return result

        # Generic dict (no special shape) — strip defaults, recurse.
        result = {}
        for key, value in node.items():
            if key == "default":
                continue
            result[key] = _strictify(value, parent_required=True)
        return result

    if isinstance(node, list):
        return [_strictify(item, parent_required=parent_required) for item in node]

    return node


def _strictify_object(obj: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = dict(obj.get("properties") or {})
    originally_required: set[str] = set(obj.get("required") or [])

    new_props: dict[str, Any] = {}
    for name, raw_schema in props.items():
        was_required = name in originally_required
        had_default = isinstance(raw_schema, dict) and "default" in raw_schema
        # Originally-optional ⇒ broaden to nullable so we can still list
        # the key in `required` without forcing the model to invent a
        # value when the user didn't touch it.
        keep_required = was_required and not had_default

        # Recurse first so nested objects/arrays inside the property
        # also get strictified.
        recursed = _strictify(raw_schema, parent_required=keep_required)
        if isinstance(recursed, dict):
            recursed = dict(recursed)
            recursed.pop("default", None)
            if not keep_required:
                recursed = _broaden_to_nullable(recursed)
        new_props[name] = recursed

    out = {
        k: v for k, v in obj.items() if k not in ("properties", "required", "default")
    }
    out["type"] = "object"
    out["properties"] = new_props
    out["required"] = list(new_props.keys())
    out["additionalProperties"] = False
    return out


def _broaden_to_nullable(prop: dict[str, Any]) -> dict[str, Any]:
    """Add ``"null"`` to the type so the LLM can produce ``null`` for
    fields it shouldn't touch."""
    t = prop.get("type")
    if isinstance(t, list):
        if "null" not in t:
            prop["type"] = [*t, "null"]
        return prop
    if isinstance(t, str):
        if t != "null":
            prop["type"] = [t, "null"]
        return prop
    # No declared type (likely enum / anyOf) — leave as is; strict mode
    # accepts these provided the enum/anyOf list itself includes ``null``,
    # which we can't safely synthesize without changing semantics.
    return prop


def _resolve_refs(node: Any, defs: dict[str, Any], *, seen: set[str]) -> Any:
    """Recursively replace ``$ref`` pointers with the referenced subtree."""
    if isinstance(node, dict):
        if "$ref" in node and len(node) == 1:
            ref = node["$ref"]
            # Only handle local refs of the form `#/$defs/Name`.
            if not isinstance(ref, str) or not ref.startswith("#/"):
                return node
            name = ref.rsplit("/", 1)[-1]
            if name in seen:
                # Cycle — return a placeholder so we don't recurse forever.
                # Pydantic models in this codebase don't actually contain
                # cycles, but better to be defensive.
                return {"type": "object", "description": f"recursive ref to {name}"}
            target = defs.get(name)
            if target is None:
                return node
            return _resolve_refs(target, defs, seen=seen | {name})

        return {k: _resolve_refs(v, defs, seen=seen) for k, v in node.items()}

    if isinstance(node, list):
        return [_resolve_refs(item, defs, seen=seen) for item in node]

    return node


_NOISE_KEYS: frozenset[str] = frozenset({"title"})


def _strip_noise(node: Any) -> Any:
    """Drop fields that don't add LLM-relevant information."""
    if isinstance(node, dict):
        # First, normalise ``anyOf: [{...},{"type":"null"}]`` -> nullable.
        node = _collapse_nullable(node)

        result: dict[str, Any] = {}
        for key, value in node.items():
            if key in _NOISE_KEYS:
                continue
            if key == "additionalProperties" and value is True:
                # ``true`` is the implicit default — drop it.
                continue
            result[key] = _strip_noise(value)
        return result

    if isinstance(node, list):
        return [_strip_noise(item) for item in node]

    return node


def _collapse_nullable(node: dict[str, Any]) -> dict[str, Any]:
    """Turn ``{"anyOf": [<X>, {"type":"null"}]}`` into ``X`` with type
    extended to include ``"null"``. Pydantic emits this shape for ``Optional[X]``
    fields; LLMs handle the ``type: [...]`` array more naturally.
    """
    if "anyOf" not in node:
        return node
    branches = node.get("anyOf")
    if not isinstance(branches, list) or len(branches) != 2:
        return node

    null_branch = next(
        (b for b in branches if isinstance(b, dict) and b.get("type") == "null"),
        None,
    )
    non_null = next(
        (b for b in branches if isinstance(b, dict) and b.get("type") != "null"),
        None,
    )
    if null_branch is None or non_null is None:
        return node

    merged = copy.deepcopy(non_null)
    current_type = merged.get("type")
    if isinstance(current_type, list):
        if "null" not in current_type:
            current_type = [*current_type, "null"]
        merged["type"] = current_type
    elif isinstance(current_type, str):
        merged["type"] = [current_type, "null"]
    else:
        # No type at all on the non-null branch — keep anyOf
        return node

    # Carry over any sibling keys present on the original node (e.g. title,
    # default) after the noise stripper takes care of them.
    for key, value in node.items():
        if key == "anyOf":
            continue
        if key not in merged:
            merged[key] = value
    return merged
