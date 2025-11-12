"""
Pydantic schemas for Evaluations validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Pydantic schemas for serialization with evaluation specific fields
class Evaluation(BaseModel):
    """Evaluation schema for serialization."""

    id: Optional[UUID] = Field(default=None, description="Evaluation ID")
    job_id: Optional[str] = Field(default=None, description="Job identifier")
    type: Optional[str] = Field(default=None, description="Evaluation type")
    test_sets: Optional[List[str]] = Field(
        default=None, description="List of test sets used in evaluation"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Evaluation start time"
    )
    finished_at: Optional[datetime] = Field(
        default=None, description="Evaluation finish time"
    )
    status: Optional[str] = Field(default=None, description="Evaluation status")
    errors: Optional[List[str]] = Field(
        default=None, description="Error details if any"
    )
    tool: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool configuration used"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Evaluation results with latency, score, usage data"
    )


class EvaluationCreate(BaseModel):
    """Schema for creating a new evaluation."""

    job_id: Optional[str] = Field(default=None, description="Job identifier")
    type: Optional[str] = Field(default=None, description="Evaluation type")
    test_sets: Optional[List[str]] = Field(
        default=None, description="List of test sets used in evaluation"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Evaluation start time"
    )
    finished_at: Optional[datetime] = Field(
        default=None, description="Evaluation finish time"
    )
    status: Optional[str] = Field(default=None, description="Evaluation status")
    errors: Optional[List[str]] = Field(
        default=None, description="Error details if any"
    )
    tool: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool configuration used"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Evaluation results with latency, score, usage data"
    )


class EvaluationUpdate(BaseModel):
    """Schema for updating an existing evaluation."""

    job_id: Optional[str] = Field(default=None, description="Job identifier")
    type: Optional[str] = Field(default=None, description="Evaluation type")
    test_sets: Optional[List[str]] = Field(
        default=None, description="List of test sets used in evaluation"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Evaluation start time"
    )
    finished_at: Optional[datetime] = Field(
        default=None, description="Evaluation finish time"
    )
    status: Optional[str] = Field(default=None, description="Evaluation status")
    errors: Optional[List[str]] = Field(
        default=None, description="Error details if any"
    )
    tool: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool configuration used"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Evaluation results with latency, score, usage data"
    )
