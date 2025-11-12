"""Fluid Topics Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry

from .plugin import FluidTopicsPlugin

# Auto-register plugin
PluginRegistry.register(FluidTopicsPlugin())

__all__ = ["FluidTopicsPlugin"]
