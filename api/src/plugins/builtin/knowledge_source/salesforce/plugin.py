"""Salesforce Knowledge Source Plugin

This is a CLIENT-SPECIFIC plugin that should be moved to a private repository.
Synchronizes data from Salesforce objects.

To use as external plugin:
1. Move to separate package: magnet-plugins-salesforce
2. Install: pip install magnet-plugins-salesforce
3. Set environment: MAGNET_PLUGINS=magnet_plugins.salesforce
"""

from json import loads
from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.salesforce.source import SalesforceDataSource
from data_sources.salesforce.utils import create_salesforce_instance
from data_sync.data_processor import DataProcessor

from .processor import SalesforceDataProcessor


class SalesforcePlugin(KnowledgeSourcePlugin):
    """Plugin for syncing Salesforce objects"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Salesforce",
            version="1.0.0",
            author="Client Team",
            description="Synchronizes data from Salesforce objects",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=["simple-salesforce"],
            config_schema={
                "type": "object",
                "properties": {
                    "object_api_name": {
                        "type": "string",
                        "description": "Salesforce object API name",
                    },
                    "output_config": {
                        "type": "string",
                        "description": "JSON configuration for output format",
                    },
                },
                "required": ["object_api_name", "output_config"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Salesforce"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create Salesforce processor

        Args:
            source_config: Source configuration containing Salesforce settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            SalesforceDataProcessor instance

        Raises:
            ClientException: If required fields are missing
        """
        object_api_name = source_config.get("object_api_name")
        output_config_json = source_config.get("output_config")

        if not object_api_name:
            raise ClientException("Missing `object_api_name` in metadata")
        if not output_config_json:
            raise ClientException("Missing `output_config` in metadata")

        # Parse output config
        output_config = loads(output_config_json)

        # Create Salesforce instance
        salesforce = create_salesforce_instance()

        # Create data source
        data_source = SalesforceDataSource(
            salesforce, object_api_name, output_config
        )

        # Return processor
        return SalesforceDataProcessor(data_source, output_config)
