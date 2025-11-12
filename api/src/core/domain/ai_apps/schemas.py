"""
Pydantic schemas for AI Apps validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


class TabsSchema(BaseModel):
    """Schema for tabs configuration."""

    name: Optional[str] = Field(None, description="Tab name")
    type: Optional[str] = Field(None, description="Tab type")
    config: Optional[Dict[str, Any]] = Field(None, description="Tab configuration")


class SettingsSchema(BaseModel):
    """Schema for AI app settings."""

    theme: Optional[str] = Field(None, description="App theme")
    layout: Optional[str] = Field(None, description="App layout")
    features: Optional[List[str]] = Field(
        default_factory=list, description="Enabled features"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Additional configuration"
    )


# Pydantic schemas for serialization with AI app specific fields
class AiApp(BaseSimpleSchema):
    """AI App schema for serialization."""

    settings: Optional[Dict[str, Any]] = Field(
        default=None, description="AI app settings"
    )
    tabs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tabs configuration"
    )


class AiAppCreate(BaseSimpleCreateSchema):
    """Schema for creating a new AI app."""

    settings: Optional[Dict[str, Any]] = Field(
        default=None, description="AI app settings"
    )
    tabs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tabs configuration"
    )


class AiAppUpdate(BaseSimpleUpdateSchema):
    """Schema for updating an existing AI app."""

    settings: Optional[Dict[str, Any]] = Field(
        default=None, description="AI app settings"
    )
    tabs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tabs configuration"
    )
