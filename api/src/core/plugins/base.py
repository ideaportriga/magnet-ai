"""Base Plugin Architecture

Provides the foundation for all plugins in the Magnet AI system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass, field

from core.plugins.plugin_types import PluginType


@dataclass
class PluginMetadata:
    """Metadata describing a plugin"""

    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)


class BasePlugin(ABC):
    """Base class for all plugins in the system

    All plugins must inherit from this class and implement the required methods.
    This ensures a consistent interface across all plugin types.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata including name, version, author, etc."""

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Return the type of this plugin"""

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with the provided configuration

        This method is called when the plugin is loaded. Override it to perform
        any setup tasks like establishing connections, loading resources, etc.

        Args:
            config: Plugin-specific configuration dictionary
        """

    async def shutdown(self) -> None:
        """Perform cleanup when the plugin is being shut down

        Override this method to release resources, close connections, etc.
        """

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate plugin configuration

        Override this method to implement custom configuration validation.
        Raise an exception if the configuration is invalid.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
