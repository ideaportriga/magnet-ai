"""Execute a prompt queue config."""

from __future__ import annotations

import json
from typing import Any

from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams
from services.prompt_templates import execute_prompt_template


def _resolve_value(val: Any, input_data: dict[str, Any], result: dict[str, Any]) -> Any:
    """Resolve a value that may be a path like input.task or result.data."""
    if not isinstance(val, str):
        return val
    if val.startswith("input."):
        key = val[6:].strip()
        return input_data.get(key)
    if val.startswith("result."):
        key = val[7:].strip()
        return result.get(key)
    return val


def _resolve_dict(
    obj: dict[str, Any], input_data: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Recursively resolve input.X and result.Y references in a dict."""
    out: dict[str, Any] = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out[k] = _resolve_dict(v, input_data, result)
        elif isinstance(v, list):
            out[k] = [
                _resolve_dict(x, input_data, result)
                if isinstance(x, dict)
                else _resolve_value(x, input_data, result)
                for x in v
            ]
        else:
            out[k] = _resolve_value(v, input_data, result)
    return out


async def execute_prompt_queue(
    config: dict[str, Any],
    input_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a prompt queue config.

    Args:
        config: The queue config (steps with prompts and optional api_tool_call).
        input_data: Input parameters (e.g. {"task": "...", "query": "..."}).

    Returns:
        result dict with output_key -> value for each prompt and api_tool_call.
    """
    result: dict[str, Any] = {}
    steps = config.get("steps") or []

    for step in steps:
        prompts = step.get("prompts") or []
        for prompt in prompts:
            template_id = prompt.get("prompt_template_id")
            if not template_id:
                continue

            prompt_input = prompt.get("input")
            template_values: dict[str, Any] = {}
            if prompt_input and isinstance(prompt_input, dict):
                template_values = _resolve_dict(prompt_input, input_data, result)

            prompt_template_config = await get_prompt_template_by_system_name_flat(
                template_id
            )
            exec_result = await execute_prompt_template(
                system_name_or_config=prompt_template_config,
                template_values=template_values,
            )

            output_key = prompt.get("output_key")
            if isinstance(output_key, str) and output_key.strip():
                result[output_key.strip()] = exec_result.content

        api_tool_call = step.get("api_tool_call")
        if api_tool_call and api_tool_call.get("enabled"):
            api_server = api_tool_call.get("api_server")
            api_tool = api_tool_call.get("api_tool")
            body_str = api_tool_call.get("body") or "{}"
            if not api_server or not api_tool:
                continue

            try:
                body_raw = json.loads(body_str) if body_str.strip() else {}
            except json.JSONDecodeError:
                body_raw = {}

            body_resolved = _resolve_dict(body_raw, input_data, result)

            api_call = ApiToolCall(
                server=api_server,
                tool=api_tool,
                input_params=ApiToolCallInputParams(requestBody=body_resolved),
                variables=input_data,
            )
            api_result = await call_api_server_tool(api_call)

            output_key = api_tool_call.get("output_key")
            if isinstance(output_key, str) and output_key.strip():
                result[output_key.strip()] = api_result.content

    return result
