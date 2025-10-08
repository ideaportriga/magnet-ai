"""SharePoint Documents Knowledge Source Plugin

Synchronizes documents from SharePoint document libraries.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.sharepoint.source_documents import SharePointDocumentsDataSource
from data_sources.sharepoint.utils import create_sharepoint_client
from data_sync.data_processor import DataProcessor

from .documents_processor import SharepointDocumentsDataProcessor


class SharePointDocumentsPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing SharePoint document libraries"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="SharePoint Documents",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes documents from SharePoint document libraries",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "sharepoint_site_url": {
                        "type": "string",
                        "description": "SharePoint site URL",
                    },
                    "sharepoint_library": {
                        "type": "string",
                        "description": "Document library name",
                    },
                    "sharepoint_folder": {
                        "type": "string",
                        "description": "Optional folder path within library",
                    },
                    "sharepoint_recursive": {
                        "type": "boolean",
                        "description": "Whether to recursively sync subfolders",
                        "default": False,
                    },
                },
                "required": ["sharepoint_site_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Sharepoint"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create SharePoint documents processor

        Args:
            source_config: Source configuration containing SharePoint settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            SharepointDocumentsDataProcessor instance

        Raises:
            ClientException: If sharepoint_site_url is missing
        """
        sharepoint_site_url = source_config.get("sharepoint_site_url")

        if not sharepoint_site_url:
            raise ClientException("Missing `sharepoint_site_url` in metadata")

        # Create SharePoint client
        client = create_sharepoint_client(sharepoint_site_url)

        # Get configuration
        library = source_config.get("sharepoint_library")
        folder = source_config.get("sharepoint_folder")
        recursive = source_config.get("sharepoint_recursive", False)

        # Create data source
        data_source = SharePointDocumentsDataSource(
            ctx=client,
            library=library,
            folder=folder,
            recursive=recursive,
        )

        # Return processor
        return SharepointDocumentsDataProcessor(data_source, collection_config)
