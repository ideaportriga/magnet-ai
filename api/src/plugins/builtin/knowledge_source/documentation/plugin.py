"""Documentation Knowledge Source Plugin

Synchronizes content from VitePress documentation sites.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.vitepress.source import VitePressDataSource
from data_sync.data_processor import DataProcessor
from data_sync.processors.documentation_data_processor import DocumentationDataProcessor


class DocumentationPlugin(KnowledgeSourcePlugin):
    """Plugin for syncing documentation from VitePress sites"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Documentation",
            version="1.0.0",
            author="Magnet AI Team",
            description="Synchronizes content from VitePress documentation sites",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=["httpx", "beautifulsoup4"],
            config_schema={
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "description": "Base URL of the VitePress documentation site (e.g., http://localhost:5173)",
                    },
                    "languages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of language codes to crawl (e.g., ['en', 'ru'])",
                        "default": ["en"],
                    },
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of documentation sections to crawl (e.g., ['quickstarts', 'admin'])",
                        "default": ["quickstarts", "admin"],
                    },
                    "section_start_urls": {
                        "type": "object",
                        "description": "Optional: Specific start URLs for each section. Format: {'section_name': 'url'}. Example: {'admin': 'http://localhost:5173/docs/en/admin/connect/models/overview.html'}",
                        "additionalProperties": {"type": "string"},
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth for crawling documentation pages",
                        "default": 5,
                    },
                },
                "required": ["base_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "Documentation"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create Documentation processor

        Args:
            source_config: Source configuration containing documentation settings
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            DocumentationDataProcessor instance

        Raises:
            ClientException: If base_url is missing
        """
        base_url = source_config.get("base_url")

        if not base_url:
            raise ClientException("Missing `base_url` in metadata")

        # Get optional configuration
        languages = source_config.get("languages", ["en"])
        sections = source_config.get("sections", ["quickstarts", "admin"])
        section_start_urls = source_config.get("section_start_urls", {})
        max_depth = source_config.get("max_depth", 5)

        # Create data source
        data_source = VitePressDataSource(
            base_url=base_url,
            languages=languages,
            sections=sections,
            section_start_urls=section_start_urls,
            max_depth=max_depth,
        )

        # Return processor
        return DocumentationDataProcessor(data_source, collection_config)
