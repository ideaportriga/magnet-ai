"""
Pydantic schemas for User validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base schema for User with audit fields."""

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(UserBase):
    """User schema for serialization."""

    email: str = Field(..., description="User email address", max_length=320)
    name: Optional[str] = Field(None, description="Display name", max_length=255)
    avatar_url: Optional[str] = Field(None, description="Avatar URL", max_length=2048)
    is_active: bool = Field(True, description="Whether the account is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")
    is_verified: bool = Field(False, description="Whether the email is verified")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")


class UserCreate(BaseModel):
    """Schema for creating a new User."""

    email: str = Field(..., description="User email address", max_length=320)
    name: Optional[str] = Field(None, description="Display name", max_length=255)
    avatar_url: Optional[str] = Field(None, description="Avatar URL", max_length=2048)
    is_active: bool = Field(True, description="Whether the account is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")
    is_verified: bool = Field(False, description="Whether the email is verified")


class UserUpdate(BaseModel):
    """Schema for updating an existing User."""

    name: Optional[str] = Field(None, description="Display name", max_length=255)
    avatar_url: Optional[str] = Field(None, description="Avatar URL", max_length=2048)
    is_active: Optional[bool] = Field(None, description="Whether the account is active")
    is_superuser: Optional[bool] = Field(
        None, description="Whether the user is a superuser"
    )
    is_verified: Optional[bool] = Field(
        None, description="Whether the email is verified"
    )
