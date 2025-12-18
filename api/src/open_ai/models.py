"""Extended OpenAI models with additional metrics."""

from openai.types.chat import ChatCompletion
from pydantic import Field

from services.observability.models import CostDetails, UsageDetails


class ChatCompletionWithMetrics(ChatCompletion):
    """
    ChatCompletion extended with optional usage and cost metrics.
    """

    usage_details: UsageDetails | None = Field(default=None)
    cost_details: CostDetails | None = Field(default=None)
