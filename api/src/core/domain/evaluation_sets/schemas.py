"""
Pydantic schemas for Evaluation Sets validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


# Pydantic schemas for serialization with evaluation set specific fields
class EvaluationSet(BaseSimpleSchema):
    """Evaluation Set schema for serialization."""

    type: Optional[str] = Field(
        default=None, description="Type of evaluation set (e.g., 'rag_tool')"
    )
    items: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of items in the evaluation set"
    )


class EvaluationSetCreate(BaseSimpleCreateSchema):
    """Schema for creating a new evaluation set."""

    type: Optional[str] = Field(
        default=None, description="Type of evaluation set (e.g., 'rag_tool')"
    )
    items: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of items in the evaluation set"
    )


class EvaluationSetUpdate(BaseSimpleUpdateSchema):
    """Schema for updating an existing evaluation set."""

    type: Optional[str] = Field(
        default=None, description="Type of evaluation set (e.g., 'rag_tool')"
    )
    items: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of items in the evaluation set"
    )
