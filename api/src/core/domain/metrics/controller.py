from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.metrics.service import MetricsService

from .schemas import Metric, MetricCreate, MetricUpdate

if TYPE_CHECKING:
    pass


class MetricsController(Controller):
    """Metrics CRUD"""

    path = "/metrics"
    tags = ["Metrics"]

    dependencies = providers.create_service_dependencies(
        MetricsService,
        "metrics_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "feature_name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_metrics(
        self,
        metrics_service: MetricsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Metric]:
        """List metrics with pagination and filtering."""
        results, total = await metrics_service.list_and_count(*filters)
        return metrics_service.to_schema(
            results, total, filters=filters, schema_type=Metric
        )

    @post()
    async def create_metric(
        self, metrics_service: MetricsService, data: MetricCreate
    ) -> Metric:
        """Create a new metric."""
        obj = await metrics_service.create(data)
        return metrics_service.to_schema(obj, schema_type=Metric)

    @get("/feature/{feature_system_name:str}")
    async def get_metric_by_feature(
        self, metrics_service: MetricsService, feature_system_name: str
    ) -> Metric:
        """Get a metric by its feature system name."""
        obj = await metrics_service.get_one(feature_system_name=feature_system_name)
        return metrics_service.to_schema(obj, schema_type=Metric)

    @get("/trace/{trace_id:str}")
    async def get_metrics_by_trace(
        self,
        metrics_service: MetricsService,
        trace_id: str,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Metric]:
        """Get metrics by trace ID."""
        results, total = await metrics_service.list_and_count(
            *filters, trace_id=trace_id
        )
        return metrics_service.to_schema(
            results, total, filters=filters, schema_type=Metric
        )

    @get("/{metric_id:uuid}")
    async def get_metric(
        self,
        metrics_service: MetricsService,
        metric_id: UUID = Parameter(
            title="Metric ID",
            description="The metric to retrieve.",
        ),
    ) -> Metric:
        """Get a metric by its ID."""
        obj = await metrics_service.get(metric_id)
        return metrics_service.to_schema(obj, schema_type=Metric)

    @patch("/{metric_id:uuid}")
    async def update_metric(
        self,
        metrics_service: MetricsService,
        data: MetricUpdate,
        metric_id: UUID = Parameter(
            title="Metric ID",
            description="The metric to update.",
        ),
    ) -> Metric:
        """Update a metric."""
        obj = await metrics_service.update(data, item_id=metric_id, auto_commit=True)
        return metrics_service.to_schema(obj, schema_type=Metric)

    @delete("/{metric_id:uuid}")
    async def delete_metric(
        self,
        metrics_service: MetricsService,
        metric_id: UUID = Parameter(
            title="Metric ID",
            description="The metric to delete.",
        ),
    ) -> None:
        """Delete a metric from the system."""
        _ = await metrics_service.delete(metric_id)
