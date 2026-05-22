"""Pydantic schemas for Tenant management (superuser admin)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    is_active: bool
    user_count: int = 0
    department_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TenantCreate(BaseModel):
    slug: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    is_active: bool = True


class TenantUpdate(BaseModel):
    slug: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
