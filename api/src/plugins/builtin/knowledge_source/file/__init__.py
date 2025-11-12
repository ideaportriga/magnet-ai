"""File URL Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import FileUrlPlugin

# Auto-register plugin
PluginRegistry.register(FileUrlPlugin())

__all__ = ["FileUrlPlugin"]
