import csv
import json
import os
from datetime import datetime
from io import StringIO
from logging import getLogger
from typing import Any

import aiofiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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

OBSERVABILITY_TRACE_USERS = (
    os.getenv("OBSERVABILITY_TRACE_USERS", "false").lower() == "true"
)


def _build_where_clause(filters: FilterObject | None) -> tuple[str, dict]:
    """Build WHERE clause and parameters from filters"""
    if not filters:
        return "", {}

    filter_dict = filters.model_dump(exclude_none=True, by_alias=True)
    where_clause, params = _build_conditions(filter_dict)

    return f" AND {where_clause}" if where_clause else "", params


def _build_conditions(
    filter_dict: dict, param_counter: list[int] | None = None
) -> tuple[str, dict]:
    """Recursively build WHERE conditions from filter dictionary"""
    if param_counter is None:
        param_counter = [0]

    conditions = []
    params = {}

    for key, value in filter_dict.items():
        if key == "$and":
            # Handle $and operator
            and_conditions = []
            for and_filter in value:
                and_condition, and_params = _build_conditions(and_filter, param_counter)
                if and_condition:
                    and_conditions.append(f"({and_condition})")
                    params.update(and_params)
            if and_conditions:
                conditions.append(f"({' AND '.join(and_conditions)})")
        elif key == "$or":
            # Handle $or operator
            or_conditions = []
            for or_filter in value:
                or_condition, or_params = _build_conditions(or_filter, param_counter)
                if or_condition:
                    or_conditions.append(f"({or_condition})")
                    params.update(or_params)
            if or_conditions:
                conditions.append(f"({' OR '.join(or_conditions)})")
        else:
            # Handle field conditions
            field_condition, field_params = _build_field_condition(
                key, value, param_counter
            )
            if field_condition:
                conditions.append(field_condition)
                params.update(field_params)

    return " AND ".join(conditions), params


def _build_field_condition(
    key: str, value: dict, param_counter: list[int]
) -> tuple[str, dict]:
    """Build condition for a single field"""
    if not isinstance(value, dict):
        return "", {}

    conditions = []
    params = {}

    for operator, op_value in value.items():
        param_counter[0] += 1
        param_key = f"param_{param_counter[0]}"

        if operator == "$in":
            # Handle $in operator
            if isinstance(op_value, list):
                placeholders = []
                for i, val in enumerate(op_value):
                    param_counter[0] += 1
                    placeholder = f"param_{param_counter[0]}"
                    placeholders.append(f":{placeholder}")
                    params[placeholder] = val

                field_expr = _get_field_expression(key)
                conditions.append(f"{field_expr} IN ({','.join(placeholders)})")
        elif operator == "$nin":
            # Handle $nin operator
            if isinstance(op_value, list):
                placeholders = []
                for i, val in enumerate(op_value):
                    param_counter[0] += 1
                    placeholder = f"param_{param_counter[0]}"
                    placeholders.append(f":{placeholder}")
                    params[placeholder] = val

                field_expr = _get_field_expression(key)
                conditions.append(f"{field_expr} NOT IN ({','.join(placeholders)})")
        elif operator == "$ne":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} != :{param_key}")
            params[param_key] = op_value
        elif operator == "$gte":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} >= :{param_key}")
            params[param_key] = op_value
        elif operator == "$lte":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} <= :{param_key}")
            params[param_key] = op_value
        elif operator == "$gt":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} > :{param_key}")
            params[param_key] = op_value
        elif operator == "$lt":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} < :{param_key}")
            params[param_key] = op_value
        elif operator == "$eq":
            field_expr = _get_field_expression(key)
            conditions.append(f"{field_expr} = :{param_key}")
            params[param_key] = op_value
        elif operator == "$regex":
            field_expr = _get_field_expression(key)
            # For PostgreSQL, use ILIKE for case-insensitive pattern matching
            conditions.append(f"{field_expr} ILIKE :{param_key}")
            # Convert regex pattern to SQL LIKE pattern
            like_pattern = op_value.replace(".*", "%").replace(".", "_")
            params[param_key] = f"%{like_pattern}%"
        elif operator == "$exists":
            field_expr = _get_field_expression(key)
            if op_value:
                conditions.append(f"{field_expr} IS NOT NULL")
            else:
                conditions.append(f"{field_expr} IS NULL")

    return " AND ".join(conditions), params


def _get_field_expression(key: str) -> str:
    """Get the SQL field expression for a given key"""
    if "." in key:
        # Handle JSON field filters
        if key.startswith("extra_data."):
            json_path = key.replace("extra_data.", "")
            return f"extra_data->>'{json_path}'"
        elif key.startswith("conversation_data."):
            json_path = key.replace("conversation_data.", "")
            return f"conversation_data->>'{json_path}'"
        elif key.startswith("x_attributes."):
            json_path = key.replace("x_attributes.", "")
            return f"x_attributes->>'{json_path}'"
    return key


async def get_options_rag(
    db_session: AsyncSession, filters: FilterObject | None
) -> OptionsRagResponse:
    """Get RAG tool options using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type = 'rag-tool' AND status = 'success'"
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get topics
    topics_sql = f"""
        SELECT DISTINCT extra_data->>'topic' as topic
        FROM metrics 
        {full_where} AND extra_data->>'topic' IS NOT NULL
        ORDER BY topic
    """

    topics_result = await db_session.execute(text(topics_sql), params)
    topics = [row.topic for row in topics_result.fetchall() if row.topic]

    # Get languages
    languages_sql = f"""
        SELECT DISTINCT extra_data->>'language' as language
        FROM metrics 
        {full_where} AND extra_data->>'language' IS NOT NULL
        ORDER BY language
    """

    languages_result = await db_session.execute(text(languages_sql), params)
    languages = [row.language for row in languages_result.fetchall() if row.language]

    # Get consumer names
    consumer_names_sql = f"""
        SELECT DISTINCT consumer_name
        FROM metrics 
        {full_where} AND consumer_name IS NOT NULL
        ORDER BY consumer_name
    """

    consumer_names_result = await db_session.execute(text(consumer_names_sql), params)
    consumer_names = [
        row.consumer_name
        for row in consumer_names_result.fetchall()
        if row.consumer_name
    ]

    # Get organizations
    organizations_sql = f"""
        SELECT DISTINCT x_attributes->>'org-id' as org_id
        FROM metrics 
        {full_where} AND x_attributes->>'org-id' IS NOT NULL
        ORDER BY org_id
    """

    organizations_result = await db_session.execute(text(organizations_sql), params)
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
    """Get LLM options using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type IN ('prompt-template', 'chat-completion-api', 'embedding-api', 'reranking-api')"
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get consumer names
    consumer_names_sql = f"""
        SELECT DISTINCT consumer_name
        FROM metrics 
        {full_where} AND consumer_name IS NOT NULL
        ORDER BY consumer_name
    """

    consumer_names_result = await db_session.execute(text(consumer_names_sql), params)
    consumer_names = [
        row.consumer_name
        for row in consumer_names_result.fetchall()
        if row.consumer_name
    ]

    # Get organizations
    organizations_sql = f"""
        SELECT DISTINCT x_attributes->>'org-id' as org_id
        FROM metrics 
        {full_where} AND x_attributes->>'org-id' IS NOT NULL
        ORDER BY org_id
    """

    organizations_result = await db_session.execute(text(organizations_sql), params)
    organizations = [
        row.org_id for row in organizations_result.fetchall() if row.org_id
    ]

    return OptionsLlmResponse(
        consumer_names=consumer_names, organizations=organizations
    )


async def get_options_agent(
    db_session: AsyncSession, filters: FilterObject | None
) -> OptionsAgentResponse:
    """Get Agent options using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type = 'agent' AND status = 'success'"
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get topics from conversation_data.topics array
    topics_sql = f"""
        SELECT DISTINCT jsonb_array_elements_text(conversation_data->'topics') as topic
        FROM metrics 
        {full_where} AND conversation_data->'topics' IS NOT NULL
        ORDER BY topic
    """

    topics_result = await db_session.execute(text(topics_sql), params)
    topics = [row.topic for row in topics_result.fetchall() if row.topic]

    # Get feature system names as tools
    tools_sql = f"""
        SELECT DISTINCT feature_system_name
        FROM metrics 
        {full_where} AND feature_system_name IS NOT NULL
        ORDER BY feature_system_name
    """

    tools_result = await db_session.execute(text(tools_sql), params)
    tools = [
        row.feature_system_name
        for row in tools_result.fetchall()
        if row.feature_system_name
    ]

    # Get consumer names
    consumer_names_sql = f"""
        SELECT DISTINCT consumer_name
        FROM metrics 
        {full_where} AND consumer_name IS NOT NULL
        ORDER BY consumer_name
    """

    consumer_names_result = await db_session.execute(text(consumer_names_sql), params)
    consumer_names = [
        row.consumer_name
        for row in consumer_names_result.fetchall()
        if row.consumer_name
    ]

    # Get languages
    languages_sql = f"""
        SELECT DISTINCT conversation_data->>'language' as language
        FROM metrics 
        {full_where} AND conversation_data->>'language' IS NOT NULL
        ORDER BY language
    """

    languages_result = await db_session.execute(text(languages_sql), params)
    languages = [row.language for row in languages_result.fetchall() if row.language]

    # Get organizations
    organizations_sql = f"""
        SELECT DISTINCT x_attributes->>'org-id' as org_id
        FROM metrics 
        {full_where} AND x_attributes->>'org-id' IS NOT NULL
        ORDER BY org_id
    """

    organizations_result = await db_session.execute(text(organizations_sql), params)
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
    """Summarize RAG tool metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = (
        "feature_type = 'rag-tool' AND status = 'success' AND channel = 'production'"
    )
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get general metrics
    general_sql = f"""
        SELECT 
            COUNT(*) as total_calls,
            AVG(latency) as avg_latency,
            AVG(cost) as avg_cost,
            SUM(cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_user_count
        FROM metrics 
        {full_where}
    """

    general_result = await db_session.execute(text(general_sql), params)
    general_metrics = general_result.first()

    if not general_metrics or general_metrics.total_calls == 0:
        return EmptyDictionary()

    # Get resolution metrics
    resolution_sql = f"""
        SELECT 
            extra_data->>'is_answered' as resolution,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY extra_data->>'is_answered'
    """

    resolution_result = await db_session.execute(text(resolution_sql), params)
    resolution_metrics = [
        {"_id": row.resolution, "count": row.count}
        for row in resolution_result.fetchall()
    ]

    # Get topic metrics
    topic_sql = f"""
        SELECT 
            extra_data->>'topic' as topic,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY extra_data->>'topic'
    """

    topic_result = await db_session.execute(text(topic_sql), params)
    topic_metrics = [
        {"_id": row.topic, "count": row.count} for row in topic_result.fetchall()
    ]

    # Get feedback metrics
    feedback_sql = f"""
        SELECT 
            extra_data->'answer_feedback'->>'type' as feedback_type,
            COUNT(*) as count
        FROM metrics 
        {full_where} AND extra_data->'answer_feedback'->>'type' IS NOT NULL
        GROUP BY extra_data->'answer_feedback'->>'type'
    """

    feedback_result = await db_session.execute(text(feedback_sql), params)
    feedback_metrics = [
        {"_id": row.feedback_type, "count": row.count}
        for row in feedback_result.fetchall()
    ]

    # Get copy metrics
    copy_sql = f"""
        SELECT COUNT(*) as copy_count
        FROM metrics 
        {full_where} AND (extra_data->>'answer_copy')::boolean = true
    """

    copy_result = await db_session.execute(text(copy_sql), params)
    copy_count = copy_result.scalar() or 0

    # Get language metrics
    language_sql = f"""
        SELECT 
            extra_data->>'language' as language,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY extra_data->>'language'
    """

    language_result = await db_session.execute(text(language_sql), params)
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
    """Summarize LLM metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type IN ('prompt-template', 'chat-completion-api', 'embedding-api', 'reranking-api')"
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get general metrics
    general_sql = f"""
        SELECT 
            COUNT(*) as count,
            AVG(latency) as avg_latency,
            AVG(cost) as avg_total_cost,
            SUM(cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_user_count,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
        FROM metrics 
        {full_where}
    """

    general_result = await db_session.execute(text(general_sql), params)
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
    """Summarize Agent metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type = 'agent' AND status = 'success'"
    full_where = f"WHERE {base_condition}{where_clause}"

    # Get general metrics
    general_sql = f"""
        SELECT 
            COUNT(*) as count,
            AVG(latency) as avg_duration,
            AVG(cost) as avg_cost,
            SUM(cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_user_count,
            COUNT(DISTINCT conversation_id) as conversation_count,
            AVG((conversation_data->>'avg_tool_call_latency')::float) as avg_tool_call_latency,
            SUM((conversation_data->>'likes')::int) as total_likes,
            SUM((conversation_data->>'dislikes')::int) as total_dislikes,
            AVG((conversation_data->>'messages_count')::float) as avg_messages_count,
            SUM(CASE WHEN conversation_data->>'resolution_status' = 'resolved' THEN 1 ELSE 0 END) as total_status_resolved,
            SUM(CASE WHEN (extra_data->>'answer_copy')::boolean = true THEN 1 ELSE 0 END) as copy_count,
            SUM(CASE WHEN (COALESCE((conversation_data->>'likes')::int, 0) + COALESCE((conversation_data->>'dislikes')::int, 0)) > 0 THEN 1 ELSE 0 END) as feedback_count
        FROM metrics 
        {full_where}
    """

    general_result = await db_session.execute(text(general_sql), params)
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
    resolution_sql = f"""
        SELECT 
            conversation_data->>'resolution_status' as resolution_status,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY conversation_data->>'resolution_status'
    """

    resolution_result = await db_session.execute(text(resolution_sql), params)
    resolution_metrics = [
        {"_id": row.resolution_status, "count": row.count}
        for row in resolution_result.fetchall()
    ]

    # Get channel metrics
    channel_sql = f"""
        SELECT 
            channel,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY channel
    """

    channel_result = await db_session.execute(text(channel_sql), params)
    channel_metrics = [
        {"_id": row.channel, "count": row.count} for row in channel_result.fetchall()
    ]

    # Get sentiment metrics
    sentiment_sql = f"""
        SELECT 
            conversation_data->>'sentiment' as sentiment,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY conversation_data->>'sentiment'
    """

    sentiment_result = await db_session.execute(text(sentiment_sql), params)
    sentiment_metrics = [
        {"_id": row.sentiment, "count": row.count}
        for row in sentiment_result.fetchall()
    ]

    # Get topics metrics (this requires handling JSONB arrays)
    topics_sql = f"""
        SELECT 
            jsonb_array_elements_text(conversation_data->'topics') as topic,
            COUNT(*) as count
        FROM metrics 
        {full_where} AND conversation_data->'topics' IS NOT NULL
        GROUP BY jsonb_array_elements_text(conversation_data->'topics')
    """

    topics_result = await db_session.execute(text(topics_sql), params)
    topics_metrics = [
        {"_id": row.topic, "count": row.count} for row in topics_result.fetchall()
    ]

    # Get language metrics
    language_sql = f"""
        SELECT 
            conversation_data->>'language' as language,
            COUNT(*) as count
        FROM metrics 
        {full_where}
        GROUP BY conversation_data->>'language'
    """

    language_result = await db_session.execute(text(language_sql), params)
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
    """Get top LLM metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type IN ('prompt-template', 'chat-completion-api', 'embedding-api', 'reranking-api')"
    full_where = f"WHERE {base_condition}{where_clause}"

    sql = f"""
        SELECT 
            consumer_name as name,
            consumer_type as type,
            COUNT(*) as count,
            AVG(latency) as avg_latency,
            AVG(cost) as avg_total_cost,
            SUM(cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_user_count,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
        FROM metrics 
        {full_where}
        GROUP BY consumer_name, consumer_type
        ORDER BY count DESC
    """

    result = await db_session.execute(text(sql), params)
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
    """Get top Agent metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = "feature_type = 'agent'"
    full_where = f"WHERE {base_condition}{where_clause}"

    sql = f"""
        SELECT 
            feature_name as name,
            feature_system_name as system_name,
            COUNT(*) as count,
            AVG(latency) as avg_duration,
            AVG(cost) as avg_total_cost,
            SUM(cost) as total_cost,
            COUNT(DISTINCT user_id) as unique_user_count,
            COUNT(DISTINCT conversation_id) as conversation_count,
            AVG((conversation_data->>'avg_tool_call_latency')::float) as avg_tool_call_latency,
            SUM((conversation_data->>'likes')::int) as total_likes,
            SUM((conversation_data->>'dislikes')::int) as total_dislikes,
            SUM(CASE WHEN conversation_data->>'resolution_status' = 'resolved' THEN 1 ELSE 0 END) as total_status_resolved
        FROM metrics 
        {full_where}
        GROUP BY feature_name, feature_system_name
        ORDER BY count DESC
    """

    result = await db_session.execute(text(sql), params)
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
    """Get top RAG metrics using raw SQL"""
    where_clause, params = _build_where_clause(filters)

    base_condition = (
        "feature_type = 'rag-tool' AND status = 'success' AND channel = 'production'"
    )
    full_where = f"WHERE {base_condition}{where_clause}"

    sql = f"""
        SELECT 
            feature_system_name as name,
            COUNT(*) as count,
            AVG(latency) as avg_latency,
            AVG(cost) as avg_total_cost,
            COUNT(DISTINCT user_id) as unique_user_count
        FROM metrics 
        {full_where}
        GROUP BY feature_system_name
        ORDER BY count DESC
    """

    result = await db_session.execute(text(sql), params)
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
    """Get metrics by feature type using raw SQL"""
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

    where_clause, params = _build_where_clause(filters)

    # Build feature type condition
    if isinstance(feature_types, FeatureType):
        if feature_types == FeatureType.RAG_TOOL:
            feature_condition = "feature_type = 'rag-tool' AND status = 'success'"
        else:
            feature_condition = f"feature_type = '{feature_types.value}'"
    elif isinstance(feature_types, list):
        feature_type_values = [ft.value for ft in feature_types]
        feature_condition = f"feature_type IN ({','.join([f':{i}' for i in range(len(feature_type_values))])})"
        for i, value in enumerate(feature_type_values):
            params[f"{i}"] = value
    else:
        feature_condition = "1=1"

    full_where = f"WHERE {feature_condition}{where_clause}"

    # Get count for pagination
    count_sql = f"""
        SELECT COUNT(*) as total_count
        FROM metrics 
        {full_where}
    """

    count_result = await db_session.execute(text(count_sql), params)
    total_count = count_result.scalar()

    # Get metrics with pagination
    user_id_field = "user_id," if OBSERVABILITY_TRACE_USERS else ""

    metrics_sql = f"""
        SELECT 
            id,
            feature_name,
            feature_id,
            feature_system_name,
            feature_type,
            feature_variant,
            status,
            start_time,
            end_time,
            channel,
            source,
            latency,
            extra_data,
            conversation_id,
            conversation_data,
            trace_id,
            cost,
            consumer_name,
            consumer_type,
            x_attributes,
            {user_id_field}
            created_at,
            updated_at
        FROM metrics 
        {full_where}
        ORDER BY {sort} {order}
        LIMIT {limit} OFFSET {skip}
    """

    result = await db_session.execute(text(metrics_sql), params)

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

        if OBSERVABILITY_TRACE_USERS:
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
    """Update specific fields inside the extra_data object of a metric using raw SQL"""
    try:
        # Build the JSON update expression
        updates = []
        params = {"analytics_id": analytics_id}

        if status is not None:
            updates.append("'status', :status")
            params["status"] = status
        if language is not None:
            updates.append("'language', :language")
            params["language"] = language
        if is_answered is not None:
            updates.append("'is_answered', :is_answered")
            params["is_answered"] = is_answered
        if resolution is not None:
            updates.append("'resolution', :resolution")
            params["resolution"] = resolution
        if topic is not None:
            updates.append("'topic', :topic")
            params["topic"] = topic
        if comment is not None:
            updates.append("'comment', :comment")
            params["comment"] = comment
        if substandart_result_reason is not None:
            updates.append("'substandart_result_reason', :substandart_result_reason")
            params["substandart_result_reason"] = substandart_result_reason

        if not updates:
            return False

        # Build the JSONB update expression
        update_expr = f"jsonb_build_object({', '.join(updates)})"

        sql = f"""
            UPDATE metrics 
            SET extra_data = COALESCE(extra_data, '{{}}'::jsonb) || {update_expr}
            WHERE id = :analytics_id
        """

        result = await db_session.execute(text(sql), params)
        await db_session.commit()

        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating analytics extra data: {e}")
        await db_session.rollback()
        return False


async def update_metric_conversation_data(
    db_session: AsyncSession, analytics_id: str, data: dict
) -> bool:
    """Update conversation_data fields of a metric using raw SQL"""
    try:
        # Build the JSON update expression
        updates = []
        params = {"analytics_id": analytics_id}

        for key, value in data.items():
            param_key = f"data_{key}"
            updates.append(f"'{key}', :{param_key}")
            params[param_key] = value

        if not updates:
            return False

        # Build the JSONB update expression
        update_expr = f"jsonb_build_object({', '.join(updates)})"

        sql = f"""
            UPDATE metrics 
            SET conversation_data = COALESCE(conversation_data, '{{}}'::jsonb) || {update_expr}
            WHERE id = :analytics_id
        """

        result = await db_session.execute(text(sql), params)
        await db_session.commit()

        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating metric conversation data: {e}")
        await db_session.rollback()
        return False


async def get_analytics_by_id(
    db_session: AsyncSession, analytics_id: str
) -> dict[str, Any] | None:
    """Get analytics by ID using raw SQL"""
    try:
        sql = """
            SELECT 
                id,
                feature_name,
                feature_system_name,
                feature_type,
                feature_id,
                feature_variant,
                channel,
                source,
                status,
                start_time,
                end_time,
                latency,
                cost,
                trace_id,
                user_id,
                consumer_name,
                consumer_type,
                conversation_id,
                conversation_data,
                extra_data,
                x_attributes
            FROM metrics 
            WHERE id = :analytics_id
        """

        result = await db_session.execute(text(sql), {"analytics_id": analytics_id})
        row = result.first()

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
                *(["user_id"] if OBSERVABILITY_TRACE_USERS else []),
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
                        if OBSERVABILITY_TRACE_USERS
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
                        if OBSERVABILITY_TRACE_USERS
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
                *(["user_id"] if OBSERVABILITY_TRACE_USERS else []),
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
                        if OBSERVABILITY_TRACE_USERS
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
                        if OBSERVABILITY_TRACE_USERS
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
