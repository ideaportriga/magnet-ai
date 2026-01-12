import json
from logging import getLogger
from typing import Any

from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams

logger = getLogger(__name__)

ACCOUNT_LOOKUP_TOOL = "accountLookup"


async def account_lookup(account_name: str, *, server: str | None = None) -> Any:
    if not account_name:
        raise ValueError("Account name is required.")
    if not server:
        raise ValueError("Salesforce API server is required.")

    api_call = ApiToolCall(
        server=server,
        tool=ACCOUNT_LOOKUP_TOOL,
        input_params=ApiToolCallInputParams(
            pathParams={
                "accountName": account_name,
                "account_name": account_name,
            },
            queryParams={"accountName": account_name},
        ),
    )
    result = await call_api_server_tool(api_call)

    if result.status_code >= 400:
        raise RuntimeError(
            f"Salesforce account lookup failed (status {result.status_code})."
        )

    try:
        return json.loads(result.content) if result.content else None
    except json.JSONDecodeError:
        logger.debug("Salesforce account lookup response was not JSON.")
        return result.content


async def post_stt_recording(
    payload: dict[str, Any],
    *,
    server: str | None = None,
    tool: str | None = None,
) -> Any:
    if not server:
        raise ValueError("Salesforce API server is required.")
    if not tool:
        raise ValueError("Salesforce STT recording tool is required.")
    api_call = ApiToolCall(
        server=server,
        tool=tool,
        input_params=ApiToolCallInputParams(requestBody=payload),
    )
    result = await call_api_server_tool(api_call)

    if result.status_code >= 400:
        error_body = result.content or ""
        raise RuntimeError(
            "Salesforce sttRecording failed "
            f"(status {result.status_code}): {error_body}"
        )

    try:
        return json.loads(result.content) if result.content else None
    except json.JSONDecodeError:
        logger.debug("Salesforce sttRecording response was not JSON.")
        return result.content


__all__ = ["account_lookup", "post_stt_recording"]
