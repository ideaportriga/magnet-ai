"""Plugin Interfaces

Defines specialized interfaces for different types of plugins.
Each interface extends BasePlugin with type-specific methods.
"""

from abc import abstractmethod
from typing import Any, Dict

from core.plugins.base import BasePlugin
from core.plugins.plugin_types import PluginType


class KnowledgeSourcePlugin(BasePlugin):
    """Plugin interface for knowledge source integrations

    Knowledge source plugins provide the ability to sync data from external
    sources like SharePoint, Confluence, Salesforce, etc.
    """

    @property
    def plugin_type(self) -> PluginType:
        """This is a knowledge source plugin"""
        return PluginType.KNOWLEDGE_SOURCE

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Unique identifier for this source type

        This should match the value stored in collection metadata's
        source.source_type field.

        Examples: "Sharepoint", "Confluence", "Salesforce"
        """

    @abstractmethod
    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> Any:  # Returns DataProcessor
        """Create a data processor for syncing this source

        Args:
            source_config: Configuration from collection.source
            collection_config: Full collection configuration
            store: Database store instance

        Returns:
            DataProcessor instance ready for synchronization

        Raises:
            ClientException: If configuration is invalid or missing required fields
        """


# Future plugin interfaces can be added here:
# class LLMProviderPlugin(BasePlugin): ...
# class AuthenticationPlugin(BasePlugin): ...
# class StorageBackendPlugin(BasePlugin): ...
# class EmbeddingModelPlugin(BasePlugin): ...
