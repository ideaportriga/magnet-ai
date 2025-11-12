from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

from .types import McpServerSessionParams


@asynccontextmanager
async def init_client_session(
    params: McpServerSessionParams,
) -> AsyncGenerator[ClientSession, None]:
    match params.transport:
        case "streamable-http":
            async with streamablehttp_client(
                url=params.url, headers=params.headers
            ) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
        case "sse":
            async with sse_client(
                url=params.url,
                headers=params.headers,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
        case _:
            raise ValueError(f"Unsupported transport type: {params.transport}")
