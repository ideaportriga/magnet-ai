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

import uuid

import structlog
from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Prefer client-supplied request ID for gateway traceability
        headers = dict(scope.get("headers", []))
        request_id = headers.get(
            REQUEST_ID_HEADER.lower().encode(), b""
        ).decode() or str(uuid.uuid4())

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
