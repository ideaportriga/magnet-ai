"""SharePoint Documents Knowledge Source Plugin

Synchronizes documents from SharePoint document libraries.
"""

from typing import Any, Dict

from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sources.sharepoint.source_documents import SharePointDocumentsDataSource
from data_sources.sharepoint.utils import (
    create_sharepoint_client,
    create_sharepoint_client_with_config,
)
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
                    "endpoint": {
                        "type": "string",
                        "description": "SharePoint base URL (e.g., https://ideaport.sharepoint.com)",
                    },
                    "site_path": {
                        "type": "string",
                        "description": "SharePoint site path (e.g., sites/GenAI/siteName)",
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
