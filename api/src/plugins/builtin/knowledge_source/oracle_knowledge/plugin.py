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
from data_sources.oracle_knowledge.utils import (
    create_oracle_knowledge_client,
    create_oracle_knowledge_client_with_config,
)
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
                    "endpoint": {
                        "type": "string",
                        "description": "Oracle Knowledge base URL",
                    },
                    # Provider-level credentials (from provider config)
                    "username": {
                        "type": "string",
                        "description": "Oracle Knowledge username (from provider)",
                    },
                    "password": {
                        "type": "string",
                        "description": "Oracle Knowledge password (from provider)",
                    },
                },
                "required": ["endpoint"],
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
            ClientException: If endpoint is missing
        """
        oracle_knowledge_url = source_config.get("endpoint")

        if not oracle_knowledge_url:
            raise ClientException("Missing `endpoint` in metadata")

        # Get credentials from source_config (merged with provider config)
        username = source_config.get("username")
        password = source_config.get("password")

        # Create client with explicit config if provided, otherwise use env
        if username and password:
            client = create_oracle_knowledge_client_with_config(
                oracle_knowledge_url=oracle_knowledge_url,
                username=username,
                password=password,
            )
        else:
            # Fall back to environment-based config for backward compatibility
            client = create_oracle_knowledge_client(oracle_knowledge_url)

        # Create data source
        data_source = OracleKnowledgeDataSource(client)

        # Return processor
        return OracleKnowledgeDataProcessor(data_source)
