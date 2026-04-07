"""
Core types for the unified auth architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ExternalIdentity:
    """Verified identity from an external source (IdP, local auth, etc.).

    All identity strategies produce this; IdentityResolutionService
    consumes it to find/create the internal User.
    """

    provider: str  # 'local', 'microsoft', 'google', 'github', 'corporate-sso', ...
    subject_id: str  # unique ID from provider (oid, sub, email for local)
    email: str
    name: str | None = None
    email_verified: bool = False
    raw_claims: dict[str, Any] = field(default_factory=dict)
    suggested_roles: list[str] | None = None


@runtime_checkable
class IdentityStrategy(Protocol):
    """Pluggable identity source.

    Each external IdP implements this interface. The auth gateway
    uses it to initiate and complete authentication flows.
    """

    def get_provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'microsoft', 'google')."""
        ...

    async def get_authorization_url(self, state: str, nonce: str) -> str:
        """Return the redirect URL to start authentication at the IdP."""
        ...

    async def handle_callback(
        self, request_data: dict[str, Any], expected_nonce: str | None = None
    ) -> ExternalIdentity:
        """Exchange callback data for a verified external identity."""
        ...
