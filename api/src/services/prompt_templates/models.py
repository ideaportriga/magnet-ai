from dataclasses import dataclass, field

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class PromptTemplatePreviewRequest(BaseModel):
    system_name_for_prompt_template: str
    name: str
    prompt_template_variant: str | None = None
    messages: list[ChatCompletionMessageParam]
    model: str | None = None
    temperature: float
    top_p: float | None = None  # TODO default?
    max_tokens: int | None = None  # TODO default?
    response_format: dict | None = None
    system_name_for_model: str | None = None


class PromptTemplateExecuteRequest(BaseModel):
    system_name: str
    user_message: str
    system_message_values: dict | None = None


@dataclass
class PromptTemplateExecutionResponse:
    content: str
    usage: dict | None = field(default=None)
    latency: float | None = field(default=None)
    cost: float | None = field(default=None)  # Total cost in USD
    tool_calls: list[dict] | None = field(
        default=None
    )  # Tool calls from chat completion


@dataclass
class PromptTemplateConfig:
    messages: list[ChatCompletionMessageParam] | None = None
    llm_name: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    response_format: dict | None = None
    model: str | None = None
