from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyConfigBase(BaseModel):
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    value_masked: str
    is_active: bool = True
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    scopes: Optional[list[str]] = None


class ApiKeyConfigEntity(ApiKeyConfigBase):
    id: str


class ApiKeyConfigPersisted(ApiKeyConfigEntity):
    hash: str


class CreateApiKeyData(BaseModel):
    name: str


class CreateApiKeyResult(BaseModel):
    id: str
    api_key: str


class UpdateApiKeyData(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
