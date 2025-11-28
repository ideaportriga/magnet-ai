"""HubSpot Knowledge Source Plugin

This is a CLIENT-SPECIFIC plugin that should be moved to a private repository.

To use as external plugin:
1. Move to separate package: magnet-plugins-hubspot
2. Install: pip install magnet-plugins-hubspot
3. Set environment: MAGNET_PLUGINS=magnet_plugins.hubspot
"""

from typing import Any, Dict

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.hubspot.source import HubspotDataSource
from data_sync.data_processor import DataProcessor

from .processor import HubspotDataProcessor


class HubspotPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing HubSpot data"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="HubSpot",
            version="1.0.0",
            author="Client Team",
            description="Synchronizes data from HubSpot",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=["hubspot-api-client"],
            config_schema={
                "type": "object",
                "properties": {
                    "chunk_size": {
                        "type": "integer",
                        "description": "Optional chunk size for pagination",
                    },
                    # Provider-level credentials (from provider config)
                    "api_token": {
                        "type": "string",
                        "description": "HubSpot API token (from provider)",
                    },
                },
            },
        )

    @property
    def source_type(self) -> str:
        return "Hubspot"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create HubSpot processor

        Args:
            source_config: Source configuration
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            HubspotDataProcessor instance
        """
        chunk_size = source_config.get("chunk_size")
        api_token = source_config.get("api_token")

        # Create data source with explicit token if provided
        if chunk_size:
            data_source = HubspotDataSource(int(chunk_size), api_token=api_token)
        else:
            data_source = HubspotDataSource(api_token=api_token)

        # Return processor
        return HubspotDataProcessor(data_source)
