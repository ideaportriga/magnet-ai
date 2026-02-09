"""
Pydantic schemas for API server validation.
"""

from __future__ import annotations

from http import HTTPMethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
    SecretsEncryptedMixin,
)
from services.api_servers.types import SystemName


class ApiToolParameters(BaseModel):
    """API tool parameters schema."""

    input: dict = Field(..., description="Input parameters")
    output: dict = Field(..., description="Output parameters")


class ApiToolMockResponse(BaseModel):
    """API tool mock response schema."""

    content: str = Field(..., description="Mock response content")


class ApiTool(BaseModel):
    """API tool schema."""

    system_name: SystemName = Field(..., description="System name for the tool")
    name: str = Field(..., description="Human-readable name of the tool")
    description: Optional[str] = Field(default=None, description="Tool description")
    path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    parameters: ApiToolParameters = Field(..., description="Input/output parameters")
    original_operation_definition: Dict[str, Any] = Field(
        ..., description="Original OpenAPI operation definition"
    )
    mock_response_enabled: bool = Field(
        default=False, description="Whether mock response is enabled"
    )
    mock_response: Optional[ApiToolMockResponse] = Field(
        default=None, description="Mock response content"
    )


# Pydantic schemas for API server serialization
class ApiServer(BaseSimpleSchema):
    """API server schema for serialization."""

    url: str = Field(..., description="API server URL")
    custom_headers: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom headers configuration"
    )
    security_scheme: Optional[Dict[str, Any]] = Field(
        default=None, description="Security scheme configuration"
    )
    security_values: Optional[Dict[str, Any]] = Field(
        default=None, description="Security values configuration"
    )
    verify_ssl: bool = Field(default=True, description="SSL verification flag")
    tools: Optional[List[ApiTool]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[Dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )


class ApiServerResponse(BaseSimpleSchema, SecretsEncryptedMixin):
    """API server schema for API responses with masked secrets."""

    url: str = Field(..., description="API server URL")
    custom_headers: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom headers configuration"
    )
    security_scheme: Optional[Dict[str, Any]] = Field(
        default=None, description="Security scheme configuration"
    )
    security_values: Optional[Dict[str, Any]] = Field(
        default=None, description="Security values configuration"
    )
    verify_ssl: bool = Field(default=True, description="SSL verification flag")
    tools: Optional[List[ApiTool]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[Dict[str, str]] = Field(
        default=None, description="Encrypted secrets with masked values"
    )


class ApiServerCreate(BaseSimpleCreateSchema):
    """Schema for creating a new API server."""

    url: str = Field(..., description="API server URL")
    custom_headers: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom headers configuration"
    )
    security_scheme: Optional[Dict[str, Any]] = Field(
        default=None, description="Security scheme configuration"
    )
    security_values: Optional[Dict[str, Any]] = Field(
        default=None, description="Security values configuration"
    )
    verify_ssl: bool = Field(default=True, description="SSL verification flag")
    tools: Optional[List[ApiTool]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[Dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )


class ApiServerUpdate(BaseSimpleUpdateSchema):
    """Schema for updating an existing API server."""

    url: Optional[str] = Field(default=None, description="API server URL")
    custom_headers: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom headers configuration"
    )
    security_scheme: Optional[Dict[str, Any]] = Field(
        default=None, description="Security scheme configuration"
    )
    security_values: Optional[Dict[str, Any]] = Field(
        default=None, description="Security values configuration"
    )
    verify_ssl: Optional[bool] = Field(
        default=None, description="SSL verification flag"
    )
    tools: Optional[List[ApiTool]] = Field(
        default=None, description="Tools configuration"
    )
    secrets_encrypted: Optional[Dict[str, Any]] = Field(
        default=None, description="Encrypted secrets"
    )
