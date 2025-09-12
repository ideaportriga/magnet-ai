from litestar import Router

experimental_router = Router(
    path="/experimental",
    tags=["experimental"],
    route_handlers=[],
)
