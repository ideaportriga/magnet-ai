from litestar import Router

from .monitoring import MetricsController

observability_router = Router(
    path="/observability",
    route_handlers=[
        MetricsController,
    ],
)
