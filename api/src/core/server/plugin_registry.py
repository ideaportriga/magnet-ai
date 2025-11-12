from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.plugins.structlog import StructlogPlugin

from core.config import app as config

from .plugins import (
    CORSPlugin,
    DependenciesPlugin,
    ExceptionHandlersPlugin,
    MiddlewarePlugin,
    OpenAPIPlugin,
    OracleMonitoringPlugin,
    ShutdownPlugin,
    StartupPlugin,
)

# Core plugins
structlog = StructlogPlugin(config=config.log)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
problem_details = ProblemDetailsPlugin(config=config.problem_details)

# Initialize custom plugins
cors_plugin = CORSPlugin()
dependencies_plugin = DependenciesPlugin()
exception_handlers_plugin = ExceptionHandlersPlugin()
middleware_plugin = MiddlewarePlugin()
openapi_plugin = OpenAPIPlugin()
oracle_monitoring_plugin = OracleMonitoringPlugin()
shutdown_plugin = ShutdownPlugin()
startup_plugin = StartupPlugin()
