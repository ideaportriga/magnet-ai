"""
Pydantic schemas for MCP server validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_serializer

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


# Pydantic schemas for MCP server serialization
class MCPServer(BaseSimpleSchema):
    """MCP server schema for serialization."""

    transport: str = Field(..., description="Transport protocol (e.g., sse)")
    url: str = Field(..., description="MCP server URL")
    headers: Optional[Dict[str, Any]] = Field(
        default=None, description="HTTP headers configuration"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )


class MCPServerResponse(BaseSimpleSchema):
    """MCP server schema for API responses with masked secrets."""

    transport: str = Field(..., description="Transport protocol (e.g., sse)")
    url: str = Field(..., description="MCP server URL")
    headers: Optional[Dict[str, Any]] = Field(
        default=None, description="HTTP headers configuration"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[Dict[str, str]] = Field(
        default=None, description="Encrypted secrets with masked values"
    )

    @field_serializer("secrets_encrypted", when_used="always")
    def serialize_secrets_encrypted(
        self, value: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, str]]:
        """Serialize secrets to show keys with masked values."""
        if value is None:
            return None
        if isinstance(value, dict):
            return {key: "" for key in value.keys()}
        return None


class MCPServerCreate(BaseSimpleCreateSchema):
    """Schema for creating a new MCP server."""

    transport: str = Field(..., description="Transport protocol (e.g., sse)")
    url: str = Field(..., description="MCP server URL")
    headers: Optional[Dict[str, Any]] = Field(
        default=None, description="HTTP headers configuration"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )


class MCPServerUpdate(BaseSimpleUpdateSchema):
    """Schema for updating an existing MCP server."""

    transport: Optional[str] = Field(
        default=None, description="Transport protocol (e.g., sse)"
    )
    url: Optional[str] = Field(default=None, description="MCP server URL")
    headers: Optional[Dict[str, Any]] = Field(
        default=None, description="HTTP headers configuration"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )
