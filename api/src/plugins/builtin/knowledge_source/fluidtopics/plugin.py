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

        # Create data source
        data_source = FluidTopicsDataSource(filters)

        # Return processor
        return FluidTopicsDataProcessor(data_source, collection_config)
