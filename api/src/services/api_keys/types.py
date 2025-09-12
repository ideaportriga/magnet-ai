from datetime import datetime

from pydantic import BaseModel

class ApiKeyConfigBase(BaseModel):
    name: str
    created_at: datetime
    value_masked: str

class ApiKeyConfigEntity(ApiKeyConfigBase):
    id: str

class ApiKeyConfigPersisted(ApiKeyConfigEntity):
    hash: str


class CreateApiKeyData(BaseModel):
    name: str

class CreateApiKeyResult(BaseModel):
    id: str
    api_key: str
