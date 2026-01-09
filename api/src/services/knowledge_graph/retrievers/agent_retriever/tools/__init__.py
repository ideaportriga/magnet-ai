"""
Tool schemas for the Knowledge Graph agent retriever.

What lives here?
---------------
This package owns the **OpenAI tool schemas** ("function tools") that we show to the
retrieval LLM during the ReAct loop. Each module in this package defines a `TOOL_SPEC`
next to the corresponding implementation function.

What does NOT live here?
------------------------
We intentionally do **not** maintain a global tool registry or a generic dispatcher.
The agent loop (`agent.py`) calls the tool implementations directly.

Public API
----------
- `get_available_tools(...)`: builds the `tools=[...]` list to pass to OpenAI, applying
  graph-specific config such as enabled flags, description overrides, and searchControl.
"""

from __future__ import annotations

import copy
import importlib
import json
import pkgutil
from types import ModuleType
from typing import Any

ToolSpec = dict[str, Any]


def _iter_tool_modules() -> list[ModuleType]:
    """
    Import and return all tool modules in this package.

    We deliberately use discovery so adding a new tool is "drop a new file with
    TOOL_SPEC next to your implementation" and you're done (no central edits needed).
    """

    modules: list[ModuleType] = []
    for mod in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        # Skip nested packages and private helpers.
        if mod.ispkg or mod.name.startswith("_") or mod.name == "__init__":
            continue

        try:
            modules.append(importlib.import_module(f"{__name__}.{mod.name}"))
        except Exception as exc:
            raise RuntimeError(
                f"Failed to import retrieval tool module '{__name__}.{mod.name}': {exc}"
            ) from exc

    return modules


def get_available_tools(
    retrieval_tools_cfg: dict[str, Any],
    *,
    metadata_field_definitions: list[dict[str, Any]] | None = None,
) -> list[ToolSpec]:
    """
    Build the OpenAI `tools=[...]` list for the retrieval agent.

    The graph config controls:
    - which tools are enabled
    - optional per-tool description overrides
    - whether the model is allowed to control knobs like `limit` / `scoreThreshold`
      (searchControl == "agent")

    We deep-copy tool specs before editing them so tool modules keep canonical templates.
    """

    # Discover tool specs from modules on-demand (no global registry).
    tool_templates: dict[str, ToolSpec] = {}
    for module in _iter_tool_modules():
        tool_spec = getattr(module, "TOOL_SPEC", None)
        if not isinstance(tool_spec, dict):
            continue

        fn = tool_spec.get("function")
        if not isinstance(fn, dict):
            continue

        name = fn.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        name = name.strip()
        if name in tool_templates:
            raise RuntimeError(
                f"Duplicate retrieval tool name '{name}' discovered in '{module.__name__}'"
            )

        tool_templates[name] = tool_spec

    available_tools: list[ToolSpec] = []

    # Tool availability is primarily driven by graph config.
    for tool_name, tool_cfg in (retrieval_tools_cfg or {}).items():
        tool_cfg_d = tool_cfg if isinstance(tool_cfg, dict) else {}

        tool_template = tool_templates.get(tool_name)
        if not tool_template:
            continue

        if not tool_cfg_d.get("enabled", True):
            continue

        tool_spec: ToolSpec = copy.deepcopy(tool_template)

        # Allow overriding the description (helpful for customizing the agent's UX per graph).
        if description := tool_cfg_d.get("description"):
            tool_spec["function"]["description"] = description

        # If searchControl is "agent", give the model control over limit / threshold knobs
        # for similarity-based tools. Otherwise those values are taken from graph settings.
        # If searchControl is "agent", allow the model to specify `limit` and `scoreThreshold`.
        # This is handled explicitly per-tool (no grouping of tools).
        if (
            tool_cfg_d.get("searchControl") == "agent"
            and tool_name == "findDocumentsBySummarySimilarity"
        ):
            parameters = tool_spec["function"]["parameters"]
            properties = parameters.get("properties") or {}
            required = parameters.get("required") or []
            if not isinstance(properties, dict):
                properties = {}
            if not isinstance(required, list):
                required = []

            properties["limit"] = {
                "type": "integer",
                "description": "The maximum number of results to return.",
            }
            properties["scoreThreshold"] = {
                "type": "number",
                "description": "The minimum similarity score (0.0 to 1.0) for the results.",
            }

            for r in ("limit", "scoreThreshold"):
                if r not in required:
                    required.append(r)

            parameters["properties"] = properties
            parameters["required"] = required

        if (
            tool_cfg_d.get("searchControl") == "agent"
            and tool_name == "findChunksBySimilarity"
        ):
            parameters = tool_spec["function"]["parameters"]
            properties = parameters.get("properties") or {}
            required = parameters.get("required") or []
            if not isinstance(properties, dict):
                properties = {}
            if not isinstance(required, list):
                required = []

            properties["limit"] = {
                "type": "integer",
                "description": "The maximum number of results to return.",
            }
            properties["scoreThreshold"] = {
                "type": "number",
                "description": "The minimum similarity score (0.0 to 1.0) for the results.",
            }

            for r in ("limit", "scoreThreshold"):
                if r not in required:
                    required.append(r)

            parameters["properties"] = properties
            parameters["required"] = required

        # Metadata filter tool special casing:
        # - external: agent cannot provide `filter` (only reasoning)
        # - collaborative: agent may provide optional `filter` (merged with external input)
        if tool_name == "findDocumentsByMetadata":
            sc = str(tool_cfg_d.get("searchControl") or "").strip().lower()
            parameters = tool_spec["function"]["parameters"]
            properties = parameters.get("properties") or {}
            required = parameters.get("required") or []
            if not isinstance(properties, dict):
                properties = {}
            if not isinstance(required, list):
                required = []

            if sc == "external":
                properties.pop("filter", None)
                required = [r for r in required if r != "filter"]
            elif sc == "collaborative":
                # Make filter optional for the agent; external input may be enough.
                required = [r for r in required if r != "filter"]

            parameters["properties"] = properties
            parameters["required"] = required

            # Append the full schema (field_definitions) so the model knows available fields/values.
            if metadata_field_definitions:
                try:
                    schema_str = json.dumps(
                        metadata_field_definitions,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )
                except Exception:
                    schema_str = str(metadata_field_definitions)

                tool_spec["function"]["description"] = (
                    str(tool_spec["function"].get("description") or "").rstrip()
                    + "\n\n"
                    + "Metadata field schema (graph settings: metadata.field_definitions):\n"
                    + schema_str
                )

        available_tools.append(tool_spec)

    # Defensive fallback: ensure the model can always call `exit`, unless explicitly disabled.
    # The agent loop relies on `exit` being available on the last iteration.
    exit_cfg = (retrieval_tools_cfg or {}).get("exit")
    exit_enabled = True
    if isinstance(exit_cfg, dict):
        exit_enabled = exit_cfg.get("enabled", True)
    if exit_enabled and "exit" in tool_templates:
        if not any(
            t.get("function", {}).get("name") == "exit" for t in available_tools
        ):
            available_tools.append(copy.deepcopy(tool_templates["exit"]))

    return available_tools


__all__ = ["get_available_tools"]
