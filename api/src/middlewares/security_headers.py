"""Security headers middleware.

Adds standard security headers to all HTTP responses to mitigate
common web vulnerabilities (clickjacking, MIME sniffing, XSS, etc.).
"""

from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class SecurityHeadersMiddleware(AbstractMiddleware):
    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableScopeHeaders.from_message(message)
                for name, value in _SECURITY_HEADERS.items():
                    headers.add(name, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)
