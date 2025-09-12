from typing import Any

from litestar import Router, get
from litestar.types import ControllerRouterHandler

from core.domain.agents import AgentsController as AgentsControllerSQL
from core.domain.ai_apps import AiAppsController as AiAppsControllerSQL
from core.domain.ai_models import AIModelsController
from core.domain.api_tools import ApiToolsController as ApiToolsControllerSQL
from core.domain.collections import CollectionsController
from core.domain.evaluation_sets import (
    EvaluationSetsController as EvaluationSetsControllerSQL,
)
from core.domain.evaluations import EvaluationsController as EvaluationsControllerSQL
from core.domain.jobs import JobsController as JobsControllerSQL
from core.domain.mcp_servers import MCPServersController as MCPServersControllerSQL
from core.domain.metrics import MetricsController
from core.domain.prompts import PromptsController
from core.domain.rag_tools import RagToolsController as RagToolsControllerSQL
from core.domain.retrieval_tools import (
    RetrievalToolsController as RetrievalToolsControllerSQL,
)
from core.domain.traces import TracesController
from guards.role import UserRole, create_role_guard
from routes.admin.api_keys import ApiKeysController
from routes.admin.mcp_servers import McpServersController
from routes.user.telemetry import TelemetryController

from .admin.agents import AgentsController
from .admin.ai_apps import AiAppsController
from .admin.api_tool_providers import ApiToolProvidersController
from .admin.api_tools import ApiToolsController

# from .admin.evaluation import evaluation_router
from .admin.evaluations import EvaluationsController
from .admin.experimental import experimental_router

# from .admin.jobs import JobsBaseController, JobsController
from .admin.knowledge_sources import (
    knowledge_sources_router,
    knowledge_sources_router_deprecated,
)
from .admin.model_providers import (
    ModelProvidersController,
    ModelProvidersControllerDeprecated,
)
from .admin.models import ModelsController
from .admin.observability import observability_router
from .admin.prompt_templates import PromptTemplatesController
from .admin.rag import RagController
from .admin.rag_tools import RagToolsController
from .admin.retrieval_tools import (
    RetrievalToolsController,
    RetrievalToolsControllerDeprecated,
)
from .admin.scheduler import SchedulerController
from .admin.transfer import TransferController
from .admin.utils import UtilsController
from .auth import AuthController
from .user.agent_conversations import AgentConversationsController
from .user.ai_apps import UserAiAppsController
from .user.execute import UserExecuteController
from .user.utils import UserUtilsController


def get_route_handlers(auth_enabled: bool) -> list[ControllerRouterHandler]:
    @get("/health", exclude_from_auth=True, tags=["health"])
    async def health_route_handler() -> dict[str, Any]:
        """Health Check endpoint"""
        return {}

    route_handlers_admin: list[ControllerRouterHandler] = [
        AgentsController,
        AiAppsController,
        AIModelsController,
        ApiKeysController,
        ApiToolProvidersController,
        ApiToolsController,
        AgentsControllerSQL,
        AiAppsControllerSQL,
        ApiToolsControllerSQL,
        CollectionsController,
        MCPServersControllerSQL,
        EvaluationSetsControllerSQL,
        EvaluationsControllerSQL,
        MetricsController,
        RetrievalToolsControllerSQL,
        RagToolsControllerSQL,
        TracesController,
        EvaluationsController,
        # evaluation_router,
        experimental_router,
        JobsControllerSQL,
        # JobsController,
        # JobsBaseController,
        knowledge_sources_router,
        knowledge_sources_router_deprecated,
        McpServersController,
        ModelsController,
        ModelProvidersController,
        ModelProvidersControllerDeprecated,
        observability_router,
        PromptsController,
        PromptTemplatesController,
        RagController,
        RagToolsController,
        RetrievalToolsController,
        RetrievalToolsControllerDeprecated,
        TransferController,
        UtilsController,
        SchedulerController,
    ]

    route_handlers_user: list[ControllerRouterHandler] = [
        AgentConversationsController,
        UserAiAppsController,
        UserExecuteController,
        TelemetryController,
        UserUtilsController,
    ]

    route_handlers_public: list[ControllerRouterHandler] = [
        health_route_handler,
    ]

    if auth_enabled:
        route_handlers_public.append(AuthController)

    router_api_admin = Router(
        path="/admin",
        route_handlers=route_handlers_admin,
    )

    if auth_enabled:
        router_api_admin.guards = [create_role_guard(UserRole.ADMIN)]

    router_api_user = Router(
        path="/user",
        route_handlers=route_handlers_user,
    )

    router_api_public = Router(
        path="/",
        route_handlers=route_handlers_public,
    )

    router_api = Router(
        path="/api",
        route_handlers=[
            router_api_admin,
            router_api_user,
        ],
    )

    return [
        router_api,
        router_api_public,
    ]
