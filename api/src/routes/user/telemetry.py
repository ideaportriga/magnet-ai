from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel

from api.tags import TagNames
from services.common.models import LlmResponseFeedback
from services.telemetry import (
    record_tool_response_copy,
    record_tool_response_feedback,
)


class TelemetryBaseRequest(BaseModel):
    trace_id: str | None = None
    analytics_id: str | None = None


class ToolResponseFeedbackRequest(TelemetryBaseRequest):
    feedback: LlmResponseFeedback


class ToolResponseCopyRequest(TelemetryBaseRequest):
    pass


class TelemetryController(Controller):
    path = "/telemetry"
    tags = [TagNames.UserTelemetry]

    @post("/tool_response_feedback", status_code=HTTP_200_OK)
    async def tool_response_feedback(self, data: ToolResponseFeedbackRequest) -> None:
        try:
            await record_tool_response_feedback(
                trace_id=data.trace_id,
                analytics_id=data.analytics_id,
                feedback=data.feedback,
            )
        except Exception as e:
            # Handle/log exception as needed
            raise e

    @post("/tool_response_copy", status_code=HTTP_200_OK)
    async def tool_response_copy(self, data: ToolResponseCopyRequest) -> None:
        try:
            await record_tool_response_copy(
                trace_id=data.trace_id,
                analytics_id=data.analytics_id,
            )
        except Exception as e:
            # Handle/log exception as needed
            raise e
