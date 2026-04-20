import csv
import json
from collections import defaultdict
from datetime import datetime
from io import StringIO
from logging import getLogger
from typing import Any

import aiofiles
from sqlalchemy import ColumnElement, and_, case, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from core.config.base import get_observability_settings
from core.db.models.metric.metric import Metric
from services.common.models import EmptyDictionary
from services.observability.models import (
    AgentMetricSummary,
    AnswerFeedbackSummary,
    AnswerSummary,
    ChannelSummary,
    FeatureType,
    LanguageSummary,
    LlmMetricsSummary,
    MetricsItem,
    MetricsQueryResult,
    MetricsSummaryBreakdown,
    MetricsTopList,
    OptionsAgentResponse,
    OptionsLlmResponse,
    OptionsRagResponse,
    RagMetricsSummary,
    ResolutionSummary,
    SentimentSummary,
    TopicSummary,
)
from stores import RecordNotFoundError
from type_defs.pagination import FilterObject, OffsetPaginationRequest

logger = getLogger(__name__)

OBSERVABILITY_USAGE_SHOW_USERS = get_observability_settings().USAGE_SHOW_USERS


def _get_field_column(key: str) -> ColumnElement:
    """Get the SQLAlchemy column expression for a given key.

    Handles dotted paths like 'extra_data.topic' -> Metric.extra_data['topic'].as_string()
    """
    if "." in key:
        if key.startswith("extra_data."):
            json_path = key.replace("extra_data.", "", 1)
            return Metric.extra_data[json_path].as_string()
        elif key.startswith("conversation_data."):
            json_path = key.replace("conversation_data.", "", 1)
            return Metric.conversation_data[json_path].as_string()
        elif key.startswith("x_attributes."):
            json_path = key.replace("x_attributes.", "", 1)
            return Metric.x_attributes[json_path].as_string()
    return getattr(Metric, key)


def _build_field_condition(key: str, value: dict) -> list[ColumnElement]:
    """Build ORM conditions for a single field."""
    if not isinstance(value, dict):
        return []

    conditions = []

    for operator, op_value in value.items():
        col = _get_field_column(key)

        if operator == "$in":
            if isinstance(op_value, list):
                conditions.append(col.in_(op_value))
        elif operator == "$nin":
            if isinstance(op_value, list):
                conditions.append(col.notin_(op_value))
        elif operator == "$ne":
            conditions.append(col != op_value)
        elif operator == "$gte":
            conditions.append(col >= op_value)
        elif operator == "$lte":
            conditions.append(col <= op_value)
        elif operator == "$gt":
            conditions.append(col > op_value)
        elif operator == "$lt":
            conditions.append(col < op_value)
        elif operator == "$eq":
            conditions.append(col == op_value)
        elif operator == "$regex":
            # Convert regex pattern to SQL LIKE pattern
            like_pattern = op_value.replace(".*", "%").replace(".", "_")
            pattern = f"%{like_pattern}%"
            conditions.append(func.lower(col).like(func.lower(pattern)))
        elif operator == "$exists":
            if op_value:
                conditions.append(col.is_not(None))
            else:
                conditions.append(col.is_(None))

    return conditions


def _build_conditions(filter_dict: dict) -> list[ColumnElement]:
    """Recursively build ORM conditions from filter dictionary."""
    conditions = []

    for key, value in filter_dict.items():
        if key == "$and":
            and_conditions = []
            for and_filter in value:
                sub = _build_conditions(and_filter)
                if sub:
                    and_conditions.append(and_(*sub))
            if and_conditions:
                conditions.append(and_(*and_conditions))
        elif key == "$or":
            or_conditions = []
            for or_filter in value:
                sub = _build_conditions(or_filter)
                if sub:
                    or_conditions.append(and_(*sub))
            if or_conditions:
                conditions.append(or_(*or_conditions))
        else:
            field_conditions = _build_field_condition(key, value)
            conditions.extend(field_conditions)

    return conditions


def _build_where_conditions(filters: FilterObject | None) -> list[ColumnElement]:
    """Build a list of SQLAlchemy WHERE conditions from filters."""
    if not filters:
        return []

    filter_dict = filters.model_dump(exclude_none=True, by_alias=True)
    return _build_conditions(filter_dict)


async def get_options_rag(
    db_session: AsyncSession, filters: FilterObject | None
) -> OptionsRagResponse:
    """Get RAG tool options"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "rag-tool",
        Metric.status == "success",
    ]
    all_conditions = base_conditions + extra_conditions

    # Get topics
    stmt = (
        select(distinct(Metric.extra_data["topic"].as_string()).label("topic"))
        .where(*all_conditions)
        .where(Metric.extra_data["topic"].as_string().is_not(None))
        .order_by(Metric.extra_data["topic"].as_string())
    )
    topics_result = await db_session.execute(stmt)
    topics = [row.topic for row in topics_result.fetchall() if row.topic]

    # Get languages
    stmt = (
        select(distinct(Metric.extra_data["language"].as_string()).label("language"))
        .where(*all_conditions)
        .where(Metric.extra_data["language"].as_string().is_not(None))
        .order_by(Metric.extra_data["language"].as_string())
    )
    languages_result = await db_session.execute(stmt)
    languages = [row.language for row in languages_result.fetchall() if row.language]

    # Get consumer names
    stmt = (
        select(distinct(Metric.consumer_name))
        .where(*all_conditions)
        .where(Metric.consumer_name.is_not(None))
        .order_by(Metric.consumer_name)
    )
    consumer_names_result = await db_session.execute(stmt)
    consumer_names = [row[0] for row in consumer_names_result.fetchall() if row[0]]

    # Get organizations
    stmt = (
        select(distinct(Metric.x_attributes["org-id"].as_string()).label("org_id"))
        .where(*all_conditions)
        .where(Metric.x_attributes["org-id"].as_string().is_not(None))
        .order_by(Metric.x_attributes["org-id"].as_string())
    )
    organizations_result = await db_session.execute(stmt)
    organizations = [
        row.org_id for row in organizations_result.fetchall() if row.org_id
    ]

    return OptionsRagResponse(
        topics=topics,
        languages=languages,
        consumer_names=consumer_names,
        organizations=organizations,
    )


async def get_options_llm(
    db_session: AsyncSession, filters: FilterObject | None
) -> OptionsLlmResponse:
    """Get LLM options"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type.in_(
            ["prompt-template", "chat-completion-api", "embedding-api", "reranking-api"]
        ),
    ]
    all_conditions = base_conditions + extra_conditions

    # Get consumer names
    stmt = (
        select(distinct(Metric.consumer_name))
        .where(*all_conditions)
        .where(Metric.consumer_name.is_not(None))
        .order_by(Metric.consumer_name)
    )
    consumer_names_result = await db_session.execute(stmt)
    consumer_names = [row[0] for row in consumer_names_result.fetchall() if row[0]]

    # Get organizations
    stmt = (
        select(distinct(Metric.x_attributes["org-id"].as_string()).label("org_id"))
        .where(*all_conditions)
        .where(Metric.x_attributes["org-id"].as_string().is_not(None))
        .order_by(Metric.x_attributes["org-id"].as_string())
    )
    organizations_result = await db_session.execute(stmt)
    organizations = [
        row.org_id for row in organizations_result.fetchall() if row.org_id
    ]

    return OptionsLlmResponse(
        consumer_names=consumer_names, organizations=organizations
    )


async def get_options_agent(
    db_session: AsyncSession, filters: FilterObject | None
) -> OptionsAgentResponse:
    """Get Agent options"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "agent",
        Metric.status == "success",
    ]
    all_conditions = base_conditions + extra_conditions

    # Get topics from conversation_data.topics array (application-level)
    stmt = (
        select(Metric.conversation_data["topics"])
        .where(*all_conditions)
        .where(Metric.conversation_data["topics"].is_not(None))
    )
    topics_result = await db_session.execute(stmt)
    topics = set()
    for (topics_json,) in topics_result:
        if isinstance(topics_json, list):
            topics.update(t for t in topics_json if t)
    topics = sorted(topics)

    # Get feature system names as tools
    stmt = (
        select(distinct(Metric.feature_system_name))
        .where(*all_conditions)
        .where(Metric.feature_system_name.is_not(None))
        .order_by(Metric.feature_system_name)
    )
    tools_result = await db_session.execute(stmt)
    tools = [row[0] for row in tools_result.fetchall() if row[0]]

    # Get consumer names
    stmt = (
        select(distinct(Metric.consumer_name))
        .where(*all_conditions)
        .where(Metric.consumer_name.is_not(None))
        .order_by(Metric.consumer_name)
    )
    consumer_names_result = await db_session.execute(stmt)
    consumer_names = [row[0] for row in consumer_names_result.fetchall() if row[0]]

    # Get languages
    stmt = (
        select(
            distinct(Metric.conversation_data["language"].as_string()).label("language")
        )
        .where(*all_conditions)
        .where(Metric.conversation_data["language"].as_string().is_not(None))
        .order_by(Metric.conversation_data["language"].as_string())
    )
    languages_result = await db_session.execute(stmt)
    languages = [row.language for row in languages_result.fetchall() if row.language]

    # Get organizations
    stmt = (
        select(distinct(Metric.x_attributes["org-id"].as_string()).label("org_id"))
        .where(*all_conditions)
        .where(Metric.x_attributes["org-id"].as_string().is_not(None))
        .order_by(Metric.x_attributes["org-id"].as_string())
    )
    organizations_result = await db_session.execute(stmt)
    organizations = [
        row.org_id for row in organizations_result.fetchall() if row.org_id
    ]

    return OptionsAgentResponse(
        topics=topics,
        tools=tools,
        consumer_names=consumer_names,
        languages=languages,
        organizations=organizations,
    )


async def summarize_rag_tool_metrics(
    db_session: AsyncSession,
    filters: FilterObject | None,
) -> RagMetricsSummary | EmptyDictionary:
    """Summarize RAG tool metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "rag-tool",
        Metric.status == "success",
        Metric.channel == "production",
    ]
    all_conditions = base_conditions + extra_conditions

    # Get general metrics
    stmt = select(
        func.count().label("total_calls"),
        func.avg(Metric.latency).label("avg_latency"),
        func.avg(Metric.cost).label("avg_cost"),
        func.sum(Metric.cost).label("total_cost"),
        func.count(distinct(Metric.user_id)).label("unique_user_count"),
    ).where(*all_conditions)

    general_result = await db_session.execute(stmt)
    general_metrics = general_result.first()

    if not general_metrics or general_metrics.total_calls == 0:
        return EmptyDictionary()

    # Get resolution metrics
    is_answered_col = Metric.extra_data["is_answered"].as_string()
    stmt = (
        select(
            is_answered_col.label("resolution"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(is_answered_col)
    )
    resolution_result = await db_session.execute(stmt)
    resolution_metrics = [
        {"_id": row.resolution, "count": row.count}
        for row in resolution_result.fetchall()
    ]

    # Get topic metrics
    topic_col = Metric.extra_data["topic"].as_string()
    stmt = (
        select(
            topic_col.label("topic"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(topic_col)
    )
    topic_result = await db_session.execute(stmt)
    topic_metrics = [
        {"_id": row.topic, "count": row.count} for row in topic_result.fetchall()
    ]

    # Get feedback metrics
    feedback_type_col = Metric.extra_data["answer_feedback"]["type"].as_string()
    stmt = (
        select(
            feedback_type_col.label("feedback_type"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .where(feedback_type_col.is_not(None))
        .group_by(feedback_type_col)
    )
    feedback_result = await db_session.execute(stmt)
    feedback_metrics = [
        {"_id": row.feedback_type, "count": row.count}
        for row in feedback_result.fetchall()
    ]

    # Get copy metrics
    stmt = (
        select(func.count().label("copy_count"))
        .where(*all_conditions)
        .where(Metric.extra_data["answer_copy"].as_boolean() == True)  # noqa: E712
    )
    copy_result = await db_session.execute(stmt)
    copy_count = copy_result.scalar() or 0

    # Get language metrics
    language_col = Metric.extra_data["language"].as_string()
    stmt = (
        select(
            language_col.label("language"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(language_col)
    )
    language_result = await db_session.execute(stmt)
    language_metrics = [
        {"_id": row.language, "count": row.count} for row in language_result.fetchall()
    ]

    return RagMetricsSummary(
        total_calls=general_metrics.total_calls,
        avg_latency=general_metrics.avg_latency or 0.0,
        avg_cost=general_metrics.avg_cost or 0.0,
        total_cost=general_metrics.total_cost or 0.0,
        unique_user_count=general_metrics.unique_user_count or 0,
        resolution_summary=ResolutionSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in resolution_metrics
            ],
        ),
        topic_summary=TopicSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in topic_metrics
            ],
        ),
        answer_summary=AnswerSummary(
            feedback=AnswerFeedbackSummary(
                breakdown=[
                    MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                    for item in feedback_metrics
                ],
            ),
            copy_rate=(copy_count / general_metrics.total_calls) * 100
            if general_metrics.total_calls > 0
            else 0,
        ),
        language_summary=LanguageSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in language_metrics
            ],
        ),
    )


async def summarize_llm_metrics(
    db_session: AsyncSession,
    filters: FilterObject | None,
) -> LlmMetricsSummary | EmptyDictionary:
    """Summarize LLM metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type.in_(
            ["prompt-template", "chat-completion-api", "embedding-api", "reranking-api"]
        ),
    ]
    all_conditions = base_conditions + extra_conditions

    # Get general metrics
    stmt = select(
        func.count().label("count"),
        func.avg(Metric.latency).label("avg_latency"),
        func.avg(Metric.cost).label("avg_total_cost"),
        func.sum(Metric.cost).label("total_cost"),
        func.count(distinct(Metric.user_id)).label("unique_user_count"),
        func.sum(case((Metric.status == "error", 1), else_=0)).label("error_count"),
    ).where(*all_conditions)

    general_result = await db_session.execute(stmt)
    general_metrics = general_result.first()

    if not general_metrics or general_metrics.count == 0:
        return EmptyDictionary()

    error_rate = (
        (general_metrics.error_count / general_metrics.count) * 100
        if general_metrics.count > 0
        else 0
    )

    return LlmMetricsSummary(
        total_calls=general_metrics.count,
        avg_latency=general_metrics.avg_latency or 0.0,
        avg_cost=general_metrics.avg_total_cost or 0.0,
        total_cost=general_metrics.total_cost or 0.0,
        unique_user_count=general_metrics.unique_user_count or 0,
        error_rate=error_rate,
    )


async def summarize_agent_metrics(
    db_session: AsyncSession,
    filters: FilterObject | None,
) -> AgentMetricSummary | EmptyDictionary:
    """Summarize Agent metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "agent",
        Metric.status == "success",
    ]
    all_conditions = base_conditions + extra_conditions

    # Get general metrics
    stmt = select(
        func.count().label("count"),
        func.avg(Metric.latency).label("avg_duration"),
        func.avg(Metric.cost).label("avg_cost"),
        func.sum(Metric.cost).label("total_cost"),
        func.count(distinct(Metric.user_id)).label("unique_user_count"),
        func.count(distinct(Metric.conversation_id)).label("conversation_count"),
        func.avg(Metric.conversation_data["avg_tool_call_latency"].as_float()).label(
            "avg_tool_call_latency"
        ),
        func.sum(Metric.conversation_data["likes"].as_integer()).label("total_likes"),
        func.sum(Metric.conversation_data["dislikes"].as_integer()).label(
            "total_dislikes"
        ),
        func.avg(Metric.conversation_data["messages_count"].as_float()).label(
            "avg_messages_count"
        ),
        func.sum(
            case(
                (
                    Metric.conversation_data["resolution_status"].as_string()
                    == "resolved",
                    1,
                ),
                else_=0,
            )
        ).label("total_status_resolved"),
        func.sum(
            case(
                (Metric.extra_data["answer_copy"].as_boolean() == True, 1),  # noqa: E712
                else_=0,
            )
        ).label("copy_count"),
        func.sum(
            case(
                (
                    (
                        func.coalesce(Metric.conversation_data["likes"].as_integer(), 0)
                        + func.coalesce(
                            Metric.conversation_data["dislikes"].as_integer(), 0
                        )
                    )
                    > 0,
                    1,
                ),
                else_=0,
            )
        ).label("feedback_count"),
    ).where(*all_conditions)

    general_result = await db_session.execute(stmt)
    general_metrics = general_result.first()

    if not general_metrics or general_metrics.count == 0:
        return EmptyDictionary()

    feedback_rate = (
        (general_metrics.feedback_count / general_metrics.count)
        if general_metrics.count > 0
        else 0
    )
    copy_rate = (
        (general_metrics.copy_count / general_metrics.count)
        if general_metrics.count > 0
        else 0
    )

    # Get resolution metrics
    resolution_col = Metric.conversation_data["resolution_status"].as_string()
    stmt = (
        select(
            resolution_col.label("resolution_status"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(resolution_col)
    )
    resolution_result = await db_session.execute(stmt)
    resolution_metrics = [
        {"_id": row.resolution_status, "count": row.count}
        for row in resolution_result.fetchall()
    ]

    # Get channel metrics
    stmt = (
        select(
            Metric.channel,
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(Metric.channel)
    )
    channel_result = await db_session.execute(stmt)
    channel_metrics = [
        {"_id": row.channel, "count": row.count} for row in channel_result.fetchall()
    ]

    # Get sentiment metrics
    sentiment_col = Metric.conversation_data["sentiment"].as_string()
    stmt = (
        select(
            sentiment_col.label("sentiment"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(sentiment_col)
    )
    sentiment_result = await db_session.execute(stmt)
    sentiment_metrics = [
        {"_id": row.sentiment, "count": row.count}
        for row in sentiment_result.fetchall()
    ]

    # Get topics metrics (application-level, replaces jsonb_array_elements_text)
    stmt = (
        select(Metric.conversation_data["topics"])
        .where(*all_conditions)
        .where(Metric.conversation_data["topics"].is_not(None))
    )
    topics_result = await db_session.execute(stmt)
    topic_counts = defaultdict(int)
    for (topics_json,) in topics_result:
        if isinstance(topics_json, list):
            for t in topics_json:
                if t:
                    topic_counts[t] += 1
    topics_metrics = [
        {"_id": topic, "count": count} for topic, count in topic_counts.items()
    ]

    # Get language metrics
    language_col = Metric.conversation_data["language"].as_string()
    stmt = (
        select(
            language_col.label("language"),
            func.count().label("count"),
        )
        .where(*all_conditions)
        .group_by(language_col)
    )
    language_result = await db_session.execute(stmt)
    language_metrics = [
        {"_id": row.language, "count": row.count} for row in language_result.fetchall()
    ]

    # Get feedback metrics (likes/dislikes)
    feedback_metrics = [
        {"_id": "likes", "count": general_metrics.total_likes or 0},
        {"_id": "dislikes", "count": general_metrics.total_dislikes or 0},
    ]

    return AgentMetricSummary(
        total_conversations=general_metrics.count,
        avg_duration=float(general_metrics.avg_duration or 0.0),
        avg_tool_call_latency=float(general_metrics.avg_tool_call_latency or 0.0),
        avg_cost=float(general_metrics.avg_cost or 0.0),
        total_cost=float(general_metrics.total_cost or 0.0),
        unique_user_count=int(general_metrics.unique_user_count or 0),
        feedback_rate=float(feedback_rate),
        copy_rate=float(copy_rate),
        avg_messages_count=float(general_metrics.avg_messages_count or 0.0),
        resolution_summary=ResolutionSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in resolution_metrics
            ],
        ),
        channel_summary=ChannelSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in channel_metrics
            ],
        ),
        sentiment_summary=SentimentSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in sentiment_metrics
            ],
        ),
        topics_summary=TopicSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in topics_metrics
            ],
        ),
        feedback_summary=AnswerFeedbackSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in feedback_metrics
            ],
        ),
        language_summary=LanguageSummary(
            breakdown=[
                MetricsSummaryBreakdown(name=item["_id"], count=item["count"])
                for item in language_metrics
            ],
        ),
    )


async def get_top_metrics_llm(
    db_session: AsyncSession, filters: FilterObject | None
) -> list[MetricsTopList]:
    """Get top LLM metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type.in_(
            ["prompt-template", "chat-completion-api", "embedding-api", "reranking-api"]
        ),
    ]
    all_conditions = base_conditions + extra_conditions

    stmt = (
        select(
            Metric.consumer_name.label("name"),
            Metric.consumer_type.label("type"),
            func.count().label("count"),
            func.avg(Metric.latency).label("avg_latency"),
            func.avg(Metric.cost).label("avg_total_cost"),
            func.sum(Metric.cost).label("total_cost"),
            func.count(distinct(Metric.user_id)).label("unique_user_count"),
            func.sum(case((Metric.status == "error", 1), else_=0)).label("error_count"),
        )
        .where(*all_conditions)
        .group_by(Metric.consumer_name, Metric.consumer_type)
        .order_by(func.count().desc())
    )

    result = await db_session.execute(stmt)
    metrics = []

    for row in result.fetchall():
        error_rate = (row.error_count / row.count) * 100 if row.count > 0 else 0
        metrics.append(
            {
                "name": row.name,
                "type": row.type,
                "count": row.count,
                "avg_latency": row.avg_latency,
                "avg_total_cost": row.avg_total_cost,
                "total_cost": row.total_cost,
                "unique_user_count": row.unique_user_count,
                "error_rate": error_rate,
            }
        )

    return metrics


async def get_top_metrics_agent(
    db_session: AsyncSession, filters: FilterObject | None
) -> list[MetricsTopList]:
    """Get top Agent metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "agent",
    ]
    all_conditions = base_conditions + extra_conditions

    stmt = (
        select(
            Metric.feature_name.label("name"),
            Metric.feature_system_name.label("system_name"),
            func.count().label("count"),
            func.avg(Metric.latency).label("avg_duration"),
            func.avg(Metric.cost).label("avg_total_cost"),
            func.sum(Metric.cost).label("total_cost"),
            func.count(distinct(Metric.user_id)).label("unique_user_count"),
            func.count(distinct(Metric.conversation_id)).label("conversation_count"),
            func.avg(
                Metric.conversation_data["avg_tool_call_latency"].as_float()
            ).label("avg_tool_call_latency"),
            func.sum(Metric.conversation_data["likes"].as_integer()).label(
                "total_likes"
            ),
            func.sum(Metric.conversation_data["dislikes"].as_integer()).label(
                "total_dislikes"
            ),
            func.sum(
                case(
                    (
                        Metric.conversation_data["resolution_status"].as_string()
                        == "resolved",
                        1,
                    ),
                    else_=0,
                )
            ).label("total_status_resolved"),
        )
        .where(*all_conditions)
        .group_by(Metric.feature_name, Metric.feature_system_name)
        .order_by(func.count().desc())
    )

    result = await db_session.execute(stmt)
    metrics = []

    for row in result.fetchall():
        metrics.append(
            {
                "name": row.name,
                "system_name": row.system_name,
                "count": row.count,
                "avg_duration": row.avg_duration,
                "avg_tool_call_latency": row.avg_tool_call_latency,
                "avg_total_cost": row.avg_total_cost,
                "total_cost": row.total_cost,
                "unique_user_count": row.unique_user_count,
                "conversation_count": row.conversation_count,
                "total_likes": row.total_likes,
                "total_dislikes": row.total_dislikes,
                "total_status_resolved": row.total_status_resolved,
            }
        )

    return metrics


async def get_top_metrics_rag(
    db_session: AsyncSession, filters: FilterObject | None
) -> list[MetricsTopList]:
    """Get top RAG metrics"""
    extra_conditions = _build_where_conditions(filters)

    base_conditions = [
        Metric.feature_type == "rag-tool",
        Metric.status == "success",
        Metric.channel == "production",
    ]
    all_conditions = base_conditions + extra_conditions

    stmt = (
        select(
            Metric.feature_system_name.label("name"),
            func.count().label("count"),
            func.avg(Metric.latency).label("avg_latency"),
            func.avg(Metric.cost).label("avg_total_cost"),
            func.count(distinct(Metric.user_id)).label("unique_user_count"),
        )
        .where(*all_conditions)
        .group_by(Metric.feature_system_name)
        .order_by(func.count().desc())
    )

    result = await db_session.execute(stmt)
    metrics = []

    for row in result.fetchall():
        metrics.append(
            {
                "name": row.name,
                "count": row.count,
                "avg_latency": row.avg_latency,
                "avg_total_cost": row.avg_total_cost,
                "unique_user_count": row.unique_user_count,
            }
        )

    return metrics


async def get_metrics_by_feature_type(
    db_session: AsyncSession,
    feature_types: list[FeatureType] | FeatureType,
    data: OffsetPaginationRequest | None,
) -> MetricsQueryResult:
    """Get metrics by feature type"""
    # Handle pagination parameters
    if data is not None and getattr(data, "filters", None) is not None:
        filters = data.filters
        sort = data.sort or "id"
        limit = data.limit or 10
        skip = data.offset or 0
        order = "DESC" if data.order == -1 else "ASC"
    else:
        filters = None
        sort = "id"
        limit = 10
        skip = 0
        order = "DESC"

    # Resolve the sort column
    if sort and "." in sort:
        parts = sort.split(".", 1)
        if parts[0] in ["extra_data", "conversation_data", "x_attributes"]:
            json_field = getattr(Metric, parts[0])
            sort_col = json_field[parts[1]].as_string()
        else:
            sort_col = getattr(Metric, sort, Metric.id)
    else:
        sort_col = getattr(Metric, sort, Metric.id)

    extra_conditions = _build_where_conditions(filters)

    # Build feature type condition
    if isinstance(feature_types, FeatureType):
        if feature_types == FeatureType.RAG_TOOL:
            feature_conditions = [
                Metric.feature_type == "rag-tool",
                Metric.status == "success",
            ]
        else:
            feature_conditions = [Metric.feature_type == feature_types.value]
    elif isinstance(feature_types, list):
        feature_type_values = [ft.value for ft in feature_types]
        feature_conditions = [Metric.feature_type.in_(feature_type_values)]
    else:
        feature_conditions = []

    all_conditions = feature_conditions + extra_conditions

    # Get count for pagination
    count_stmt = select(func.count()).select_from(Metric).where(*all_conditions)
    count_result = await db_session.execute(count_stmt)
    total_count = count_result.scalar()

    # Build the columns to select
    columns = [
        Metric.id,
        Metric.feature_name,
        Metric.feature_id,
        Metric.feature_system_name,
        Metric.feature_type,
        Metric.feature_variant,
        Metric.status,
        Metric.start_time,
        Metric.end_time,
        Metric.channel,
        Metric.source,
        Metric.latency,
        Metric.extra_data,
        Metric.conversation_id,
        Metric.conversation_data,
        Metric.trace_id,
        Metric.cost,
        Metric.consumer_name,
        Metric.consumer_type,
        Metric.x_attributes,
        Metric.created_at,
        Metric.updated_at,
    ]

    if OBSERVABILITY_USAGE_SHOW_USERS:
        columns.append(Metric.user_id)

    # Apply ordering
    order_clause = sort_col.desc() if order == "DESC" else sort_col.asc()

    metrics_stmt = (
        select(*columns)
        .where(*all_conditions)
        .order_by(order_clause)
        .limit(limit)
        .offset(skip)
    )

    result = await db_session.execute(metrics_stmt)

    # Convert to dict format for compatibility
    items = []
    for row in result.fetchall():
        item = {
            "_id": row.id,
            "name": row.feature_name,
            "feature_id": row.feature_id,
            "feature_name": row.feature_name,
            "feature_system_name": row.feature_system_name,
            "feature_type": row.feature_type,
            "feature_variant": row.feature_variant,
            "variant": row.feature_variant,
            "status": row.status,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "channel": row.channel,
            "source": row.source,
            "latency": row.latency,
            "extra_data": row.extra_data or {},
            "conversation_id": row.conversation_id,
            "conversation_data": row.conversation_data or {},
            "trace_id": row.trace_id,
            "cost": row.cost,
            "consumer_name": row.consumer_name,
            "consumer_type": row.consumer_type,
            "x_attributes": row.x_attributes or {},
        }

        if OBSERVABILITY_USAGE_SHOW_USERS:
            item["user_id"] = row.user_id

        items.append(item)

    return {
        "items": items,
        "total": total_count,
        "limit": limit,
        "offset": skip,
    }


async def update_analytics_extra_data(
    db_session: AsyncSession,
    analytics_id: str,
    language: str | None = None,
    is_answered: bool | None = None,
    resolution: str | None = None,
    topic: str | None = None,
    comment: str | None = None,
    substandart_result_reason: str | None = None,
    status: str | None = None,
) -> bool:
    """Update specific fields inside the extra_data object of a metric using ORM way"""
    try:
        logger.info(
            f"[update_analytics_extra_data] Called with analytics_id={analytics_id}, "
            f"language={language}, is_answered={is_answered}, resolution={resolution}, "
            f"topic={topic}, comment={comment}, substandart_result_reason={substandart_result_reason}, "
            f"status={status}"
        )

        # Get the metric by ID
        metric = await db_session.get(Metric, analytics_id)
        if not metric:
            logger.warning(
                f"[update_analytics_extra_data] Metric not found: {analytics_id}"
            )
            return False

        # Initialize extra_data if it doesn't exist
        if not metric.extra_data:
            metric.extra_data = {}

        # Track if any changes were made
        updated = False

        # Update fields that are provided
        if status is not None:
            logger.info(f"[update_analytics_extra_data] Updating status to: {status}")
            metric.extra_data["status"] = status
            updated = True

        if language is not None:
            logger.info(
                f"[update_analytics_extra_data] Updating language to: {language}"
            )
            metric.extra_data["language"] = language
            updated = True

        if is_answered is not None:
            logger.info(
                f"[update_analytics_extra_data] Updating is_answered to: {is_answered}"
            )
            metric.extra_data["is_answered"] = is_answered
            updated = True

        if resolution is not None:
            logger.info(
                f"[update_analytics_extra_data] Updating resolution to: {resolution}"
            )
            metric.extra_data["resolution"] = resolution
            updated = True

        if topic is not None:
            logger.info(f"[update_analytics_extra_data] Updating topic to: {topic}")
            metric.extra_data["topic"] = topic
            updated = True

        if comment is not None:
            logger.info(f"[update_analytics_extra_data] Updating comment to: {comment}")
            metric.extra_data["comment"] = comment
            updated = True

        if substandart_result_reason is not None:
            logger.info(
                f"[update_analytics_extra_data] Updating substandart_result_reason to: {substandart_result_reason}"
            )
            metric.extra_data["substandart_result_reason"] = substandart_result_reason
            updated = True

        if updated:
            # Mark the JSONB field as modified so SQLAlchemy knows to update it
            flag_modified(metric, "extra_data")
            logger.info(
                f"[update_analytics_extra_data] Committing changes for metric {analytics_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_analytics_extra_data] No fields to update for metric {analytics_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating analytics extra data: {e}")
        await db_session.rollback()
        return False


async def update_metric_conversation_data(
    db_session: AsyncSession, analytics_id: str, data: dict
) -> bool:
    """Update conversation_data fields of a metric using ORM way"""
    try:
        logger.info(
            f"[update_metric_conversation_data] Called with analytics_id={analytics_id}, data={data}"
        )

        # Get the metric by ID
        metric = await db_session.get(Metric, analytics_id)
        if not metric:
            logger.warning(
                f"[update_metric_conversation_data] Metric not found: {analytics_id}"
            )
            return False

        # Initialize conversation_data if it doesn't exist
        if not metric.conversation_data:
            metric.conversation_data = {}

        # Track if any changes were made
        updated = False

        # Update fields from provided data
        for key, value in data.items():
            logger.info(f"[update_metric_conversation_data] Updating {key} to: {value}")
            metric.conversation_data[key] = value
            updated = True

        if updated:
            # Mark the JSONB field as modified so SQLAlchemy knows to update it
            flag_modified(metric, "conversation_data")
            logger.info(
                f"[update_metric_conversation_data] Committing changes for metric {analytics_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_metric_conversation_data] No fields to update for metric {analytics_id}"
            )

        return updated
    except Exception as e:
        logger.error(f"Error updating metric conversation data: {e}")
        await db_session.rollback()
        return False


async def get_analytics_by_id(
    db_session: AsyncSession, analytics_id: str
) -> dict[str, Any] | None:
    """Get analytics by ID"""
    try:
        stmt = select(Metric).where(Metric.id == analytics_id)
        result = await db_session.execute(stmt)
        row = result.scalars().first()

        if not row:
            raise RecordNotFoundError()

        # Convert to dict format for compatibility
        return {
            "_id": row.id,
            "feature_name": row.feature_name,
            "feature_system_name": row.feature_system_name,
            "feature_type": row.feature_type,
            "feature_id": row.feature_id,
            "feature_variant": row.feature_variant,
            "channel": row.channel,
            "source": row.source,
            "status": row.status,
            "start_time": row.start_time,
            "end_time": row.end_time,
            "latency": row.latency,
            "cost": row.cost,
            "trace_id": row.trace_id,
            "user_id": row.user_id,
            "consumer_name": row.consumer_name,
            "consumer_type": row.consumer_type,
            "conversation_id": row.conversation_id,
            "conversation_data": row.conversation_data,
            "extra_data": row.extra_data,
            "x_attributes": row.x_attributes,
        }
    except Exception as e:
        logger.error(f"Error getting analytics by ID: {e}")
        return None


# Export functions remain the same as they work with the dict format returned by get_metrics_by_feature_type
async def create_file_with_rag_metrics_for_export(
    metrics: list[MetricsItem],
    format: str = "csv",
) -> str:
    """Create file with RAG metrics for export - same implementation as original"""
    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "name",
                "variant",
                "consumer_type",
                "consumer_name",
                "start_time",
                "end_time",
                "latency",
                "cost",
                "question",
                "question_topic",
                "answer",
                "is_answered",
                "answer_feedback_type",
                "answer_feedback_reason",
                "answer_feedback_comment",
                "answer_copied",
                "language",
                "organization",
                "substandart_result_reason",
                "substandart_result_comment",
                *(["user_id"] if OBSERVABILITY_USAGE_SHOW_USERS else []),
            ],
        )
        writer.writeheader()

        for item in metrics:
            writer.writerow(
                {
                    "name": item["feature_system_name"],
                    "variant": item.get("variant"),
                    "consumer_type": item.get("consumer_type"),
                    "consumer_name": item.get("consumer_name"),
                    "start_time": item["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["start_time"]
                    else None,
                    "end_time": item["end_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["end_time"]
                    else None,
                    "latency": item["latency"],
                    "cost": item["cost"],
                    "question": item.get("extra_data", {}).get("question"),
                    "question_topic": item.get("extra_data", {}).get("topic"),
                    "answer": item.get("extra_data", {}).get("answer"),
                    "is_answered": item.get("extra_data", {}).get("is_answered"),
                    "answer_feedback_type": item.get("extra_data", {})
                    .get("answer_feedback", {})
                    .get("type"),
                    "answer_feedback_reason": item.get("extra_data", {})
                    .get("answer_feedback", {})
                    .get("reason"),
                    "answer_feedback_comment": item.get("extra_data", {})
                    .get("answer_feedback", {})
                    .get("comment"),
                    "answer_copied": (item.get("extra_data") or {}).get("answer_copy")
                    or False,
                    "language": item.get("extra_data", {}).get("language"),
                    "organization": (item.get("x_attributes") or {}).get("org-id"),
                    "substandart_result_reason": item.get("extra_data", {}).get(
                        "substandart_result_reason"
                    ),
                    "substandart_result_comment": item.get("extra_data", {}).get(
                        "comment"
                    ),
                    **(
                        {"user_id": item.get("user_id")}
                        if OBSERVABILITY_USAGE_SHOW_USERS
                        else {}
                    ),
                }
            )

        # Generate filename for rag metrics
        filename = f"/tmp/rag_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Write rag metrics to file
        async with aiofiles.open(filename, "w", encoding="utf-8", newline="") as f:
            await f.write(output.getvalue())

        return filename

    if format == "json":
        rag_metrics = []
        for item in metrics:
            rag_metrics.append(
                {
                    "name": item["feature_system_name"],
                    "variant": item.get("variant"),
                    "consumer": {
                        "type": item.get("consumer_type"),
                        "name": item.get("consumer_name"),
                    },
                    "start_time": item["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["start_time"]
                    else None,
                    "end_time": item["end_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["end_time"]
                    else None,
                    "latency": item["latency"],
                    "cost": item["cost"],
                    "question": item.get("extra_data", {}).get("question"),
                    "question_topic": item.get("extra_data", {}).get("topic"),
                    "answer": item.get("extra_data", {}).get("answer"),
                    "is_answered": item.get("extra_data", {}).get("is_answered"),
                    "answer_feedback": item.get("extra_data", {}).get(
                        "answer_feedback",
                        {},
                    ),
                    "answer_copied": (item.get("extra_data") or {}).get("answer_copy")
                    or False,
                    "language": item.get("extra_data", {}).get("language"),
                    "organization": (item.get("x_attributes") or {}).get("org-id"),
                    "substandart_result_reason": item.get("extra_data", {}).get(
                        "substandart_result_reason"
                    ),
                    "substandart_result_comment": item.get("extra_data", {}).get(
                        "comment"
                    ),
                    **(
                        {"user_id": item.get("user_id")}
                        if OBSERVABILITY_USAGE_SHOW_USERS
                        else {}
                    ),
                }
            )

        # Generate filename
        filename = f"/tmp/rag_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Write export data to file
        async with aiofiles.open(filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(rag_metrics, indent=4))

        return filename

    raise Exception("Invalid export format")


async def create_file_with_agent_metrics_for_export(
    metrics: list[MetricsItem],
    format: str = "csv",
) -> str:
    """Create file with Agent metrics for export - simplified version for SQL"""
    # This is a simplified version - in a full implementation you would need to
    # query the agent_conversations table as well
    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "name",
                "variant",
                "consumer_type",
                "consumer_name",
                "start_time",
                "end_time",
                "status",
                "avg_latency",
                "total_cost",
                "agent_topics",
                "resolution_status",
                "total_likes",
                "total_dislikes",
                "avg_response_time",
                "answer_copied",
                "language",
                "sentiment",
                "substandart_result_reason",
                "substandart_result_comment",
                "organization",
                *(["user_id"] if OBSERVABILITY_USAGE_SHOW_USERS else []),
                "conversation_id",
            ],
        )
        writer.writeheader()

        for item in metrics:
            conversation_id = (item.get("extra_data") or {}).get(
                "conversation_id"
            ) or item.get("conversation_id")

            writer.writerow(
                {
                    "name": item["feature_system_name"],
                    "variant": item.get("variant"),
                    "consumer_type": item.get("consumer_type"),
                    "consumer_name": item.get("consumer_name"),
                    "start_time": item["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["start_time"]
                    else None,
                    "end_time": item["end_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["end_time"]
                    else None,
                    "status": item.get("status"),
                    "avg_latency": item.get("conversation_data", {}).get(
                        "avg_tool_call_latency"
                    ),
                    "total_cost": item.get("cost"),
                    "agent_topics": ",".join(
                        (item.get("conversation_data") or {}).get("topics") or []
                    ),
                    "resolution_status": item.get("conversation_data", {}).get(
                        "resolution_status",
                    ),
                    "total_likes": item.get("conversation_data", {}).get("likes"),
                    "total_dislikes": item.get("conversation_data", {}).get("dislikes"),
                    "avg_response_time": item.get("conversation_data", {}).get(
                        "avg_tool_call_latency"
                    ),
                    "answer_copied": (item.get("extra_data") or {}).get("answer_copy")
                    or False,
                    "language": item.get("conversation_data", {}).get("language"),
                    "sentiment": item.get("conversation_data", {}).get("sentiment"),
                    "substandart_result_reason": item.get("conversation_data", {}).get(
                        "substandart_result_reason"
                    ),
                    "substandart_result_comment": item.get("conversation_data", {}).get(
                        "comment"
                    ),
                    "organization": (item.get("x_attributes") or {}).get("org-id"),
                    **(
                        {"user_id": item.get("user_id")}
                        if OBSERVABILITY_USAGE_SHOW_USERS
                        else {}
                    ),
                    "conversation_id": conversation_id,
                },
            )

        # Generate filename for agent metrics
        agent_data_filename = (
            f"/tmp/agent_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        # Write agent metrics to file
        async with aiofiles.open(
            agent_data_filename, "w", encoding="utf-8", newline=""
        ) as f:
            await f.write(output.getvalue())

        return agent_data_filename

    if format == "json":
        agent_metrics = []
        for item in metrics:
            conversation_id = (item.get("extra_data") or {}).get(
                "conversation_id"
            ) or item.get("conversation_id")

            agent_metrics.append(
                {
                    "name": item["feature_system_name"],
                    "variant": item.get("variant"),
                    "consumer": {
                        "type": item.get("consumer_type"),
                        "name": item.get("consumer_name"),
                    },
                    "start_time": item["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["start_time"]
                    else None,
                    "end_time": item["end_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if item["end_time"]
                    else None,
                    "status": item.get("status"),
                    "avg_latency": item.get("conversation_data", {}).get(
                        "avg_tool_call_latency"
                    ),
                    "total_cost": item.get("cost"),
                    "agent_topics": ",".join(
                        (item.get("conversation_data") or {}).get("topics") or []
                    ),
                    "resolution_status": item.get("conversation_data", {}).get(
                        "resolution_status",
                    ),
                    "total_likes": item.get("conversation_data", {}).get("likes"),
                    "total_dislikes": item.get("conversation_data", {}).get("dislikes"),
                    "avg_response_time": item.get("conversation_data", {}).get(
                        "avg_tool_call_latency"
                    ),
                    "answer_copied": (item.get("extra_data") or {}).get("answer_copy")
                    or False,
                    "language": item.get("conversation_data", {}).get("language"),
                    "sentiment": item.get("conversation_data", {}).get("sentiment"),
                    "substandart_result_reason": item.get("conversation_data", {}).get(
                        "substandart_result_reason"
                    ),
                    "substandart_result_comment": item.get("conversation_data", {}).get(
                        "comment"
                    ),
                    "organization": (item.get("x_attributes") or {}).get("org-id"),
                    **(
                        {"user_id": item.get("user_id")}
                        if OBSERVABILITY_USAGE_SHOW_USERS
                        else {}
                    ),
                    "conversation_id": conversation_id,
                },
            )

        # Generate filename
        agent_data_filename = (
            f"/tmp/agent_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # Write export data to file
        async with aiofiles.open(agent_data_filename, "w", encoding="utf-8") as f:
            await f.write(json.dumps(agent_metrics, indent=4))

        return agent_data_filename

    raise Exception("Invalid export format")
