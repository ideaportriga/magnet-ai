"""Oracle Knowledge Plugin

This is a CLIENT-SPECIFIC plugin that should be moved to a private repository.
Synchronizes content from Oracle Knowledge base.

To use as external plugin:
1. Move to separate package: magnet-plugins-oracle-knowledge
2. Install: pip install magnet-plugins-oracle-knowledge
3. Set environment: MAGNET_PLUGINS=magnet_plugins.oracle_knowledge
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.oracle_knowledge.source import OracleKnowledgeDataSource
from data_sources.oracle_knowledge.utils import create_oracle_knowledge_client
from data_sync.data_processor import DataProcessor

from .processor import OracleKnowledgeDataProcessor


class OracleKnowledgePlugin(KnowledgeSourcePlugin):
    """Plugin for syncing Oracle Knowledge base"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Oracle Knowledge",
            version="1.0.0",
            author="Client Team",
            description="Synchronizes content from Oracle Knowledge base",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "oracle_knowledge_url": {
                        "type": "string",
                        "description": "Oracle Knowledge base URL",
                    },
                },
                "required": ["oracle_knowledge_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Oracle Knowledge"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create Oracle Knowledge processor

        Args:
            source_config: Source configuration
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            OracleKnowledgeDataProcessor instance

        Raises:
            ClientException: If oracle_knowledge_url is missing
        """
        oracle_knowledge_url = source_config.get("oracle_knowledge_url")

        if not oracle_knowledge_url:
            raise ClientException("Missing `oracle_knowledge_url` in metadata")

        # Create client
        client = create_oracle_knowledge_client(oracle_knowledge_url)

        # Create data source
        data_source = OracleKnowledgeDataSource(client)

        # Return processor
        return OracleKnowledgeDataProcessor(data_source)
