"""Documentation Knowledge Source Plugin

Synchronizes content from VitePress documentation.
"""

from core.plugins.registry import PluginRegistry

from .plugin import DocumentationPlugin

# Auto-register plugin
PluginRegistry.register(DocumentationPlugin())

__all__ = ["DocumentationPlugin"]
