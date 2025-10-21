"""Fluid Topics Knowledge Source Plugin

Synchronizes content from Fluid Topics platform.
"""

from json import loads
from typing import Any, Dict

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.fluid_topics.source import FluidTopicsDataSource
from data_sync.data_processor import DataProcessor
from data_sync.processors.fluidtopics_data_processor import FluidTopicsDataProcessor


class FluidTopicsPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing Fluid Topics content"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Fluid Topics",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes content from Fluid Topics platform",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "fluid_topics_search_filters": {
                        "type": "string",
                        "description": "JSON string of search filters",
                    },
                    # Provider-level credentials (from provider config)
                    "api_key": {
                        "type": "string",
                        "description": "Fluid Topics API key (from provider)",
                    },
                    "search_api_url": {
                        "type": "string",
                        "description": "Fluid Topics Search API URL (from provider)",
                    },
                    "pdf_api_url": {
                        "type": "string",
                        "description": "Fluid Topics PDF API URL (from provider)",
                    },
                },
            },
        )

    @property
    def source_type(self) -> str:
        return "Fluid Topics"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create Fluid Topics processor

        Args:
            source_config: Source configuration containing Fluid Topics settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            FluidTopicsDataProcessor instance
        """
        # Parse filters from JSON string
        filters = source_config.get("fluid_topics_search_filters")
        filters = loads(filters) if filters else []

        # Get API configuration from source_config (merged with provider config)
        api_key = source_config.get("api_key")
        search_api_url = source_config.get("search_api_url")
        pdf_api_url = source_config.get("pdf_api_url")

        # Create data source with explicit config if provided
        data_source = FluidTopicsDataSource(
            filters=filters,
            api_key=api_key,
            search_api_url=search_api_url,
            pdf_api_url=pdf_api_url,
        )

        # Return processor
        return FluidTopicsDataProcessor(data_source, collection_config)
