from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.metric import Metric


class MetricsService(service.SQLAlchemyAsyncRepositoryService[Metric]):
    """Metrics service."""

    async def update_metric_fields(
        self,
        db_session,
        metric_id: str,
        fields_to_update: dict[str, Any],
    ) -> bool:
        """
        Update specific fields for a metric.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_metric_fields] Called with metric_id={metric_id}, fields={list(fields_to_update.keys())}"
        )

        metric = await db_session.get(Metric, metric_id)
        if not metric:
            logger.warning(f"[update_metric_fields] Metric not found: {metric_id}")
            return False

        updated = False
        for field_name, field_value in fields_to_update.items():
            if field_name.startswith("conversation_data."):
                # Handle nested conversation_data fields
                conversation_data_key = field_name.replace("conversation_data.", "")
                if metric.conversation_data is None:
                    metric.conversation_data = {}
                metric.conversation_data[conversation_data_key] = field_value
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(metric, "conversation_data")
                updated = True
            elif field_name.startswith("extra_data."):
                # Handle nested extra_data fields
                extra_data_key = field_name.replace("extra_data.", "")
                if metric.extra_data is None:
                    metric.extra_data = {}
                metric.extra_data[extra_data_key] = field_value
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(metric, "extra_data")
                updated = True
            elif hasattr(metric, field_name):
                # Handle direct fields
                setattr(metric, field_name, field_value)
                updated = True
            else:
                logger.warning(
                    f"[update_metric_fields] Field {field_name} not found on metric model"
                )

        if updated:
            logger.info(
                f"[update_metric_fields] Committing changes for metric {metric_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_metric_fields] No fields were updated for metric {metric_id}"
            )
        return updated

    class Repo(repository.SQLAlchemyAsyncRepository[Metric]):
        """Metrics repository."""

        model_type = Metric

    repository_type = Repo
