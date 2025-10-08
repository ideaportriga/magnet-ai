"""SharePoint Documents Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import SharePointDocumentsPlugin

# Auto-register plugin when module is imported
PluginRegistry.register(SharePointDocumentsPlugin())

__all__ = ["SharePointDocumentsPlugin"]
