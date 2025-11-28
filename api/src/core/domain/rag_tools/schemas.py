from typing import List, Optional

from pydantic import Field

from core.domain.base import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)
from validation.rag_tools import RagToolsBase


class RagTool(BaseEntitySchema):
    """RAG Tool schema for serialization."""

    variants: Optional[List[RagToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )


class RagToolCreate(BaseEntityCreateSchema):
    """Schema for creating a new RAG tool."""

    variants: Optional[List[RagToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )


class RagToolUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing RAG tool."""

    variants: Optional[List[RagToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )
