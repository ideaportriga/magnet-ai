"""Shared httpx.AsyncClient for outbound HTTP calls.

Reuses TCP connections and TLS sessions across requests,
avoiding the overhead of creating a new client per call.

Usage::

    from utils.http_client import get_http_client

    async def fetch_something():
        client = get_http_client()
        resp = await client.get("https://example.com/api")
        ...

The client is created lazily on first access and closed on app shutdown
via ``close_http_client()``.
"""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return the shared async HTTP client (created lazily)."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=120,
            ),
            follow_redirects=True,
        )
    return _client


async def close_http_client() -> None:
    """Close the shared client (call on app shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
