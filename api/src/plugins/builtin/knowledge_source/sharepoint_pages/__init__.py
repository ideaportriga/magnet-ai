"""SharePoint Pages Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import SharePointPagesPlugin

# Auto-register plugin when module is imported
PluginRegistry.register(SharePointPagesPlugin())

__all__ = ["SharePointPagesPlugin"]
