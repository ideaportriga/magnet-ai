"""SAQ-based scheduler manager.

Provides configuration for the litestar-saq plugin and helpers to retrieve
the SAQ queue at runtime.
"""

from logging import getLogger

from litestar_saq import QueueConfig, SAQConfig, SAQPlugin
from litestar_saq.config import TaskQueues

from core.config.base import get_database_settings
from scheduler.executors import (
    execute_cleanup_logs,
    execute_custom_function,
    execute_evaluation,
    execute_post_process_configuration,
    execute_sync_collection,
    execute_sync_knowledge_graph_source,
)

logger = getLogger(__name__)

# ---------------------------------------------------------------------------
# Queue / SAQ configuration helpers
# ---------------------------------------------------------------------------

QUEUE_NAME = "scheduler"


def _get_postgres_dsn() -> str:
    """Build a ``postgresql://`` DSN suitable for SAQ/psycopg from settings."""
    db_settings = get_database_settings()
    url = db_settings.effective_url

    # SAQ + psycopg3 needs a plain ``postgresql://`` DSN (no async driver prefix)
    for prefix in (
        "postgresql+asyncpg://",
        "postgresql+psycopg2://",
        "postgresql+psycopg://",
    ):
        if url.startswith(prefix):
            return url.replace(prefix, "postgresql://")

    if url.startswith("postgresql://"):
        return url

    raise RuntimeError(
        f"Cannot derive a PostgreSQL DSN for SAQ from DATABASE_URL={url!r}. "
        "Ensure DATABASE_URL points to a PostgreSQL database."
    )


def get_saq_plugin_config() -> SAQPlugin:
    """Create the SAQPlugin instance used by the Litestar application."""
    dsn = _get_postgres_dsn()

    # All task functions that can be enqueued dynamically
    task_functions = [
        execute_custom_function,
        execute_sync_collection,
        execute_post_process_configuration,
        execute_evaluation,
        execute_sync_knowledge_graph_source,
        execute_cleanup_logs,
    ]

    saq_plugin = SAQPlugin(
        config=SAQConfig(
            use_server_lifespan=True,
            queue_configs=[
                QueueConfig(
                    dsn=dsn,
                    name=QUEUE_NAME,
                    tasks=task_functions,
                    concurrency=10,
                    separate_process=False,
                ),
            ],
        ),
    )
    return saq_plugin


def get_queue(task_queues: TaskQueues):
    """Retrieve the scheduler queue from the ``TaskQueues`` dependency."""
    return task_queues.get(QUEUE_NAME)
