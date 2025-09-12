from logging import getLogger
from typing import Annotated

from litestar import Controller, post, put
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


class MetricsController(Controller):
    path = "/monitoring"
    tags = ["observability/monitoring"]

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
            logger.error(f"Error in rag_tool_monitoring: {e}")
            return EmptyDictionary()

    @post("/rag/top", status_code=HTTP_200_OK)
    async def rag_tool_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_rag(db_session, data.filters if data else None)
        except Exception as e:
            logger.error(f"Error in rag_tool_top: {e}")
            return []

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
            logger.error(f"Error in rag_tool_list: {e}")
            return MetricsQueryResult(items=[], total=0, limit=0, offset=0)

    @post(
        "/rag/export",
        status_code=HTTP_200_OK,
    )
    async def rag_tool_export(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
        format: str = "csv",
    ) -> File | None:
        try:
            metrics = await get_metrics_by_feature_type(
                db_session, FeatureType.RAG_TOOL, data
            )
            filename = await create_file_with_rag_metrics_for_export(
                metrics["items"],
                format,
            )
            # Optionally use aiofiles for file existence check or manipulation
            return File(path=filename)
        except Exception as e:
            logger.error(f"Error in rag_tool_export: {e}")
            return None

    @post("/rag/options", status_code=HTTP_200_OK)
    async def rag_tool_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsRagResponse:
        try:
            return await get_options_rag(db_session, data.filters if data else None)
        except Exception as e:
            logger.error(f"Error in rag_tool_options: {e}")
            return OptionsRagResponse(
                organizations=[], topics=[], languages=[], consumer_names=[]
            )

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
            logger.error(f"Error in llm_monitoring: {e}")
            return EmptyDictionary()

    @post("/llm/top", status_code=HTTP_200_OK)
    async def llm_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_llm(db_session, data.filters if data else None)
        except Exception as e:
            logger.error(f"Error in llm_top: {e}")
            return []

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
            logger.error(f"Error in llm_list: {e}")
            return MetricsQueryResult(items=[], total=0, limit=0, offset=0)

    @post("/llm/options", status_code=HTTP_200_OK)
    async def llm_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsLlmResponse:
        try:
            return await get_options_llm(db_session, data.filters if data else None)
        except Exception as e:
            logger.error(f"Error in llm_options: {e}")
            return OptionsLlmResponse(organizations=[], consumer_names=[])

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
            logger.error(f"Error in agent_monitoring: {e}")
            return EmptyDictionary()

    @post("/agent/top", status_code=HTTP_200_OK)
    async def agent_top(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> MonitoringTopResponse:
        try:
            return await get_top_metrics_agent(
                db_session, data.filters if data else None
            )
        except Exception as e:
            logger.error(f"Error in agent_top: {e}")
            return []

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
            logger.error(f"Error in agent_list: {e}")
            return MetricsQueryResult(items=[], total=0, limit=0, offset=0)

    @post(
        "/agent/export",
        status_code=HTTP_200_OK,
    )
    async def agent_export(
        self,
        db_session: AsyncSession,
        data: OffsetPaginationRequest | None = None,
        format: str = "csv",
    ) -> File | None:
        try:
            metrics = await get_metrics_by_feature_type(
                db_session, FeatureType.AGENT, data
            )
            filename = await create_file_with_agent_metrics_for_export(
                metrics["items"],
                format,
            )
            return File(path=filename)
        except Exception as e:
            logger.error(f"Error in agent_export: {e}")
            return None

    @post("/agent/options", status_code=HTTP_200_OK)
    async def agent_options(
        self, db_session: AsyncSession, data: MetricsFilteringRequest | None = None
    ) -> OptionsAgentResponse:
        try:
            return await get_options_agent(db_session, data.filters if data else None)
        except Exception as e:
            logger.error(f"Error in agent_options: {e}")
            return OptionsAgentResponse(
                organizations=[], topics=[], tools=[], consumer_names=[], languages=[]
            )

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
