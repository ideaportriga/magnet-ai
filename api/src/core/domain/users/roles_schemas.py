"""
Pydantic schemas for Role management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    """Role schema for API responses."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoleCreate(BaseModel):
    """Schema for creating a new Role."""

    name: str = Field(..., description="Role display name", max_length=100)
    slug: str = Field(..., description="URL-safe role identifier", max_length=100)
    description: Optional[str] = Field(None, description="Role description")


class RoleUpdate(BaseModel):
    """Schema for updating an existing Role."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class UserRoleAssign(BaseModel):
    """Schema for assigning a role to a user."""

    role_id: UUID = Field(..., description="Role ID to assign")


class GroupResponse(BaseModel):
    """Group schema for API responses."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GroupCreate(BaseModel):
    """Schema for creating a new Group."""

    name: str = Field(..., description="Group name", max_length=255)
    slug: str = Field(..., description="URL-safe group identifier", max_length=255)
    description: Optional[str] = Field(None, description="Group description")


class GroupUpdate(BaseModel):
    """Schema for updating a Group."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class GroupMemberAdd(BaseModel):
    """Schema for adding a user to a group."""

    user_id: UUID = Field(..., description="User ID to add")
    role_in_group: str = Field(
        "member", description="Role in group: 'member' or 'owner'"
    )
