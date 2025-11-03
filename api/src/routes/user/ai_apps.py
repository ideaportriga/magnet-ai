import logging
from typing import Annotated, Any

from litestar import Controller, get
from litestar.exceptions import InternalServerException, NotFoundException
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from api.tags import TagNames
from core.domain.ai_apps.service import AiAppsService
from core.domain.ai_apps.schemas import AiApp
from core.domain.rag_tools.service import RagToolsService
from core.domain.rag_tools.schemas import RagTool
from core.domain.retrieval_tools.service import RetrievalToolsService
from core.domain.retrieval_tools.schemas import RetrievalTool
from core.domain.agents.service import AgentsService
from core.domain.agents.schemas import Agent

# Configure logger
logger = logging.getLogger(__name__)


def filter_keys(document: dict[str, Any], allowed_keys: list[str]) -> dict[str, Any]:
    """Filter dictionary to only include specified keys."""
    return {key: document[key] for key in allowed_keys if key in document}


def convert_object_id(document: dict[str, Any]) -> dict[str, Any]:
    """Convert MongoDB ObjectId to string representation (deprecated - keeping for compatibility)."""
    # This function is kept for backward compatibility but is no longer needed
    # since SQLAlchemy models already use UUID strings
    return document


def get_active_variant(config: dict[str, Any]) -> dict[str, Any] | None:
    """Extract active variant from configuration."""
    active_variant_name = config.get("active_variant")
    variants = config.get("variants", [])

    if not active_variant_name:
        return None

    for variant in variants:
        if variant.get("variant") == active_variant_name:
            return variant

    return None


def transform_rag_tool(config: dict[str, Any]) -> dict[str, Any]:
    """Transform RAG tool configuration for client consumption."""
    config_copy = config.copy()
    active_variant = get_active_variant(config_copy)

    if active_variant:
        config_copy["active_variant"] = filter_keys(active_variant, ["ui_settings"])

    return filter_keys(config_copy, ["active_variant", "name"])


def transform_retrieval_tool(config: dict[str, Any]) -> dict[str, Any]:
    """Transform retrieval tool configuration for client consumption."""
    return filter_keys(config, ["ui_settings", "name"])


def transform_agent(config: dict[str, Any]) -> dict[str, Any]:
    """Transform agent configuration for client consumption."""
    config_copy = config.copy()
    active_variant = get_active_variant(config_copy)

    transformed = filter_keys(config_copy, ["name", "channels"])
    if active_variant:
        transformed["settings"] = active_variant.get("value", {}).get("settings", {})

    return transformed


class UserAiAppsController(Controller):
    tags = [TagNames.UserAiApps]
    path = "/ai_apps"

    @get(
        "/{system_name:str}",
        summary="Retrieve AI App",
        description="Retrieves the configuration of a specific AI App by its system name.",
    )
    async def get_entity_by_system_name(
        self,
        db_session: AsyncSession,
        system_name: Annotated[
            str,
            Parameter(
                description="Unique AI app system name.",
            ),
        ],
    ) -> dict[str, Any]:
        try:
            ai_apps_service = AiAppsService(session=db_session)
            ai_app = await ai_apps_service.get_one_or_none(system_name=system_name)

            if not ai_app:
                raise NotFoundException(
                    f"Entity with system_name '{system_name}' not found",
                )

            # Convert to schema and then to dict
            ai_app_schema = ai_apps_service.to_schema(ai_app, schema_type=AiApp)
            entity = ai_app_schema.model_dump()
            
            tabs: list[dict[str, Any]] = entity.get("tabs", [])

            await self._process_tabs(tabs, db_session)

            return entity
        except Exception as e:
            if not isinstance(e, NotFoundException):
                logger.exception(
                    f"Error processing panel for system_name '{system_name}'",
                )
                raise InternalServerException(f"Failed to process entity: {e!s}")
            raise

    @get(
        "/agents/{system_name:str}",
        summary="Retrieve Agent",
        description="Retrieves the configuration of a specific Agent by its system name.",
    )
    async def get_agent_by_system_name(
        self,
        db_session: AsyncSession,
        system_name: Annotated[
            str,
            Parameter(
                description="Unique Agent system name.",
            ),
        ],
    ) -> dict[str, Any]:
        try:
            imitate_tab = {
                "name": "Agent",
                "config": {
                    "agent": system_name
                }
            }
            agent_settings = await self._get_agent_config(imitate_tab, db_session)
            
            if agent_settings:
                imitate_tab["entityObject"] = agent_settings
                return imitate_tab
            else:
                raise NotFoundException(f"Agent with system_name '{system_name}' not found")
        except Exception as e:
            logger.exception(f"Error retrieving agent '{system_name}': {e!s}")
            raise InternalServerException(f"Failed to retrieve agent: {e!s}") from e

    async def _process_tabs(self, tabs: list[dict[str, Any]], db_session: AsyncSession) -> None:
        """Process tabs recursively to enrich with entity objects.

        Args:
            tabs: List of tab configurations
            db_session: Database session instance

        """
        for tab in tabs:
            tab_type = tab.get("tab_type")
            config = None

            try:
                if tab_type == "RAG":
                    config = await self._get_rag_config(tab, db_session)
                elif tab_type == "Retrieval":
                    config = await self._get_retrieval_config(tab, db_session)
                elif tab_type == "Agent":
                    config = await self._get_agent_config(tab, db_session)

                if config:
                    tab["entityObject"] = {**convert_object_id(config)}

                # Process nested tabs in groups
                if tab_type == "Group" and "children" in tab:
                    await self._process_tabs(tab["children"], db_session)
            except Exception as e:
                logger.error(f"Error processing tab '{tab_type}': {e!s}")

    async def _get_rag_config(
        self,
        tab: dict[str, Any],
        db_session: AsyncSession,
    ) -> dict[str, Any] | None:
        """Get and transform RAG tool configuration."""
        system_name = tab.get("config", {}).get("rag_tool")
        if not system_name:
            return None

        service = RagToolsService(session=db_session)
        rag_tool = await service.get_one_or_none(system_name=system_name)
        
        if rag_tool:
            rag_tool_schema = service.to_schema(rag_tool, schema_type=RagTool)
            config = rag_tool_schema.model_dump()
            return transform_rag_tool(config)
        return None

    async def _get_retrieval_config(
        self,
        tab: dict[str, Any],
        db_session: AsyncSession,
    ) -> dict[str, Any] | None:
        """Get and transform retrieval tool configuration."""
        system_name = tab.get("config", {}).get("retrieval_tool")
        if not system_name:
            return None

        service = RetrievalToolsService(session=db_session)
        retrieval_tool = await service.get_one_or_none(system_name=system_name)
        
        if retrieval_tool:
            retrieval_tool_schema = service.to_schema(retrieval_tool, schema_type=RetrievalTool)
            config = retrieval_tool_schema.model_dump()
            return transform_retrieval_tool(config)
        return None

    async def _get_agent_config(
        self,
        tab: dict[str, Any],
        db_session: AsyncSession,
    ) -> dict[str, Any] | None:
        """Get and transform agent configuration."""
        system_name = tab.get("config", {}).get("agent")
        if not system_name:
            return None
        service = AgentsService(session=db_session)
        agent = await service.get_one_or_none(system_name=system_name)
        
        if agent:
            logger.debug(f"Agent configuration found: {system_name}")
            agent_schema = service.to_schema(agent, schema_type=Agent)
            config = agent_schema.model_dump()
            return transform_agent(config)
        return None
