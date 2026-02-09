import traceback
from logging import getLogger
from uuid import UUID

from services.observability import observability_context
from services.observability.models import FeatureType

logger = getLogger(__name__)


async def execute_sync_collection_impl(**kwargs):
    job_id = kwargs.get("job_id")

    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type=FeatureType.KNOWLEDGE_SOURCE.value,
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        system_name = params.get("system_name")

        if not system_name:
            logger.error(f"Missing system_name parameter for job {job_id}")
            return False

        from services.utils.get_ids_by_system_names import get_ids_by_system_names

        collection_id = await get_ids_by_system_names(system_name, "collections")
        if not collection_id:
            logger.error(
                f"Collection not found for system_name '{system_name}' in job {job_id}"
            )
            return False

        if isinstance(collection_id, list):
            if collection_id:
                collection_id = collection_id[0]
            else:
                logger.error(
                    f"Empty collection_id list for system_name '{system_name}' in job {job_id}"
                )
                return False

        from routes.admin.knowledge_sources import sync_collection_standalone

        result = await sync_collection_standalone(collection_id)

        if not result:
            logger.warning(
                f"Sync collection returned False for collection_id '{collection_id}' in job {job_id}"
            )
            return False

        logger.info(f"Successfully completed sync collection for job {job_id}")
        return True

    except Exception as e:
        logger.error(f"Error in execute_sync_collection for job {job_id}: {str(e)}")
        traceback.print_exc()

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "params": params,
            },
        )
        raise


async def execute_sync_knowledge_graph_source_impl(**kwargs):
    job_id = kwargs.get("job_id")

    try:
        job_definition = kwargs.get("job_definition")
        params = kwargs.get("params", {})

        observability_context.update_current_trace(
            type="sync_knowledge_graph_source",
            extra_data={
                "job_id": job_id,
                "job_definition": job_definition,
                "params": params,
            },
        )

        graph_id = params.get("graph_id")
        source_id = params.get("source_id")

        if not graph_id or not source_id:
            logger.error(f"Missing graph_id or source_id for job {job_id}")
            return False

        from core.config.app import alchemy
        from core.domain.knowledge_graph.service import KnowledgeGraphSourceService

        async with alchemy.get_session() as session:
            service = KnowledgeGraphSourceService(session=session)
            await service.sync_source(
                session, UUID(str(graph_id)), UUID(str(source_id))
            )

        logger.info(
            f"Successfully started sync for graph {graph_id} source {source_id} in job {job_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error in execute_sync_knowledge_graph_source for job {job_id}: {str(e)}"
        )
        traceback.print_exc()

        observability_context.update_current_trace(
            extra_data={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "params": params,
            },
        )
        raise
