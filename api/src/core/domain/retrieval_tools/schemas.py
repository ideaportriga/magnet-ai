from typing import List, Optional

from pydantic import Field

from core.domain.base import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)
from validation.retrieval_tools import RetrievalToolsBase  # noqa: F401


class RetrievalTool(BaseEntitySchema):
    """Retrieval Tool schema for serialization."""

    variants: Optional[List[RetrievalToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )


class RetrievalToolCreate(BaseEntityCreateSchema):
    """Schema for creating a new Retrieval tool."""

    variants: Optional[List[RetrievalToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )


class RetrievalToolUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing Retrieval tool."""

    variants: Optional[List[RetrievalToolsBase]] = Field(
        default=None, description="List of prompt variants with model override support"
    )
