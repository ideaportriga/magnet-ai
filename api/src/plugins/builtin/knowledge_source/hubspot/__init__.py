"""HubSpot Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import HubspotPlugin

# Auto-register plugin
# NOTE: Comment this out when moving to external package
PluginRegistry.register(HubspotPlugin())

__all__ = ["HubspotPlugin"]
