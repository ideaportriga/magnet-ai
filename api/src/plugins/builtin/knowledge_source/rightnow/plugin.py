"""RightNow Knowledge Source Plugin

This is a CLIENT-SPECIFIC plugin that should be moved to a private repository.

To use as external plugin:
1. Move to separate package: magnet-plugins-rightnow
2. Install: pip install magnet-plugins-rightnow
3. Set environment: MAGNET_PLUGINS=magnet_plugins.rightnow
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.rightnow.source import RightNowDataSource
from data_sources.rightnow.utils import get_rightnow_basic_auth
from data_sync.data_processor import DataProcessor

from .processor import RightNowDataProcessor


class RightNowPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing RightNow knowledge base"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="RightNow",
            version="1.0.0",
            author="Client Team",
            description="Synchronizes content from RightNow knowledge base",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "RightNow service URL",
                    },
                    # Provider-level credentials (from provider config)
                    "username": {
                        "type": "string",
                        "description": "RightNow username (from provider)",
                    },
                    "password": {
                        "type": "string",
                        "description": "RightNow password (from provider)",
                    },
                },
                "required": ["endpoint"],
            },
        )

    @property
    def source_type(self) -> str:
        return "RightNow"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create RightNow processor

        Args:
            source_config: Source configuration
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            RightNowDataProcessor instance

        Raises:
            ClientException: If endpoint is missing
        """
        rightnow_url = source_config.get("endpoint")

        if not rightnow_url:
            raise ClientException("Missing `endpoint` in metadata")

        # Get credentials from source_config (merged with provider config)
        username = source_config.get("username")
        password = source_config.get("password")

        # Get authentication with explicit config if provided, otherwise use env
        if username and password:
            from data_sources.rightnow.utils import get_rightnow_basic_auth_with_config
            auth = get_rightnow_basic_auth_with_config(
                username=username,
                password=password,
            )
        else:
            # Fall back to environment-based config for backward compatibility
            auth = get_rightnow_basic_auth()

        # Create data source
        data_source = RightNowDataSource(rightnow_url, auth)

        # Return processor
        return RightNowDataProcessor(data_source)
