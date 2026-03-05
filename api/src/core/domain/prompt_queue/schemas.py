"""Pydantic schemas for Prompt Queue Config."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


class PromptQueuePromptSchema(BaseModel):
    """A single prompt in a step with its own input and output binding."""

    prompt_template_id: str = Field(
        ...,
        description="Prompt template system name or ID",
    )
    input: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Input variables for the template. Keys are placeholder names (e.g. task, context). "
            "Values can be literals or path references like 'input.task', 'result.data' to bind from run input or previous outputs.",
        ),
    )
    output_key: str | None = Field(
        default=None,
        description="Optional key to store this prompt's output at result.{output_key} for use in later steps (e.g. 'data' -> result.data)",
    )


class PromptQueueStepSchema(BaseModel):
    """A single step in the prompt queue with multiple prompts, each with input/output binding."""

    prompts: list[PromptQueuePromptSchema] = Field(
        default_factory=list,
        description="Prompts in this step, each with template, input vars, and optional output_key for variable binding",
    )


class PromptQueueConfigSchema(BaseSimpleSchema):
    """Prompt Queue Config schema for serialization."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Config with steps, expected_input, and optional api_tool_call per step: { steps: [{ prompts, api_tool_call?: { enabled, api_server, api_tool, body, output_key } }], expected_input?: string[] }",
    )


class PromptQueueConfigCreateSchema(BaseSimpleCreateSchema):
    """Schema for creating a new Prompt Queue Config."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Config with steps, expected_input, and optional api_tool_call per step: { steps: [{ prompts, api_tool_call?: { enabled, api_server, api_tool, body, output_key } }], expected_input?: string[] }",
    )


class PromptQueueConfigUpdateSchema(BaseSimpleUpdateSchema):
    """Schema for updating an existing Prompt Queue Config."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Config with steps, expected_input, and optional api_tool_call per step: { steps: [{ prompts, api_tool_call?: { enabled, api_server, api_tool, body, output_key } }], expected_input?: string[] }",
    )


class PromptQueueExecuteRequestSchema(BaseModel):
    """Request body for executing a prompt queue."""

    input: dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the queue (e.g. {'task': '...', 'query': '...'})",
    )


class PromptQueueExecuteResponseSchema(BaseModel):
    """Response from executing a prompt queue."""

    result: dict[str, Any] = Field(
        default_factory=dict,
        description="Output values keyed by output_key from prompts and api_tool_call",
    )
