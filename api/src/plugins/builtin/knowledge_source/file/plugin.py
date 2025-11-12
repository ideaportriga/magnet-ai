"""File URL Knowledge Source Plugin

Synchronizes content from file URLs.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.file.source import UrlDataSource
from data_sync.data_processor import DataProcessor
from data_sync.processors.file_data_processor import UrlDataProcessor


class FileUrlPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing files from URLs"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="File URL",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes content from file URLs",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "file_url": {
                        "type": "array",
                        "description": "Only links to PDF files are accepted",
                        "items": {"type": "string"},
                    },
                },
                "required": ["file_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "File"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create File URL processor

        Args:
            source_config: Source configuration containing file URL(s)
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            UrlDataProcessor instance

        Raises:
            ClientException: If file_url is missing
        """
        file_url = source_config.get("file_url")

        if not file_url:
            raise ClientException(
                "Missing `file_url` configuration. Please specify the file URL(s) "
                "in the knowledge source settings"
            )

        # Ensure file_url is a list (can be string or list)
        if isinstance(file_url, str):
            file_url = [file_url]

        # Create data source with list of URLs
        data_source = UrlDataSource(file_url)

        # Return processor
        return UrlDataProcessor(data_source, collection_config)
