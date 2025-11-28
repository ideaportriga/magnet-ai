"""Confluence Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import ConfluencePlugin

# Auto-register plugin
PluginRegistry.register(ConfluencePlugin())

__all__ = ["ConfluencePlugin"]
