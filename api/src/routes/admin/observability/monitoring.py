from __future__ import annotations

import os
import uuid
from logging import getLogger
from typing import Annotated

from storage import StorageService

from litestar import Controller, post, put
from litestar.exceptions import InternalServerException
from litestar.params import Parameter
from litestar.response import File
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from services.agents.conversations.services import set_message_custom_feedback
from services.common.models import ConversationMessageFeedback, EmptyDictionary
from services.observability.models import (
    AgentMetricSummary,
    FeatureType,
    LlmMetricsSummary,
    MetricsQueryResult,
    MetricsTopList,
    OptionsAgentResponse,
    OptionsLlmResponse,
    OptionsRagResponse,
    RagMetricsSummary,
)
from services.observability.services import (
    create_file_with_agent_metrics_for_export,
    create_file_with_rag_metrics_for_export,
    get_metrics_by_feature_type,
    get_options_agent,
    get_options_llm,
    get_options_rag,
    get_top_metrics_agent,
    get_top_metrics_llm,
    get_top_metrics_rag,
    summarize_agent_metrics,
    summarize_llm_metrics,
    summarize_rag_tool_metrics,
    update_analytics_extra_data,
    update_metric_conversation_data,
)
from type_defs.pagination import FilterObject, OffsetPaginationRequest

logger = getLogger(__name__)


class MetricsFilteringRequest(BaseModel):
    filters: FilterObject | None = Field(
        default_factory=lambda: FilterObject({}),
        description="Filters for search",
    )


class UpdateMetricRequest(BaseModel):
    language: str | None = None
    is_answered: bool | None = None
    resolution: str | None = None
    topic: str | None = None
    comment: str | None = None
    substandart_result_reason: str | None = None
    conversation_data: dict | None = None


RagMonitoringResponse = RagMetricsSummary | EmptyDictionary
LlimMonitoringResponse = LlmMetricsSummary | EmptyDictionary
AgentMonitoringResponse = AgentMetricSummary | EmptyDictionary

MonitoringTopResponse = list[MetricsTopList]
MonitoringListResponse = MetricsQueryResult


def _raise_internal(handler: str, exc: Exception) -> None:
    """Log with full stacktrace + error_id and raise a 500 (see §C.4).

    Previously these handlers returned an empty dictionary on exception,
    which hid DB failures from monitoring. Now every failure surfaces an
    error_id the client can quote when filing a bug.

    We emit two log lines: `logger.exception` for the full traceback
    (console + standard sinks), and a flat `logger.warning` summary —
    tracebacks produced by structlog's `ProcessorFormatter` are
    sometimes dropped by the Loki batch sender when the rendered
    message contains embedded newlines, so the summary guarantees at
    least the exception type + message + error_id reach Loki.
    """
    error_id = uuid.uuid4().hex
    exc_type = type(exc).__name__
    exc_msg = str(exc)[:400]
    logger.exception("Error in %s (error_id=%s): %s", handler, error_id, exc)
    logger.warning(
        "%s failed (error_id=%s, type=%s): %s",
        handler,
        error_id,
        exc_type,
        exc_msg,
    )
    raise InternalServerException(
        detail=f"{handler} failed: {exc_type}: {exc_msg}",
        extra={"error_id": error_id, "exc_type": exc_type},
    )


class MetricsController(Controller):
    path = "/monitoring"
    tags = ["Admin / Observability"]

    # RAG Dashboard
    @post(
        "/rag",
        status_code=HTTP_200_OK,
    )
    async def rag_tool_monitoring(
        self,
        db_session: AsyncSession,
        data: MetricsFilteringRequest | None = None,
    ) -> RagMonitoringResponse:
        try:
            return await summarize_rag_tool_metrics(
                db_session, data.filters if data else None
            )
        except Exception as e:
            _raise_internal("rag_tool_monitoring", e)

    @post("/rag/top", status_code=HTTP_200_OK)
    async def rag_tool_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_rag(db_session, data.filters if data else None)
        except Exception as e:
            _raise_internal("rag_tool_top", e)

    @post(
        "/rag/list",
        status_code=HTTP_200_OK,
    )
    async def rag_tool_list(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
    ) -> MonitoringListResponse:
        try:
            return await get_metrics_by_feature_type(
                db_session, FeatureType.RAG_TOOL, data
            )
        except Exception as e:
            _raise_internal("rag_tool_list", e)

    @post(
        "/rag/export",
        status_code=HTTP_200_OK,
    )
    async def rag_tool_export(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
        format: str = "csv",
        storage_service: StorageService | None = None,
    ) -> File | None:
        try:
            metrics = await get_metrics_by_feature_type(
                db_session, FeatureType.RAG_TOOL, data
            )
            filename = await create_file_with_rag_metrics_for_export(
                metrics["items"],
                format,
            )

            # Persist export in StorageService (if available)
            await _persist_export(storage_service, db_session, filename, "rag_export")

            return File(path=filename)
        except Exception as e:
            _raise_internal("rag_tool_export", e)

    @post("/rag/options", status_code=HTTP_200_OK)
    async def rag_tool_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsRagResponse:
        try:
            return await get_options_rag(db_session, data.filters if data else None)
        except Exception as e:
            _raise_internal("rag_tool_options", e)

    # LLM Dashboard
    @post("/llm", status_code=HTTP_200_OK)
    async def llm_monitoring(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> LlimMonitoringResponse:
        try:
            return await summarize_llm_metrics(
                db_session, data.filters if data else None
            )
        except Exception as e:
            _raise_internal("llm_monitoring", e)

    @post("/llm/top", status_code=HTTP_200_OK)
    async def llm_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_llm(db_session, data.filters if data else None)
        except Exception as e:
            _raise_internal("llm_top", e)

    @post("/llm/list", status_code=HTTP_200_OK)
    async def llm_list(
        self, db_session: AsyncSession, data: OffsetPaginationRequest | None = None
    ) -> MonitoringListResponse:
        try:
            return await get_metrics_by_feature_type(
                db_session,
                [
                    FeatureType.PROMPT_TEMPLATE,
                    FeatureType.CHAT_COMPLETION,
                    FeatureType.EMBEDDING,
                    FeatureType.RERANKING,
                ],
                data,
            )
        except Exception as e:
            _raise_internal("llm_list", e)

    @post("/llm/options", status_code=HTTP_200_OK)
    async def llm_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsLlmResponse:
        try:
            return await get_options_llm(db_session, data.filters if data else None)
        except Exception as e:
            _raise_internal("llm_options", e)

    # Agent Dashboard
    @post(
        "/agent",
        status_code=HTTP_200_OK,
    )
    async def agent_monitoring(
        self,
        db_session: AsyncSession,
        data: MetricsFilteringRequest | None = None,
    ) -> AgentMonitoringResponse:
        try:
            return await summarize_agent_metrics(
                db_session, data.filters if data else None
            )
        except Exception as e:
            _raise_internal("agent_monitoring", e)

    @post("/agent/top", status_code=HTTP_200_OK)
    async def agent_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_agent(
                db_session, data.filters if data else None
            )
        except Exception as e:
            _raise_internal("agent_top", e)

    @post(
        "/agent/list",
        status_code=HTTP_200_OK,
    )
    async def agent_list(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
    ) -> MonitoringListResponse:
        try:
            return await get_metrics_by_feature_type(
                db_session, FeatureType.AGENT, data if data else None
            )
        except Exception as e:
            _raise_internal("agent_list", e)

    @post(
        "/agent/export",
        status_code=HTTP_200_OK,
    )
    async def agent_export(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
        format: str = "csv",
        storage_service: StorageService | None = None,
    ) -> File | None:
        try:
            metrics = await get_metrics_by_feature_type(
                db_session, FeatureType.AGENT, data
            )
            filename = await create_file_with_agent_metrics_for_export(
                metrics["items"],
                format,
            )

            # Persist export in StorageService (if available)
            await _persist_export(storage_service, db_session, filename, "agent_export")

            return File(path=filename)
        except Exception as e:
            _raise_internal("agent_export", e)

    @post("/agent/options", status_code=HTTP_200_OK)
    async def agent_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsAgentResponse:
        try:
            return await get_options_agent(db_session, data.filters if data else None)
        except Exception as e:
            _raise_internal("agent_options", e)

    @put("/analytics/{analytics_id:str}", status_code=HTTP_200_OK)
    async def update_metric(
        self, db_session: AsyncSession, analytics_id: str, data: UpdateMetricRequest
    ) -> dict:
        success = await update_analytics_extra_data(
            db_session=db_session,
            analytics_id=analytics_id,
            language=data.language,
            is_answered=data.is_answered,
            resolution=data.resolution,
            topic=data.topic,
            comment=data.comment,
            substandart_result_reason=data.substandart_result_reason,
        )

        if data.conversation_data is not None:
            success = await update_metric_conversation_data(
                db_session=db_session,
                analytics_id=analytics_id,
                data=data.conversation_data,
            )

        if not success:
            return {"message": "Failed to update metric."}
        return {"message": "Metric updated successfully."}

    @put(
        "conversation/{conversation_id:str}/messages/{message_id:str}/feedback_custom",
        status_code=HTTP_200_OK,
        summary="Provide custom feedback for a message",
        description="Allows the user to provide custom feedback for a specific message in a conversation.",
    )
    async def message_feedback_custom(
        self,
        conversation_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the conversation containing the message."
            ),
        ],
        message_id: Annotated[
            str,
            Parameter(
                description="The unique identifier of the message for which custom feedback is being provided."
            ),
        ],
        data: ConversationMessageFeedback,
    ) -> None:
        await set_message_custom_feedback(
            conversation_id=conversation_id, message_id=message_id, data=data
        )


async def _persist_export(
    storage_service: StorageService | None,
    db_session: AsyncSession | None,
    filepath: str,
    entity_type: str,
) -> None:
    """Best-effort: persist an export file in StorageService for later retrieval."""
    if not storage_service or not db_session:
        return
    try:
        import mimetypes

        from uuid_utils import uuid7

        import aiofiles

        async with aiofiles.open(filepath, "rb") as f:
            content = await f.read()
        filename = os.path.basename(filepath)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        await storage_service.save_file(
            db_session,
            content=content,
            filename=filename,
            content_type=content_type,
            entity_type="export",
            entity_id=uuid7(),
            sub_path=f"exports/{entity_type}",
        )
    except Exception:
        logger.exception("Failed to persist export file in StorageService")
