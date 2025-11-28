import json

from sqlalchemy import text

from core.config.app import alchemy
from services.common.models import LlmResponseFeedback


async def record_tool_response_feedback(
    *,
    trace_id: str | None,
    analytics_id: str | None,
    feedback: LlmResponseFeedback,
) -> None:
    """Record feedback for a tool response using SQLAlchemy."""
    if not analytics_id:
        return

    async with alchemy.get_session() as session:
        try:
            # Convert feedback to JSON string to ensure proper type handling
            feedback_json = json.dumps(feedback.model_dump())

            # Update the extra_data JSONB field with the feedback information
            sql = """
                UPDATE metrics 
                SET extra_data = COALESCE(extra_data, '{}'::jsonb) || 
                    jsonb_build_object('answer_feedback', CAST(:feedback AS jsonb))
                WHERE id = :analytics_id
            """

            await session.execute(
                text(sql),
                {"analytics_id": analytics_id, "feedback": feedback_json},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def record_tool_response_copy(
    *,
    trace_id: str | None,
    analytics_id: str | None,
) -> None:
    """Record that a tool response was copied using SQLAlchemy."""
    if not analytics_id:
        return

    async with alchemy.get_session() as session:
        try:
            # Update the extra_data JSONB field with the copy flag
            sql = """
                UPDATE metrics 
                SET extra_data = COALESCE(extra_data, '{}'::jsonb) || 
                    jsonb_build_object('answer_copy', true)
                WHERE id = :analytics_id
            """

            await session.execute(text(sql), {"analytics_id": analytics_id})
            await session.commit()
        except Exception:
            await session.rollback()
            raise
