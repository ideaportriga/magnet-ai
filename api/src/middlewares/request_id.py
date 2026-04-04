"""Middleware that assigns a unique request ID to every HTTP request.

The ID is:
- taken from the incoming ``X-Request-ID`` header when present (for
  end-to-end tracing through an API gateway), or generated as a new UUID;
- stored in ``scope["state"]["request_id"]`` so other middleware / handlers
  can access it;
- injected into structlog's context so all log lines emitted during the
  request include the ``request_id`` field;
- returned to the client via the ``X-Request-ID`` response header.
"""

from __future__ import annotations

import re
import uuid

import structlog
from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"

# Only allow safe characters in request IDs to prevent log injection.
# Accepts UUIDs, alphanumeric strings, hyphens, and underscores (max 128 chars).
_SAFE_REQUEST_ID_RE = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")


class RequestIdMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Prefer client-supplied request ID for gateway traceability
        headers = dict(scope.get("headers", []))
        raw_id = headers.get(REQUEST_ID_HEADER.lower().encode(), b"").decode()

        # Validate client-supplied ID to prevent log injection
        if raw_id and _SAFE_REQUEST_ID_RE.match(raw_id):
            request_id = raw_id
        else:
            request_id = str(uuid.uuid4())

        # Make available to handlers via scope["state"]
        state: dict = scope.setdefault("state", {})
        state["request_id"] = request_id

        # Bind to structlog so every log line in this request carries the ID
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers_list: list = list(message.get("headers", []))
                headers_list.append(
                    (REQUEST_ID_HEADER.lower().encode(), request_id.encode())
                )
                message["headers"] = headers_list
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            structlog.contextvars.clear_contextvars()
