"""Universal Plugin Registry

Manages registration, loading, and retrieval of all plugin types.
"""

import importlib
import os
import pkgutil
from collections import defaultdict
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.plugins.base import BasePlugin
from core.plugins.plugin_types import PluginType

logger = getLogger(__name__)


class PluginRegistry:
    """Universal registry for managing all types of plugins

    This registry provides a centralized location for:
    - Registering plugins
    - Loading built-in and external plugins
    - Retrieving plugins by type and ID
    - Managing plugin lifecycle (initialization/shutdown)
    """

    # Structure: {plugin_type: {plugin_id: plugin_instance}}
    _plugins: Dict[PluginType, Dict[str, BasePlugin]] = defaultdict(dict)
    _loaded = False

    @classmethod
    def register(cls, plugin: BasePlugin, plugin_id: Optional[str] = None) -> None:
        """Register a plugin in the registry

        Args:
            plugin: The plugin instance to register
            plugin_id: Optional custom ID. If not provided, will be auto-generated

        Example:
            >>> plugin = MyKnowledgeSourcePlugin()
            >>> PluginRegistry.register(plugin)
        """
        plugin_type = plugin.plugin_type

        # Auto-generate plugin ID if not provided
        if plugin_id is None:
            plugin_id = cls._get_plugin_id(plugin)

        if plugin_id in cls._plugins[plugin_type]:
            logger.warning(
                f"Plugin {plugin_type}/{plugin_id} already registered, overwriting"
            )

        cls._plugins[plugin_type][plugin_id] = plugin
        logger.info(f"Registered plugin: {plugin_type}/{plugin_id}")

    @classmethod
    def get(cls, plugin_type: PluginType, plugin_id: str) -> Optional[BasePlugin]:
        """Retrieve a specific plugin by type and ID

        Args:
            plugin_type: The type of plugin to retrieve
            plugin_id: The unique identifier of the plugin

        Returns:
            The plugin instance, or None if not found

        Example:
            >>> plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, "Sharepoint")
        """
        return cls._plugins.get(plugin_type, {}).get(plugin_id)

    @classmethod
    def get_all(cls, plugin_type: PluginType) -> Dict[str, BasePlugin]:
        """Get all plugins of a specific type

        Args:
            plugin_type: The type of plugins to retrieve

        Returns:
            Dictionary mapping plugin IDs to plugin instances
        """
        return cls._plugins.get(plugin_type, {}).copy()

    @classmethod
    def list_available(
        cls, plugin_type: Optional[PluginType] = None
    ) -> Dict[str, List[str]]:
        """List all available plugins, optionally filtered by type

        Args:
            plugin_type: Optional filter by plugin type

        Returns:
            Dictionary mapping plugin types to lists of plugin IDs
        """
        if plugin_type:
            return {plugin_type.value: list(cls._plugins.get(plugin_type, {}).keys())}

        return {
            ptype.value: list(plugins.keys()) for ptype, plugins in cls._plugins.items()
        }

    @classmethod
    def load_builtin_plugins(cls, plugin_type: Optional[PluginType] = None) -> None:
        """Load built-in plugins from the plugins/builtin directory

        Args:
            plugin_type: Optional - load only plugins of this type
        """
        # Plugins are located in src/plugins/builtin/
        builtin_path = Path(__file__).parent.parent.parent / "plugins" / "builtin"

        if not builtin_path.exists():
            logger.warning(f"Built-in plugins directory not found: {builtin_path}")
            return

        # If specific type requested, load only that type
        if plugin_type:
            type_path = builtin_path / plugin_type.value
            if type_path.exists():
                cls._load_plugins_from_path(type_path, plugin_type.value)
        else:
            # Load all plugin types
            for type_dir in builtin_path.iterdir():
                if type_dir.is_dir() and not type_dir.name.startswith("_"):
                    cls._load_plugins_from_path(type_dir, type_dir.name)

    @classmethod
    def load_external_plugins(cls, plugin_type: Optional[PluginType] = None) -> None:
        """Load external plugins from plugins/external directory and environment variable

        External plugins can be loaded from two sources:
        1. Local directory: plugins/external/<plugin_type>/ (auto-discovered)
        2. Environment variable: MAGNET_PLUGINS (for installed packages)

        The environment variable format is: module1,module2,module3

        Example:
            MAGNET_PLUGINS=magnet_plugins.oracle_knowledge,magnet_plugins.salesforce
        """
        # First, load plugins from local external directory
        external_path = Path(__file__).parent.parent.parent / "plugins" / "external"

        if external_path.exists():
            logger.info(f"Scanning external plugins directory: {external_path}")

            # If specific type requested, load only that type
            if plugin_type:
                type_path = external_path / plugin_type.value
                if type_path.exists():
                    cls._load_plugins_from_path(type_path, plugin_type.value)
            else:
                # Load all plugin types from external directory
                for type_dir in external_path.iterdir():
                    if type_dir.is_dir() and not type_dir.name.startswith("_"):
                        cls._load_plugins_from_path(type_dir, type_dir.name)
        else:
            logger.debug(f"External plugins directory not found: {external_path}")

        # Second, load plugins from environment variable (for installed packages)
        external_plugins = os.environ.get("MAGNET_PLUGINS", "").split(",")

        for plugin_module in external_plugins:
            plugin_module = plugin_module.strip()
            if not plugin_module:
                continue

            try:
                importlib.import_module(plugin_module)
                logger.info(f"Loaded external plugin module from env: {plugin_module}")
            except ImportError as e:
                logger.warning(f"Failed to load external plugin {plugin_module}: {e}")

    @classmethod
    def auto_load(cls) -> None:
        """Automatically load all built-in and external plugins

        This should be called once during application startup.
        Subsequent calls are ignored (idempotent).
        """
        if cls._loaded:
            logger.debug("Plugins already loaded, skipping auto_load")
            return

        logger.info("Loading plugins...")
        cls.load_builtin_plugins()
        cls.load_external_plugins()
        cls._loaded = True

        # Log summary of loaded plugins
        available = cls.list_available()
        for ptype, plugins in available.items():
            if plugins:
                logger.info(f"Available {ptype} plugins: {', '.join(plugins)}")

    @classmethod
    async def initialize_all(cls, config: Dict[str, Any]) -> None:
        """Initialize all registered plugins with configuration

        Args:
            config: Configuration dictionary with plugin-specific settings
        """
        for plugin_type, plugins in cls._plugins.items():
            type_config = config.get(plugin_type.value, {})

            for plugin_id, plugin in plugins.items():
                plugin_config = type_config.get(plugin_id, {})
                try:
                    await plugin.initialize(plugin_config)
                    logger.info(f"Initialized plugin: {plugin_type}/{plugin_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to initialize plugin {plugin_type}/{plugin_id}: {e}"
                    )

    @classmethod
    async def shutdown_all(cls) -> None:
        """Gracefully shutdown all registered plugins"""
        for plugin_type, plugins in cls._plugins.items():
            for plugin_id, plugin in plugins.items():
                try:
                    await plugin.shutdown()
                    logger.info(f"Shutdown plugin: {plugin_type}/{plugin_id}")
                except Exception as e:
                    logger.error(
                        f"Failed to shutdown plugin {plugin_type}/{plugin_id}: {e}"
                    )

    @classmethod
    def _get_plugin_id(cls, plugin: BasePlugin) -> str:
        """Auto-generate plugin ID based on plugin type

        Args:
            plugin: The plugin instance

        Returns:
            A unique identifier for the plugin
        """
        # Import here to avoid circular dependency
        from core.plugins.interfaces import KnowledgeSourcePlugin

        if isinstance(plugin, KnowledgeSourcePlugin):
            return plugin.source_type

        # Fallback to plugin name from metadata
        return plugin.metadata.name

    @classmethod
    def _load_plugins_from_path(cls, path: Path, plugin_type_name: str) -> None:
        """Load all plugin modules from a directory

        Args:
            path: Directory path containing plugin modules
            plugin_type_name: Name of the plugin type (for logging)
        """
        for module_info in pkgutil.iter_modules([str(path)]):
            if module_info.name.startswith("_"):
                continue

            try:
                # Calculate relative import path
                relative_path = path.relative_to(Path(__file__).parent.parent.parent)
                module_path = (
                    str(relative_path).replace("/", ".") + f".{module_info.name}"
                )

                importlib.import_module(module_path)
                logger.info(
                    f"Loaded {plugin_type_name} plugin module: {module_info.name}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load plugin module {module_info.name}: {e}",
                    exc_info=True,
                )
