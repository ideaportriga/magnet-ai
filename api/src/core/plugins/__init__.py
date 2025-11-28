"""Universal Plugin System for Magnet AI

This module provides a flexible plugin architecture that supports multiple plugin types.
Currently implemented: Knowledge Source plugins
Future support: LLM Providers, Authentication, Storage Backends, etc.
"""

from core.plugins.base import BasePlugin, PluginMetadata
from core.plugins.plugin_types import PluginType
from core.plugins.registry import PluginRegistry

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginType",
    "PluginRegistry",
]
