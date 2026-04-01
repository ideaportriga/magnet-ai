from logging import getLogger

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = getLogger(__name__)


async def list_evaluations_with_aggregations(
    db_session: AsyncSession,
) -> list[dict]:
    """
    List evaluations with aggregated metrics using raw SQL to match the original MongoDB aggregation.
    """

    # Simplified SQL query that works with PostgreSQL
    sql = """
    WITH evaluation_results AS (
        SELECT 
            e.id,
            e.job_id,
            e.type,
            e.test_sets,
            e.started_at,
            e.status,
            e.errors,
            e.finished_at,
            e.tool,
            -- Extract results array length
            COALESCE(jsonb_array_length(
                CASE 
                    WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                    ELSE '[]'::jsonb
                END
            ), 0) as records_count,
            -- Calculate averages directly from the JSONB array
            (
                SELECT COALESCE(AVG((elem->>'latency')::float), 0)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE (elem->>'latency')::float > 0
            ) as average_latency,
            (
                SELECT COALESCE(AVG((elem->>'score')::float), 0)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE (elem->>'score')::float > 0
            ) as average_score,
            (
                SELECT COALESCE(AVG((elem->'usage'->>'completion_tokens')::float), 0)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE elem->'usage'->>'completion_tokens' IS NOT NULL
            ) as average_completion_tokens,
            (
                SELECT COALESCE(AVG((elem->'usage'->>'prompt_tokens')::float), 0)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE elem->'usage'->>'prompt_tokens' IS NOT NULL
            ) as average_prompt_tokens,
            (
                SELECT COALESCE(AVG((elem->'usage'->>'cached_tokens')::float), 0)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE elem->'usage'->>'cached_tokens' IS NOT NULL
            ) as average_cached_tokens,
            (
                SELECT COUNT(*)
                FROM jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(e.results) = 'array' THEN e.results
                        ELSE '[]'::jsonb
                    END
                ) elem
                WHERE (elem->>'score')::float > 0
            ) as results_with_score
        FROM evaluations e
    )
    SELECT 
        id::text as _id,
        job_id,
        type,
        test_sets,
        started_at,
        status,
        errors,
        finished_at,
        tool,
        average_latency,
        average_score,
        average_completion_tokens,
        average_prompt_tokens,
        average_cached_tokens,
        records_count,
        results_with_score
    FROM evaluation_results
    ORDER BY started_at DESC
    """

    result = await db_session.execute(text(sql))
    entities = []

    for row in result.fetchall():
        entity = {
            "_id": row._id,
            "job_id": row.job_id,
            "type": row.type,
            "test_sets": row.test_sets,
            "started_at": row.started_at,
            "status": row.status,
            "errors": row.errors,
            "finished_at": row.finished_at,
            "tool": row.tool,
            "average_latency": float(row.average_latency or 0),
            "average_score": float(row.average_score or 0),
            "average_completion_tokens": float(row.average_completion_tokens or 0),
            "average_prompt_tokens": float(row.average_prompt_tokens or 0),
            "average_cached_tokens": float(row.average_cached_tokens or 0),
            "records_count": int(row.records_count or 0),
            "results_with_score": int(row.results_with_score or 0),
        }
        entities.append(entity)

    return entities


async def update_evaluation_score(
    db_session: AsyncSession,
    evaluation_id: str,
    result_id: str,
    score: float,
    score_comment: str | None = None,
) -> bool:
    """Update the score for a specific result in an evaluation's results array.

    Uses application-level load-modify-save instead of PG-specific jsonb_set()
    with WITH ORDINALITY for cross-dialect compatibility.
    """
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    from core.db.models.evaluation.evaluation import Evaluation

    evaluation = (
        await db_session.execute(
            select(Evaluation).where(Evaluation.id == UUID(evaluation_id))
        )
    ).scalar_one_or_none()

    if evaluation is None:
        return False

    results = list(evaluation.results or [])
    updated = False
    for r in results:
        if isinstance(r, dict) and r.get("id") == result_id:
            r["score"] = score
            r["score_comment"] = score_comment
            updated = True
            break

    if not updated:
        return False

    evaluation.results = results
    flag_modified(evaluation, "results")
    await db_session.commit()
    return True


async def append_evaluation_results(
    db_session: AsyncSession,
    evaluation_id: str,
    new_results: list[dict],
    errors: list[str] | None = None,
) -> None:
    """Append new results to an evaluation's results array."""
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified

    from core.db.models.evaluation.evaluation import Evaluation

    evaluation = (
        await db_session.execute(
            select(Evaluation).where(Evaluation.id == UUID(evaluation_id))
        )
    ).scalar_one_or_none()

    if evaluation is None:
        return

    evaluation.results = (evaluation.results or []) + new_results
    if errors is not None:
        evaluation.errors = errors
    flag_modified(evaluation, "results")
    await db_session.commit()
