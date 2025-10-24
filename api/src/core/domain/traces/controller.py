from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from advanced_alchemy.filters import BeforeAfter, CollectionFilter
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.domain.traces.service import TracesService

from .schemas import Trace, TraceCreate, TraceUpdate

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class TracesController(Controller):
    """Traces CRUD"""

    path = "/traces"
    tags = ["traces"]

    dependencies = providers.create_service_dependencies(
        TracesService,
        "traces_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": str,
            "id_field": "id",
            "search": [
                "name",
                "source",
                "channel",
                "user_id",
            ],
            "search_ignore_case": True,
            "pagination_size": 10,
            # Sort configuration
            "sort_field": "created_at",  # Default sort field
            "sort_order": "desc",  # Default sort order (newest first)
            # Time-based filters
            "created_at": True,
            "updated_at": True,
            "in_fields": [
                providers.FieldNameType("type", str),
            ],
        },
    )

    @get()
    async def list_traces(
        self,
        traces_service: TracesService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        status_in: list[str] | None = Parameter(
            query="statusIn", default=None, required=False
        ),
        channel_in: list[str] | None = Parameter(
            query="channelIn", default=None, required=False
        ),
        source_in: list[str] | None = Parameter(
            query="sourceIn", default=None, required=False
        ),
        name_in: list[str] | None = Parameter(
            query="nameIn", default=None, required=False
        ),
        start_time_after: datetime | None = Parameter(
            query="startTimeAfter", default=None, required=False
        ),
        start_time_before: datetime | None = Parameter(
            query="startTimeBefore", default=None, required=False
        ),
        end_time_after: datetime | None = Parameter(
            query="endTimeAfter", default=None, required=False
        ),
        end_time_before: datetime | None = Parameter(
            query="endTimeBefore", default=None, required=False
        ),
        system_name_in: list[str] | None = Parameter(
            query="system_name_in", default=None, required=False
        ),
    ) -> service.OffsetPagination[Trace]:
        """List traces with pagination and filtering."""

        additional_filters = []

        if status_in:
            additional_filters.append(
                CollectionFilter(field_name="status", values=status_in)
            )

        if channel_in:
            additional_filters.append(
                CollectionFilter(field_name="channel", values=channel_in)
            )

        if source_in:
            additional_filters.append(
                CollectionFilter(field_name="source", values=source_in)
            )

        if name_in:
            additional_filters.append(
                CollectionFilter(field_name="name", values=name_in)
            )

        # Add time-based filters
        if start_time_after or start_time_before:
            additional_filters.append(
                BeforeAfter(
                    field_name="start_time",
                    before=start_time_before,
                    after=start_time_after,
                )
            )

        if end_time_after or end_time_before:
            additional_filters.append(
                BeforeAfter(
                    field_name="end_time",
                    before=end_time_before,
                    after=end_time_after,
                )
            )

        all_filters = list(filters) + additional_filters

        # Prepare JSONB filters if any
        jsonb_filters = {}
        if system_name_in:
            jsonb_filters["system_name"] = system_name_in

        # Use the enhanced service method that handles both standard and JSONB filtering
        results, total = await traces_service.list_and_count_with_jsonb_filters(
            *all_filters, jsonb_filters=jsonb_filters
        )

        return traces_service.to_schema(
            results, total, filters=all_filters, schema_type=Trace
        )

    @post()
    async def create_trace(
        self, traces_service: TracesService, data: TraceCreate
    ) -> Trace:
        """Create a new trace."""
        obj = await traces_service.create(data)
        return traces_service.to_schema(obj, schema_type=Trace)

    @get("/name/{name:str}")
    async def get_trace_by_name(
        self, traces_service: TracesService, name: str
    ) -> Trace:
        """Get a trace by its name."""
        obj = await traces_service.get_one(name=name)
        return traces_service.to_schema(obj, schema_type=Trace)

    @get("/{trace_id:uuid}")
    async def get_trace(
        self,
        traces_service: TracesService,
        trace_id: UUID = Parameter(
            title="Trace ID",
            description="The trace to retrieve.",
        ),
    ) -> Trace:
        """Get a trace by its ID."""
        obj = await traces_service.get(trace_id)
        return traces_service.to_schema(obj, schema_type=Trace)

    @patch("/{trace_id:uuid}")
    async def update_trace(
        self,
        traces_service: TracesService,
        data: TraceUpdate,
        trace_id: UUID = Parameter(
            title="Trace ID",
            description="The trace to update.",
        ),
    ) -> Trace:
        """Update a trace."""
        obj = await traces_service.update(data, item_id=trace_id, auto_commit=True)
        return traces_service.to_schema(obj, schema_type=Trace)

    @delete("/{trace_id:uuid}")
    async def delete_trace(
        self,
        traces_service: TracesService,
        trace_id: UUID = Parameter(
            title="Trace ID",
            description="The trace to delete.",
        ),
    ) -> None:
        """Delete a trace from the system."""
        _ = await traces_service.delete(trace_id)
