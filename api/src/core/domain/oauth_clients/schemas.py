"""Pydantic schemas for OAuth client CRUD."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import BaseSchema


class OAuthClient(BaseSchema):
    """Full OAuth client schema (used internally — exposes encrypted secret)."""

    client_id: str
    name: str
    is_public: bool = True
    client_secret_encrypted: Optional[str] = None
    redirect_uris: List[str] = Field(default_factory=list)
    enabled: bool = True
    created_via: str = "admin"


class OAuthClientResponse(BaseSchema):
    """API response schema — masks the encrypted client secret.

    `client_secret_encrypted` is replaced with the literal "***" if present so
    the admin UI can show whether one is configured without exposing the value.
    """

    client_id: str
    name: str
    is_public: bool = True
    client_secret_set: bool = False
    redirect_uris: List[str] = Field(default_factory=list)
    enabled: bool = True
    created_via: str = "admin"

    @classmethod
    def from_model(cls, obj) -> "OAuthClientResponse":
        return cls(
            id=obj.id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            client_id=obj.client_id,
            name=obj.name,
            is_public=obj.is_public,
            client_secret_set=bool(obj.client_secret_encrypted),
            redirect_uris=list(obj.redirect_uris or []),
            enabled=obj.enabled,
            created_via=obj.created_via,
        )


class OAuthClientCreate(BaseModel):
    """Body schema for POST /admin/oauth_clients."""

    client_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Identifier the OAuth client sends in /authorize and /token (e.g. 'claude').",
    )
    name: str = Field(
        ..., min_length=1, max_length=255, description="Human-readable display name."
    )
    is_public: bool = Field(
        default=True,
        description="True for public clients (PKCE-only, no secret). Almost always True.",
    )
    client_secret: Optional[str] = Field(
        default=None,
        description="Plaintext secret for confidential clients. Encrypted at rest.",
    )
    redirect_uris: List[str] = Field(
        ...,
        min_length=1,
        description="Whitelist of allowed redirect URIs (exact match; loopback http://127.0.0.1 / http://localhost are wildcarded by port).",
    )
    enabled: bool = True


class OAuthClientUpdate(BaseModel):
    """Body schema for PATCH /admin/oauth_clients/{id}."""

    name: Optional[str] = None
    is_public: Optional[bool] = None
    client_secret: Optional[str] = Field(
        default=None,
        description="If set, replaces the stored secret (re-encrypted). Empty string clears it.",
    )
    redirect_uris: Optional[List[str]] = None
    enabled: Optional[bool] = None
