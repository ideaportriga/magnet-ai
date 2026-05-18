"""Task definitions grouped by domain.

`DISPATCH_TABLE` maps `RunConfigurationType` → `AsyncTaskiqDecoratedTask` and is
used by the admin scheduler routes to pick the right task for a given user
`JobDefinition`.
"""

from __future__ import annotations

from tasks.definitions.background import (
    add_assistant_message_bg_task,
    add_user_message_bg_task,
    api_ingest_bg_task,
    deep_research_bg_task,
    entity_extraction_bg_task,
    note_taker_confluence_publish_bg_task,
    note_taker_kg_ingest_bg_task,
    note_taker_preview_bg_task,
    note_taker_rerun_bg_task,
    note_taker_salesforce_publish_bg_task,
    sync_kg_source_bg_task,
)
from tasks.definitions.custom import custom_function_task
from tasks.definitions.housekeeping import cleanup_logs_task
from tasks.definitions.jobs import evaluate_task, post_process_conversation_task
from tasks.definitions.knowledge_sources import (
    sync_collection_task,
    sync_knowledge_graph_source_task,
)
from tasks.types import RunConfigurationType

DISPATCH_TABLE = {
    RunConfigurationType.CUSTOM: custom_function_task,
    RunConfigurationType.SYNC_COLLECTION: sync_collection_task,
    RunConfigurationType.POST_PROCESS_CONVERSATION: post_process_conversation_task,
    RunConfigurationType.EVALUATION: evaluate_task,
    RunConfigurationType.SYNC_KNOWLEDGE_GRAPH_SOURCE: sync_knowledge_graph_source_task,
    RunConfigurationType.CLEANUP_LOGS: cleanup_logs_task,
}

__all__ = [
    "DISPATCH_TABLE",
    "add_assistant_message_bg_task",
    "add_user_message_bg_task",
    "api_ingest_bg_task",
    "cleanup_logs_task",
    "custom_function_task",
    "deep_research_bg_task",
    "entity_extraction_bg_task",
    "evaluate_task",
    "note_taker_confluence_publish_bg_task",
    "note_taker_kg_ingest_bg_task",
    "note_taker_preview_bg_task",
    "note_taker_rerun_bg_task",
    "note_taker_salesforce_publish_bg_task",
    "post_process_conversation_task",
    "sync_collection_task",
    "sync_kg_source_bg_task",
    "sync_knowledge_graph_source_task",
]
