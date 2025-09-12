from litestar import Router

from .monitoring import MetricsController
from .traces import ObservabilityTracesController

observability_router = Router(
    path="/observability",
    route_handlers=[
        MetricsController,
        ObservabilityTracesController,
    ],
)
