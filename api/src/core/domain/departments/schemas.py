"""Pydantic schemas for Department management."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DepartmentMember(BaseModel):
    user_id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    is_lead: bool = False


class DepartmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    slug: str
    name: str
    parent_id: Optional[UUID] = None
    member_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DepartmentDetailResponse(DepartmentResponse):
    members: List[DepartmentMember] = Field(default_factory=list)


class DepartmentCreate(BaseModel):
    slug: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    parent_id: Optional[UUID] = None


class DepartmentUpdate(BaseModel):
    slug: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[UUID] = None


class DepartmentMemberAdd(BaseModel):
    user_id: UUID
    is_lead: bool = False


class DepartmentMemberUpdate(BaseModel):
    is_lead: bool


class UserDepartmentMembership(BaseModel):
    department_id: UUID
    department_slug: str
    department_name: str
    is_lead: bool


class UserDepartmentMembershipInput(BaseModel):
    department_id: UUID
    is_lead: bool = False


class UserDepartmentsPatch(BaseModel):
    """Replace the full set of department memberships for a user."""

    memberships: List[UserDepartmentMembershipInput] = Field(default_factory=list)
