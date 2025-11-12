"""SharePoint Pages Knowledge Source Plugin

Synchronizes SharePoint pages (wiki pages, modern pages).
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.sharepoint.source_pages import SharePointPagesDataSource
from data_sources.sharepoint.utils import (
    create_sharepoint_client,
    create_sharepoint_client_with_config,
)
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
                    "endpoint": {
                        "type": "string",
                        "description": "SharePoint base URL (e.g., https://ideaport.sharepoint.com)",
                    },
                    "site_path": {
                        "type": "string",
                        "description": "SharePoint site path (e.g., sites/GenAI/siteName)",
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
                    # Provider-level credentials (from provider config)
                    "client_id": {
                        "type": "string",
                        "description": "Azure AD application client ID (from provider)",
                    },
                    "client_secret": {
                        "type": "string",
                        "description": "Azure AD application client secret (from provider)",
                    },
                    "tenant": {
                        "type": "string",
                        "description": "Azure AD tenant ID for cert auth (from provider)",
                    },
                    "thumbprint": {
                        "type": "string",
                        "description": "Certificate thumbprint for cert auth (from provider)",
                    },
                    "private_key": {
                        "type": "string",
                        "description": "Certificate private key for cert auth (from provider)",
                    },
                },
                "required": ["endpoint"],
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
            ClientException: If endpoint or site_path is missing
        """
        # Get base endpoint from provider
        base_endpoint = source_config.get("endpoint")
        if not base_endpoint:
            raise ClientException(
                "Missing `endpoint` configuration. Please ensure the provider is configured "
                "with a valid SharePoint endpoint URL (e.g., https://yoursite.sharepoint.com)"
            )

        # Get site path from knowledge source config
        site_path = source_config.get("site_path")
        if not site_path:
            raise ClientException(
                "Missing `site_path` configuration. Please specify the SharePoint site path "
                "(e.g., sites/YourSite) in the knowledge source settings"
            )

        # Construct full SharePoint site URL
        # Remove trailing slash from base_endpoint and leading slash from site_path
        base_endpoint = base_endpoint.rstrip("/")
        site_path = site_path.lstrip("/")
        sharepoint_site_url = f"{base_endpoint}/{site_path}"

        # Get credentials from source_config (merged with provider config)
        client_id = source_config.get("client_id")
        client_secret = source_config.get("client_secret")
        tenant = source_config.get("tenant")
        thumbprint = source_config.get("thumbprint")
        private_key = source_config.get("private_key")

        # Create SharePoint client with explicit config if provided, otherwise use env
        if client_id:
            client = create_sharepoint_client_with_config(
                sharepoint_site_url=sharepoint_site_url,
                client_id=client_id,
                client_secret=client_secret,
                tenant=tenant,
                thumbprint=thumbprint,
                private_key=private_key,
            )
        else:
            # Fall back to environment-based config for backward compatibility
            client = create_sharepoint_client(sharepoint_site_url)

        # Get configuration
        page_name = source_config.get("sharepoint_pages_page_name")
        embed_title = source_config.get("sharepoint_pages_embed_title", False)

        # Create data source
        data_source = SharePointPagesDataSource(client, page_name)

        # Return processor
        return SharepointPagesDataProcessor(data_source, collection_config, embed_title)
