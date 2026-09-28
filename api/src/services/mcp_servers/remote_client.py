import hashlib
import httpx
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from services.outbound_auth.models import (
    ServerConfig,
)
from services.outbound_auth.service import (
    resolve_request_auth,
    security_config_from_openapi,
    token_cache_cfg_from_openapi,
)

from .types import McpServerSessionParams, McpServerConfigWithSecrets


def _token_cache_key(mcp_server: McpServerConfigWithSecrets) -> str:
    revision = hashlib.sha256(
        json.dumps(
            {
                "security_scheme": mcp_server.security_scheme,
                "security_values": mcp_server.security_values,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()[:12]

    return f"mcp_server:{mcp_server.name}:{revision}"


async def build_mcp_request_headers(
    mcp_server: McpServerConfigWithSecrets,
) -> dict[str, str] | None:
    """Resolve shared outbound authentication for an MCP HTTP transport."""

    token_cache = token_cache_cfg_from_openapi(
        _token_cache_key(mcp_server),
        mcp_server.security_scheme,
    )
    security_config = security_config_from_openapi(
        mcp_server.security_scheme,
        mcp_server.security_values,
        token_cache=token_cache,
    )

    resolved = await resolve_request_auth(
        ServerConfig(security=security_config),
        base_headers=mcp_server.headers,
        secrets=mcp_server.secrets,
    )

    if resolved.query or resolved.cookies:
        raise ValueError("MCP authentication currently supports header placement only")

    return resolved.headers or None


@asynccontextmanager
async def init_client_session(
    params: McpServerSessionParams,
) -> AsyncGenerator[ClientSession, None]:
    try:
        match params.transport:
            case "streamable-http":
                async with streamablehttp_client(
                    url=params.url,
                    headers=params.headers,
                ) as (
                    read_stream,
                    write_stream,
                    _,
                ):
                    async with ClientSession(
                        read_stream,
                        write_stream,
                    ) as session:
                        await session.initialize()
                        yield session

            case "sse":
                async with sse_client(
                    url=params.url,
                    headers=params.headers,
                ) as (read_stream, write_stream):
                    async with ClientSession(
                        read_stream,
                        write_stream,
                    ) as session:
                        await session.initialize()
                        yield session

            case _:
                raise ValueError(f"Unsupported transport type: {params.transport}")

    except (httpx.HTTPStatusError, ExceptionGroup) as exc:
        mcp_error = _mcp_http_error(exc)

        if mcp_error is None:
            raise

        raise mcp_error from None


def _mcp_http_error(
    exception: BaseException,
) -> RuntimeError | None:
    if isinstance(exception, httpx.HTTPStatusError):
        response = exception.response

        return RuntimeError(
            "MCP server request failed with status "
            f"{response.status_code} {response.reason_phrase}"
        )

    if isinstance(exception, ExceptionGroup):
        for nested_exception in exception.exceptions:
            if error := _mcp_http_error(nested_exception):
                return error

    return None
