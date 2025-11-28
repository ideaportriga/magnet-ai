"""Custom plugins for the application."""

from .cors import CORSPlugin
from .dependencies import DependenciesPlugin
from .exception_handlers import ExceptionHandlersPlugin
from .middleware import MiddlewarePlugin
from .openapi import OpenAPIPlugin
from .oracle_monitoring import OracleMonitoringPlugin
from .shutdown import ShutdownPlugin
from .startup import StartupPlugin

__all__ = [
    "CORSPlugin",
    "DependenciesPlugin",
    "ExceptionHandlersPlugin",
    "MiddlewarePlugin",
    "OpenAPIPlugin",
    "OracleMonitoringPlugin",
    "ShutdownPlugin",
    "StartupPlugin",
]
