"""Oracle Knowledge Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import OracleKnowledgePlugin

# Auto-register plugin
# NOTE: Comment this out when moving to external package
PluginRegistry.register(OracleKnowledgePlugin())

__all__ = ["OracleKnowledgePlugin"]
