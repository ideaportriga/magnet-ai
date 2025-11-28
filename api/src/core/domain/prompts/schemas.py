"""
Pydantic schemas for prompt variants validation.
"""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)


class RetrieveSchema(BaseModel):
    """Schema for retrieve configuration."""

    collection_system_names: List[str] = Field(
        default_factory=list, description="List of collection system names"
    )


class PromptVariantSchema(BaseModel):
    """Schema for validating prompt variant data."""

    model_config = {"populate_by_name": True}
    variant: str = Field(..., description="Name of the variant", alias="variant")
    topP: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Top-p sampling parameter", alias="topP"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Temperature parameter"
    )
    system_name_for_model: Optional[str] = Field(None, description="Model name to use")
    retrieve: Optional[RetrieveSchema] = Field(
        None, description="Retrieve configuration"
    )
    description: Optional[str] = Field(None, description="Description of the variant")
    text: Optional[str] = Field(None, description="Prompt text")
    sample_text: Optional[str] = Field(None, description="Sample text for testing")
    response_format: Optional[dict] = Field(None, description="Response format")
    sample_test_set: Optional[str] = Field(
        None, description="Sample test set for evaluation"
    )


# Pydantic schemas for serialization with variant validation
class Prompt(BaseEntitySchema):
    """Prompt schema for serialization."""

    variants: Optional[List[PromptVariantSchema]] = Field(
        default=None, description="List of prompt variants with model override support"
    )

    @field_validator("variants", mode="before")
    @classmethod
    def parse_variants_if_string(cls, v):
        """Parse variants from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


class PromptCreate(BaseEntityCreateSchema):
    """Schema for creating a new prompt."""

    variants: Optional[List[PromptVariantSchema]] = Field(
        default=None, description="List of prompt variants with model override support"
    )


class PromptUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing prompt."""

    variants: Optional[List[PromptVariantSchema]] = Field(
        default=None, description="List of prompt variants with model override support"
    )
