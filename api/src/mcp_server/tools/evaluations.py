"""MCP tools: evaluation sets and evaluation job management.

Five tools:
  1. evaluation_sets_list   — paginated list of evaluation sets (lightweight)
  2. evaluation_set_get     — one evaluation set with all test items
  3. evaluation_set_create  — create a new evaluation set
  4. evaluations_list       — paginated list of past evaluation runs with results
  5. evaluation_run         — fire a background evaluation job (returns immediately)
"""

from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field

from core.config.app import alchemy
from core.domain.evaluation_sets.schemas import EvaluationSetCreate
from core.domain.evaluation_sets.service import EvaluationSetsService
from prompt_templates.prompt_templates import get_prompt_template_by_system_name
from routes.admin.evaluation_scheduler import EvaluationConfig
from services.evaluation.services import list_evaluations_with_aggregations
from tasks.admin_ops import create_or_update_job
from tasks.types import JobDefinition, JobType, RunConfiguration, RunConfigurationType

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class EvaluationSetSummaryOut(BaseModel):
    """Lightweight evaluation set entry."""

    name: str
    system_name: str
    description: Optional[str] = None
    type: Optional[str] = Field(None, description="E.g. 'prompt_eval', 'rag_eval'")
    item_count: int = Field(0, description="Number of test items in this set")


class EvaluationItemOut(BaseModel):
    """One test item in an evaluation set."""

    user_input: str = Field(description="Input sent to the prompt template")
    expected_result: str = Field(description="Expected / reference output")


class EvaluationSetDetailOut(BaseModel):
    """Full evaluation set including all test items."""

    name: str
    system_name: str
    description: Optional[str] = None
    type: Optional[str] = None
    items: list[EvaluationItemOut] = Field(default_factory=list)


class EvaluationItemIn(BaseModel):
    """One test item for creating an evaluation set."""

    user_input: str = Field(description="Input to send to the prompt template")
    expected_result: str = Field(description="Expected / reference output")


class EvaluationSummaryOut(BaseModel):
    """Aggregated result of one evaluation run."""

    id: str
    tool_system_name: Optional[str] = Field(
        None, description="Prompt template system_name that was evaluated"
    )
    tool_variant: Optional[str] = None
    status: Optional[str] = Field(
        None, description="'in_progress' | 'completed' | 'failed'"
    )
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    records_count: int = Field(0, description="Number of test items evaluated")
    average_score: float = Field(0.0, description="Average score across all results")
    average_latency: float = Field(0.0, description="Average latency in milliseconds")
    test_sets: Optional[list[str]] = Field(
        None, description="Evaluation set names used"
    )


class EvaluationRunStartedOut(BaseModel):
    """Confirmation that a background evaluation job was created."""

    status: str = Field(
        "started", description="Always 'started' — job runs in background"
    )
    job_details: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Job creation details returned by the task broker. "
            "Use evaluations_list to track results once the job completes."
        ),
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def evaluation_sets_list(
    limit: Annotated[int, Field(ge=1, le=200, description="Max sets to return")] = 20,
    offset: Annotated[int, Field(ge=0, description="Sets to skip for pagination")] = 0,
) -> list[EvaluationSetSummaryOut]:
    """List evaluation sets with name, system_name, description, type, and item count.

    Use this to discover existing evaluation sets before running an evaluation
    or fetching a set's test items with ``evaluation_set_get``.
    """
    async with alchemy.get_session() as session:
        service = EvaluationSetsService(session=session)
        results = await service.list()

    page = results[offset : offset + limit]

    return [
        EvaluationSetSummaryOut(
            name=r.name,
            system_name=r.system_name,
            description=r.description,
            type=r.type,
            item_count=len(r.items) if r.items else 0,
        )
        for r in page
    ]


async def evaluation_set_get(system_name: str) -> EvaluationSetDetailOut:
    """Get a single evaluation set by its system_name, including all test items.

    Each item contains a ``user_input`` (sent to the prompt template) and an
    ``expected_result`` (reference output for scoring).
    """
    async with alchemy.get_session() as session:
        service = EvaluationSetsService(session=session)
        record = await service.get_one_or_none(system_name=system_name)

    if record is None:
        raise ValueError(f"Evaluation set {system_name!r} not found")

    items = [
        EvaluationItemOut(
            user_input=item.get("user_input", ""),
            expected_result=item.get("expected_result", ""),
        )
        for item in (record.items or [])
    ]

    return EvaluationSetDetailOut(
        name=record.name,
        system_name=record.system_name,
        description=record.description,
        type=record.type,
        items=items,
    )


async def evaluation_set_create(
    name: str,
    items: list[EvaluationItemIn],
    description: Optional[str] = None,
    type: Annotated[
        Optional[str],
        Field(description="Evaluation set type, e.g. 'prompt_eval'"),
    ] = None,
    system_name: Annotated[
        Optional[str],
        Field(
            description=(
                "Unique identifier for the evaluation set used in API calls. "
                "Auto-generated from ``name`` (uppercased, spaces replaced with underscores) "
                "if not provided."
            )
        ),
    ] = None,
) -> EvaluationSetSummaryOut:
    """Create a new evaluation set with test items.

    Each item must have a ``user_input`` (the query sent to the prompt template)
    and an ``expected_result`` (the reference answer used for scoring).

    Returns the created evaluation set summary including its ``system_name``,
    which you will need when running an evaluation with ``evaluation_run``.
    """
    import re

    resolved_system_name = system_name or re.sub(
        r"[^A-Z0-9_]", "_", name.upper().strip()
    )

    async with alchemy.get_session() as session:
        service = EvaluationSetsService(session=session)
        data = EvaluationSetCreate(
            name=name,
            system_name=resolved_system_name,
            description=description,
            type=type,
            items=[item.model_dump() for item in items],
        )
        record = await service.create(data, auto_commit=True)

    return EvaluationSetSummaryOut(
        name=record.name,
        system_name=record.system_name,
        description=record.description,
        type=record.type,
        item_count=len(record.items) if record.items else 0,
    )


async def evaluations_list(
    template_system_name: Optional[str] = None,
    limit: Annotated[int, Field(ge=1, le=200, description="Max runs to return")] = 20,
    offset: Annotated[int, Field(ge=0, description="Runs to skip for pagination")] = 0,
) -> list[EvaluationSummaryOut]:
    """List past evaluation runs with aggregated results.

    Each entry shows status, avg score, avg latency, and number of records
    evaluated. Filter by ``template_system_name`` to see runs for a specific
    prompt template.

    Results are ordered most recent first.
    """
    async with alchemy.get_session() as session:
        all_rows = await list_evaluations_with_aggregations(session)

    if template_system_name:
        all_rows = [
            r
            for r in all_rows
            if (r.get("tool") or {}).get("system_name") == template_system_name
        ]

    page = all_rows[offset : offset + limit]

    return [
        EvaluationSummaryOut(
            id=row.get("_id", ""),
            tool_system_name=(row.get("tool") or {}).get("system_name"),
            tool_variant=(row.get("tool") or {}).get("variant_name"),
            status=row.get("status"),
            started_at=row.get("started_at"),
            finished_at=row.get("finished_at"),
            records_count=row.get("records_count", 0),
            average_score=row.get("average_score", 0.0),
            average_latency=row.get("average_latency", 0.0),
            test_sets=row.get("test_sets"),
        )
        for row in page
    ]


async def evaluation_run(
    name: str,
    template_system_name: str,
    evaluation_set_system_names: list[str],
    variants: Annotated[
        Optional[list[str]],
        Field(
            description=(
                "Variant names to evaluate. Defaults to the template's active variant. "
                "Each variant is evaluated against all evaluation sets."
            )
        ),
    ] = None,
    iteration_count: Annotated[
        int,
        Field(ge=1, description="How many times to run each test item per variant"),
    ] = 1,
) -> EvaluationRunStartedOut:
    """Fire a background evaluation job for a prompt template.

    The job runs the template against all items in the specified evaluation
    sets, once per variant per iteration. Returns immediately with job details
    — the job continues in the background. Use ``evaluations_list`` to check
    results after the job completes.

    Note: each call incurs real LLM cost proportional to
    (items × variants × iteration_count).
    """
    resolved_variants = variants
    if not resolved_variants:
        try:
            raw = await get_prompt_template_by_system_name(template_system_name)
            active = raw.get("active_variant", "default")
            resolved_variants = [active] if active else ["default"]
        except LookupError:
            resolved_variants = ["default"]

    evaluation_params = {
        "type": "prompt_eval",
        "iteration_count": iteration_count,
        "config": [
            EvaluationConfig(
                system_name=template_system_name,
                test_set_system_names=evaluation_set_system_names,
                variants=resolved_variants,
            ).model_dump()
        ],
        "result_entity": "evaluations",
    }

    job_definition = JobDefinition(
        name=name,
        job_type=JobType.ONE_TIME_IMMEDIATE,
        run_configuration=RunConfiguration(
            type=RunConfigurationType.EVALUATION,
            params=evaluation_params,
        ),
        job_id=None,
        interval=None,
        notification_email=None,
        cron=None,
        scheduled_start_time=None,
        status=None,
        timezone=None,
    )

    async with alchemy.get_session() as session:
        result = await create_or_update_job(job_definition, session)

    logger.info("MCP evaluation_run: job created for template=%s", template_system_name)
    return EvaluationRunStartedOut(
        status="started",
        job_details=result if isinstance(result, dict) else None,
    )
