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
                        "description": "Links to supported document files (PDF, DOCX, XLSX, PPTX, HTML, images, etc.)",
                        "items": {"type": "string"},
                        "x-component": "collections-file-url-upload",
                    },
                    "uploaded_files": {
                        "type": "array",
                        "description": "Files uploaded via StorageService or legacy filesystem",
                        "x-hidden": True,
                        "items": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string"},
                                "file_id": {"type": "string"},
                                "storage_path": {"type": "string"},
                            },
                        },
                    },
                },
                "required": [],
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
        """Create File URL processor."""
        file_url = source_config.get("file_url") or []
        uploaded_files = source_config.get("uploaded_files") or []

        if not file_url and not uploaded_files:
            raise ClientException(
                "Missing file configuration. Please specify file URL(s) "
                "or upload files in the knowledge source settings"
            )

        if isinstance(file_url, str):
            file_url = [file_url]

        # Split uploaded files: new-style (file_id) vs legacy (storage_path)
        stored_files = [uf for uf in uploaded_files if "file_id" in uf]
        local_files = [uf for uf in uploaded_files if "storage_path" in uf]

        data_source = UrlDataSource(
            file_url,
            local_files=local_files,
            stored_files=stored_files,
        )

        # Get StorageService and shared db_session from store
        # (both injected by _inject_storage_into_store in sync_collection_standalone)
        storage_service = getattr(store, "storage_service", None)
        db_session = getattr(store, "storage_db_session", None)

        return UrlDataProcessor(
            data_source,
            collection_config,
            storage_service=storage_service,
            db_session=db_session,
        )
