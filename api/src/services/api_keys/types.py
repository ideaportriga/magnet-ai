from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApiKeyConfigBase(BaseModel):
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    value_masked: str
    expires_at: datetime | None = None
    is_active: bool = True
    notes: str | None = None
    tenant_id: str | UUID
    scopes: list[str] = Field(default_factory=list)


class ApiKeyConfigEntity(ApiKeyConfigBase):
    id: str


class ApiKeyConfigPersisted(ApiKeyConfigEntity):
    hash: str


class CreateApiKeyData(BaseModel):
    name: str
    scopes: list[str] = Field(default_factory=list)


class CreateApiKeyResult(BaseModel):
    id: str
    api_key: str


class UpdateApiKeyData(BaseModel):
    name: str | None = None
    notes: str | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None
    scopes: list[str] | None = None
