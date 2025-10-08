"""RightNow Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import RightNowPlugin

# Auto-register plugin
# NOTE: Comment this out when moving to external package
PluginRegistry.register(RightNowPlugin())

__all__ = ["RightNowPlugin"]
