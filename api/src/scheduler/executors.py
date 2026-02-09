"""Job executor functions for the AsyncMQ-based scheduler.

Each task function is decorated with ``@task(queue=<QUEUE>)`` which
registers it in the global ``TASK_REGISTRY``.  The queue is chosen per
workload type so that heavyweight sync tasks don't starve lightweight
evaluations or maintenance work.

Functions receive only ``**kwargs`` – there is no ``ctx`` parameter.
Recurring jobs are handled by AsyncMQ's built-in repeatable scheduler.
"""

from logging import getLogger

from asyncmq.tasks import task

from scheduler.decorators import with_progress_status
from scheduler.settings import (
    QUEUE_DEFAULT,
    QUEUE_EVALUATION,
    QUEUE_MAINTENANCE,
    QUEUE_SYNC,
)
from scheduler.tasks.custom import execute_custom_function_impl
from scheduler.tasks.evaluation import execute_evaluation_impl
from scheduler.tasks.maintenance import (
    execute_cleanup_logs_impl,
    execute_post_process_configuration_impl,
)
from scheduler.tasks.sync import (
    execute_sync_collection_impl,
    execute_sync_knowledge_graph_source_impl,
)
from scheduler.types import RunConfigurationType
from services.observability import observe

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Task functions
# ---------------------------------------------------------------------------


@task(queue=QUEUE_DEFAULT)
@with_progress_status
@observe(name="Custom job", channel="Job")
async def execute_custom_function(**kwargs):
    """Execute a custom function with the given parameters."""
    return await execute_custom_function_impl(**kwargs)


@task(queue=QUEUE_SYNC)
@with_progress_status
@observe(name="Sync knowledge source", channel="Job")
async def execute_sync_collection(**kwargs):
    """Execute a sync collection job with the given parameters."""
    return await execute_sync_collection_impl(**kwargs)


@task(queue=QUEUE_MAINTENANCE)
@with_progress_status
async def execute_post_process_configuration(**kwargs):
    """Execute a post-process configuration job with the given parameters."""
    return await execute_post_process_configuration_impl(**kwargs)


@task(queue=QUEUE_EVALUATION)
@with_progress_status
@observe(name="Evaluation job", channel="Job")
async def execute_evaluation(**kwargs):
    """Execute an evaluation job with the given parameters."""
    return await execute_evaluation_impl(**kwargs)


@task(queue=QUEUE_SYNC)
@with_progress_status
@observe(name="Sync knowledge graph source", channel="Job")
async def execute_sync_knowledge_graph_source(**kwargs):
    """Execute a knowledge graph source sync job."""
    return await execute_sync_knowledge_graph_source_impl(**kwargs)


@task(queue=QUEUE_MAINTENANCE)
@with_progress_status
@observe(name="Cleanup logs", channel="Job")
async def execute_cleanup_logs(**kwargs):
    """Execute a cleanup job to delete old traces and metrics.

    Params:
        retention_days: Number of days to retain logs. Logs older than this will be deleted.
        cleanup_traces: Whether to cleanup traces table (default: True)
        cleanup_metrics: Whether to cleanup metrics table (default: True)
    """
    return await execute_cleanup_logs_impl(**kwargs)


# Mapping of run configuration types to execution functions directly
RUN_CONFIG_HANDLERS = {
    RunConfigurationType.CUSTOM: execute_custom_function,
    RunConfigurationType.SYNC_COLLECTION: execute_sync_collection,
    RunConfigurationType.POST_PROCESS_CONVERSATION: execute_post_process_configuration,
    RunConfigurationType.EVALUATION: execute_evaluation,
    RunConfigurationType.SYNC_KNOWLEDGE_GRAPH_SOURCE: execute_sync_knowledge_graph_source,
    RunConfigurationType.CLEANUP_LOGS: execute_cleanup_logs,
}


# ---------------------------------------------------------------------------
# Populate _TASK_QUEUE_MAP in manager for runtime lookups
# ---------------------------------------------------------------------------


def _register_task_queue_mapping() -> None:
    """Register RunConfigurationType → queue-name map in the manager."""
    from scheduler.manager import _TASK_QUEUE_MAP

    _TASK_QUEUE_MAP.update(
        {
            RunConfigurationType.CUSTOM.value: QUEUE_DEFAULT,
            RunConfigurationType.SYNC_COLLECTION.value: QUEUE_SYNC,
            RunConfigurationType.POST_PROCESS_CONVERSATION.value: QUEUE_MAINTENANCE,
            RunConfigurationType.EVALUATION.value: QUEUE_EVALUATION,
            RunConfigurationType.SYNC_KNOWLEDGE_GRAPH_SOURCE.value: QUEUE_SYNC,
            RunConfigurationType.CLEANUP_LOGS.value: QUEUE_MAINTENANCE,
        }
    )


_register_task_queue_mapping()
