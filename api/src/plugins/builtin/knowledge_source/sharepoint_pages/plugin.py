"""SharePoint Pages Knowledge Source Plugin

Synchronizes SharePoint pages (wiki pages, modern pages).
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.sharepoint.source_pages import SharePointPagesDataSource
from data_sources.sharepoint.utils import create_sharepoint_client
from data_sync.data_processor import DataProcessor

from .pages_processor import SharepointPagesDataProcessor


class SharePointPagesPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing SharePoint pages"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="SharePoint Pages",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes SharePoint pages (wiki and modern pages)",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "sharepoint_site_url": {
                        "type": "string",
                        "description": "SharePoint site URL",
                    },
                    "sharepoint_pages_page_name": {
                        "type": "string",
                        "description": "Specific page name to sync (optional)",
                    },
                    "sharepoint_pages_embed_title": {
                        "type": "boolean",
                        "description": "Whether to embed page title in content",
                        "default": False,
                    },
                },
                "required": ["sharepoint_site_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Sharepoint Pages"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create SharePoint pages processor

        Args:
            source_config: Source configuration containing SharePoint settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            SharepointPagesDataProcessor instance

        Raises:
            ClientException: If sharepoint_site_url is missing
        """
        sharepoint_site_url = source_config.get("sharepoint_site_url")

        if not sharepoint_site_url:
            raise ClientException("Missing `sharepoint_site_url` in metadata")

        # Create SharePoint client
        client = create_sharepoint_client(sharepoint_site_url)

        # Get configuration
        page_name = source_config.get("sharepoint_pages_page_name")
        embed_title = source_config.get("sharepoint_pages_embed_title", False)

        # Create data source
        data_source = SharePointPagesDataSource(client, page_name)

        # Return processor
        return SharepointPagesDataProcessor(
            data_source, collection_config, embed_title
        )
