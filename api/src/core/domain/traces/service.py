from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service
from advanced_alchemy.filters import FilterTypes
from sqlalchemy import text
from sqlalchemy.orm import defer

from core.db.models.trace import Trace


_MESSAGES_PLACEHOLDER = "<see Messages section above>"


def _build_from_captured_payloads(
    captured_request: Any, captured_response: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    request: dict[str, Any] = (
        dict(captured_request) if isinstance(captured_request, dict) else {}
    )
    request.pop("api_key", None)
    messages_count = request.pop("_messages_count", None)
    if messages_count is not None:
        request["messages"] = f"<{messages_count} messages, see Messages section above>"

    response: dict[str, Any] = (
        dict(captured_response) if isinstance(captured_response, dict) else {}
    )
    raw = response.get("raw")
    if isinstance(raw, dict):
        for choice in raw.get("choices") or []:
            if not isinstance(choice, dict):
                continue
            msg = choice.get("message")
            if not isinstance(msg, dict):
                continue
            if msg.get("content"):
                msg["content"] = _MESSAGES_PLACEHOLDER
            if msg.get("tool_calls"):
                msg["tool_calls"] = _MESSAGES_PLACEHOLDER

    return request, response


def _build_chat_request_response(
    span: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build LLM-style request/response dicts for a chat span, with messages
    redacted (since they are rendered in the dedicated Messages section).

    When the litellm provider has attached the actual request/response payloads
    to the span (under ``extra_data.litellm_request`` / ``litellm_response``),
    those are used directly. Otherwise we fall back to reconstructing from the
    other span fields (for older traces persisted before that capture existed).
    """
    extra_data = span.get("extra_data") or {}
    captured_request = extra_data.get("litellm_request")
    captured_response = extra_data.get("litellm_response")

    if captured_request is not None or captured_response is not None:
        return _build_from_captured_payloads(captured_request, captured_response)

    model = span.get("model") or {}
    params = model.get("parameters") or {}
    input_messages = span.get("input") or []
    output = span.get("output")

    messages_count = len(input_messages) if isinstance(input_messages, list) else 0
    request: dict[str, Any] = {
        "model": params.get("llm"),
        "messages": f"<{messages_count} messages, see Messages section above>",
        "temperature": params.get("temperature"),
        "top_p": params.get("top_p"),
        "max_tokens": params.get("max_tokens"),
        "reasoning_effort": params.get("reasoning_effort"),
        "response_format": params.get("response_format"),
        "tools": extra_data.get("tools"),
    }
    request = {k: v for k, v in request.items() if v is not None}

    if isinstance(output, dict):
        response: dict[str, Any] = {
            "id": output.get("id"),
            "role": output.get("role"),
            "content": _MESSAGES_PLACEHOLDER if output.get("content") else None,
            "tool_calls": _MESSAGES_PLACEHOLDER if output.get("tool_calls") else None,
            "usage": span.get("usage_details"),
            "cost": span.get("cost_details"),
        }
    else:
        response = {
            "content": _MESSAGES_PLACEHOLDER if output else None,
            "usage": span.get("usage_details"),
            "cost": span.get("cost_details"),
        }
    response = {k: v for k, v in response.items() if v is not None}

    return request, response


def _inject_chat_request_response(spans: list[dict[str, Any]] | None) -> None:
    if not spans:
        return
    for span in spans:
        if isinstance(span, dict) and span.get("type") == "chat":
            request, response = _build_chat_request_response(span)
            span["request"] = request
            span["response"] = response


class JsonbPathFilter:
    """Custom filter for JSONB path filtering that works with advanced-alchemy."""

    def __init__(self, json_field: str, json_path: str, values: list[str]):
        self.json_field = json_field
        self.json_path = json_path
        self.values = values

    def append_to_statement(self, statement, model_type: type[Trace]):
        """Append JSONB filter condition to the statement."""
        # Create OR conditions for multiple values using parameterized queries
        condition_strings = []
        params = {}

        for i, value in enumerate(self.values):
            param_name = f"{self.json_path}_value_{i}"
            params[param_name] = value

            if self.json_path == "system_name":
                # For nested path: extra_data->'params'->>'system_name'
                condition_strings.append(
                    f"extra_data->'params'->>'system_name' = :{param_name}"
                )
            else:
                # For direct path: extra_data->>'key'
                condition_strings.append(
                    f"extra_data->>'{self.json_path}' = :{param_name}"
                )

        # Combine with OR if multiple values
        if len(condition_strings) == 1:
            filter_condition = text(condition_strings[0]).params(**params)
        else:
            combined_condition = " OR ".join(condition_strings)
            filter_condition = text(f"({combined_condition})").params(**params)

        return statement.where(filter_condition)


class TracesService(service.SQLAlchemyAsyncRepositoryService[Trace]):
    """Traces service."""

    class Repo(repository.SQLAlchemyAsyncRepository[Trace]):
        """Traces repository."""

        model_type = Trace

    repository_type = Repo

    def to_schema(self, data, *args, **kwargs):  # type: ignore[override]
        result = super().to_schema(data, *args, **kwargs)
        spans = getattr(result, "spans", None)
        if spans is not None:
            _inject_chat_request_response(spans)
        return result

    async def list_and_count_with_jsonb_filters(
        self,
        *filters: FilterTypes,
        jsonb_filters: dict[str, list[str]] | None = None,
    ) -> tuple[list[Trace], int]:
        """
        Enhanced method to handle JSONB field filtering while preserving all
        advanced-alchemy functionality including sorting, pagination, etc.

        Args:
            *filters: Standard advanced_alchemy filters
            jsonb_filters: Dictionary mapping JSON keys to values for filtering

        Returns:
            Tuple of (filtered traces list, total count)
        """
        load_options = [defer(Trace.spans)]

        # If no JSONB filters, use standard method
        if not jsonb_filters:
            results, total = await self.list_and_count(*filters, load=load_options)
            return list(results), total

        # Create JSONB filters using our custom filter class
        additional_filters = []

        for json_key, values in jsonb_filters.items():
            if values:  # Only add filter if values are provided
                jsonb_filter = JsonbPathFilter(
                    json_field="extra_data", json_path=json_key, values=values
                )
                additional_filters.append(jsonb_filter)

        # Combine all filters and use standard list_and_count method
        all_filters = list(filters) + additional_filters
        results, total = await self.list_and_count(*all_filters, load=load_options)

        return list(results), total
