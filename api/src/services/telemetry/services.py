from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from core.config.app import alchemy
from core.db.models.metric.metric import Metric
from services.common.models import LlmResponseFeedback


async def record_tool_response_feedback(
    *,
    trace_id: str | None,
    analytics_id: str | None,
    feedback: LlmResponseFeedback,
) -> None:
    """Record feedback for a tool response."""
    if not analytics_id:
        return

    async with alchemy.get_session() as session:
        try:
            metric = (
                await session.execute(select(Metric).where(Metric.id == analytics_id))
            ).scalar_one_or_none()

            if metric is not None:
                extra = dict(metric.extra_data or {})
                extra["answer_feedback"] = feedback.model_dump()
                metric.extra_data = extra
                flag_modified(metric, "extra_data")

            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def record_tool_response_copy(
    *,
    trace_id: str | None,
    analytics_id: str | None,
) -> None:
    """Record that a tool response was copied."""
    if not analytics_id:
        return

    async with alchemy.get_session() as session:
        try:
            metric = (
                await session.execute(select(Metric).where(Metric.id == analytics_id))
            ).scalar_one_or_none()

            if metric is not None:
                extra = dict(metric.extra_data or {})
                extra["answer_copy"] = True
                metric.extra_data = extra
                flag_modified(metric, "extra_data")

            await session.commit()
        except Exception:
            await session.rollback()
            raise
