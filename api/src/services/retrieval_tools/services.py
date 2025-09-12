import os
from logging import getLogger

from prompt_templates.prompt_templates import transform_to_flat

env = os.environ
logger = getLogger(__name__)


async def get_retrieval_by_system_name_flat(
    system_name: str,
    variant: str | None = None,
) -> dict:
    """Get retrieval tool configuration by system name using SQLAlchemy."""
    try:
        from core.config.app import alchemy
        from core.domain.retrieval_tools.schemas import RetrievalTool
        from core.domain.retrieval_tools.service import RetrievalToolsService

        async with alchemy.get_session() as session:
            service = RetrievalToolsService(session=session)
            retrieval_tool = await service.get_one_or_none(system_name=system_name)

            if not retrieval_tool:
                raise LookupError(
                    f"Retrieval Tool with system name '{system_name}' not found"
                )

            config = service.to_schema(retrieval_tool, schema_type=RetrievalTool)
            return transform_to_flat(config.model_dump(), variant)
    except Exception as e:
        logger.warning("Failed to get retrieval tool: '%s': %s", system_name, e)
        raise
