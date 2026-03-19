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
import pkgutil
from types import ModuleType
from typing import Any

from .find_documents_by_metadata import build_find_documents_by_metadata_description

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
        # - external: agent cannot provide `details` (only reasoning)
        # - collaborative: agent may provide optional `details` (merged with external input)
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
                properties.pop("details", None)
                required = [r for r in required if r != "details"]
            elif sc == "collaborative":
                # Make details optional for the agent; external input may be enough.
                required = [r for r in required if r != "details"]

            parameters["properties"] = properties
            parameters["required"] = required

            tool_spec["function"]["description"] = (
                build_find_documents_by_metadata_description(
                    description=tool_spec["function"].get("description"),
                    metadata_field_definitions=metadata_field_definitions,
                )
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


_FULL_SEARCH_SPEC: dict[str, Any] = {
    "name": "fullSearch",
    "system_name": "fullSearch",
    "description": (
        "Search the entire knowledge graph using an autonomous ReAct retrieval agent. "
        "The agent autonomously decides which retrieval strategies to use "
        "(chunk similarity, document summary, metadata filtering) to best answer the query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The user query to search for in the knowledge graph.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


def get_agent_tool_specs() -> list[dict[str, Any]]:
    """
    Return tool specs formatted for the agent tool selection UI.

    Each entry contains ``name``, ``system_name``, ``description`` and
    ``parameters`` (with the internal ``reasoning`` field stripped).
    The ``exit`` tool is excluded because it is internal to the ReAct loop.
    ``fullSearch`` is prepended as a synthetic spec representing the full ReAct loop.
    """

    specs: list[dict[str, Any]] = [_FULL_SEARCH_SPEC]
    for module in _iter_tool_modules():
        tool_spec = getattr(module, "TOOL_SPEC", None)
        if not isinstance(tool_spec, dict):
            continue

        fn = tool_spec.get("function")
        if not isinstance(fn, dict):
            continue

        name = (fn.get("name") or "").strip()
        if not name or name == "exit":
            continue

        # Deep-copy parameters and strip "reasoning" (internal to ReAct loop).
        params: dict[str, Any] = copy.deepcopy(fn.get("parameters", {}))
        if "properties" in params:
            params["properties"] = {
                k: v for k, v in params["properties"].items() if k != "reasoning"
            }
        if "required" in params:
            params["required"] = [r for r in params["required"] if r != "reasoning"]

        specs.append(
            {
                "name": name,
                "system_name": name,
                "description": fn.get("description", ""),
                "parameters": params,
            }
        )

    return specs


__all__ = ["get_available_tools", "get_agent_tool_specs"]
