from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from advanced_alchemy.filters import BeforeAfter, CollectionFilter
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.jobs.service import (
    JobsService,
)

from .schemas import Job, JobCreate, JobUpdate

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class JobsController(Controller):
    """Jobs CRUD"""

    path = "/jobs"
    tags = ["Admin / Jobs"]

    dependencies = providers.create_service_dependencies(
        JobsService,
        "jobs_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": ["status"],
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            # Sort configuration
            "sort_field": "created_at",  # Default sort field
            "sort_order": "desc",  # Default sort order (newest first)
            # Time-based filters
            "created_at": True,
            "updated_at": True,
        },
    )

    @get()
    async def list_jobs(
        self,
        jobs_service: JobsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        status_in: list[str] | None = Parameter(
            query="statusIn", default=None, required=False
        ),
        type: str | None = Parameter(query="type", default=None, required=False),
        created_at_after: datetime | None = Parameter(
            query="createdAtAfter", default=None, required=False
        ),
        created_at_before: datetime | None = Parameter(
            query="createdAtBefore", default=None, required=False
        ),
        definition_job_type_in: list[str] | None = Parameter(
            query="definition.jobTypeIn", default=None, required=False
        ),
        definition_interval_in: list[str] | None = Parameter(
            query="definition.intervalIn", default=None, required=False
        ),
    ) -> service.OffsetPagination[Job]:
        """List jobs with pagination and filtering."""

        additional_filters = []

        if status_in:
            additional_filters.append(
                CollectionFilter(field_name="status", values=status_in)
            )

        # Add time-based filters for created_at
        if created_at_after or created_at_before:
            additional_filters.append(
                BeforeAfter(
                    field_name="created_at",
                    before=created_at_before,
                    after=created_at_after,
                )
            )

        all_filters = list(filters) + additional_filters

        # Use the service's custom method for JSONB filtering if we have JSONB filters
        if definition_job_type_in or definition_interval_in or type:
            jsonb_filters = {}
            if definition_job_type_in:
                jsonb_filters["job_type"] = definition_job_type_in
            if definition_interval_in:
                jsonb_filters["interval"] = definition_interval_in
            if type:
                jsonb_filters["run_configuration_type"] = [type]

            # Call custom service method for JSONB filtering
            results, total = await jobs_service.list_and_count_with_jsonb_filters(
                *all_filters, jsonb_filters=jsonb_filters
            )

        else:
            # Use standard filtering
            results, total = await jobs_service.list_and_count(*all_filters)

        return jobs_service.to_schema(
            results, total, filters=all_filters, schema_type=Job
        )

    @post()
    async def create_job(self, jobs_service: JobsService, data: JobCreate) -> Job:
        """Create a new job."""
        obj = await jobs_service.create(data)
        return jobs_service.to_schema(obj, schema_type=Job)

    @get("/code/{code:str}")
    async def get_job_by_code(self, jobs_service: JobsService, code: str) -> Job:
        """Get a job by its system_name."""
        obj = await jobs_service.get_one(system_name=code)
        return jobs_service.to_schema(obj, schema_type=Job)

    @get("/{job_id:uuid}")
    async def get_job(
        self,
        jobs_service: JobsService,
        job_id: UUID = Parameter(
            title="Job ID",
            description="The job to retrieve.",
        ),
    ) -> Job:
        """Get a job by its ID."""
        obj = await jobs_service.get(job_id)
        return jobs_service.to_schema(obj, schema_type=Job)

    @patch("/{job_id:uuid}")
    async def update_job(
        self,
        jobs_service: JobsService,
        data: JobUpdate,
        job_id: UUID = Parameter(
            title="Job ID",
            description="The job to update.",
        ),
    ) -> Job:
        """Update a job."""
        obj = await jobs_service.update(data, item_id=job_id, auto_commit=True)
        return jobs_service.to_schema(obj, schema_type=Job)

    @delete("/{job_id:uuid}")
    async def delete_job(
        self,
        jobs_service: JobsService,
        job_id: UUID = Parameter(
            title="Job ID",
            description="The job to delete.",
        ),
    ) -> None:
        """Delete a job from the system."""
        _ = await jobs_service.delete(job_id)
