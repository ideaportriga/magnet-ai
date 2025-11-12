"""Confluence Knowledge Source Plugin

Synchronizes pages from Confluence spaces.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.confluence.source import ConfluenceDataSource
from data_sources.confluence.utils import (
    create_confluence_instance,
    create_confluence_instance_with_config,
)
from data_sync.data_processor import DataProcessor

from .processor import ConfluenceDataProcessor


class ConfluencePlugin(KnowledgeSourcePlugin):
    """Plugin for syncing Confluence spaces"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Confluence",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes pages from Confluence spaces",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "Confluence instance URL",
                    },
                    "confluence_space": {
                        "type": "string",
                        "description": "Confluence space key",
                    },
                    # Provider-level credentials (from provider config)
                    "username": {
                        "type": "string",
                        "description": "Confluence username (from provider)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Confluence API token (from provider)",
                    },
                },
                "required": ["endpoint", "confluence_space"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Confluence"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create Confluence processor

        Args:
            source_config: Source configuration containing Confluence settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            ConfluenceDataProcessor instance

        Raises:
            ClientException: If required fields are missing
        """
        confluence_url = source_config.get("endpoint")
        confluence_space = source_config.get("confluence_space")

        if not confluence_url:
            raise ClientException(
                "Missing `endpoint` configuration. Please ensure the provider is configured "
                "with a valid Confluence endpoint URL"
            )
        if not confluence_space:
            raise ClientException(
                "Missing `confluence_space` configuration. Please specify the Confluence space "
                "in the knowledge source settings"
            )

        # Get credentials from source_config (merged with provider config)
        username = source_config.get("username")
        token = source_config.get("token")

        # Create Confluence instance with explicit config if provided, otherwise use env
        if username and token:
            confluence_instance = create_confluence_instance_with_config(
                url=confluence_url,
                username=username,
                token=token,
            )
        else:
            # Fall back to environment-based config for backward compatibility
            confluence_instance = create_confluence_instance(confluence_url)

        # Create data source
        data_source = ConfluenceDataSource(confluence_instance, confluence_space)

        # Return processor
        return ConfluenceDataProcessor(data_source)
