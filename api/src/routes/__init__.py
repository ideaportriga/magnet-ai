import os

from typing import Any

from litestar import Router, get
from litestar.types import ControllerRouterHandler
from litestar.static_files import create_static_files_router

from core.domain.ai_apps import AiAppsController
from core.domain.ai_models import AIModelsController
from core.domain.api_servers import ApiServersController
from core.domain.collections import CollectionsController
from core.domain.evaluation_sets import EvaluationSetsController
from core.domain.evaluations import EvaluationsController
from core.domain.jobs import JobsController
from core.domain.mcp_servers import MCPServersController
from core.domain.metrics import MetricsController
from core.domain.prompts import PromptsController
from core.domain.providers import ProvidersController
from core.domain.rag_tools import RagToolsController
from core.domain.retrieval_tools import RetrievalToolsController
from core.domain.traces import TracesController
from core.domain.knowledge_graph import KnowledgeGraphController
from guards.role import UserRole, create_role_guard
from routes.admin.api_keys import ApiKeysController
from routes.user.telemetry import TelemetryController

from .admin.agents import AgentsController
from .admin.deep_research import DeepResearchConfigController, DeepResearchRunController


from .admin.knowledge_sources import (
    knowledge_sources_router,
    knowledge_sources_router_deprecated,
)
from .admin.observability import observability_router
from .admin.rag import RagController
from .admin.scheduler import SchedulerController
from .admin.transfer import TransferController
from .admin.utils import UtilsController
from .auth import AuthController
from .user.agent_conversations import AgentConversationsController
from .user.ask_magnet import AskMagnetController
from .user.ai_apps import UserAiAppsController
from .user.execute import UserExecuteController
from .user.utils import UserUtilsController
from .user.agents import UserAgentsController
from .static import serve_static_file


def get_route_handlers(
    auth_enabled: bool, web_included: bool
) -> list[ControllerRouterHandler]:
    @get("/health", exclude_from_auth=True, tags=["health"])
    async def health_route_handler() -> dict[str, Any]:
        """Health Check endpoint"""
        return {}

    route_handlers_admin: list[ControllerRouterHandler] = [
        # Admin routes (alphabetically sorted)
        AgentsController,  # Admin / Agents
        AiAppsController,  # Admin / AI Apps
        ApiKeysController,  # Admin / API Keys
        ApiServersController,  # Admin / API Servers
        CollectionsController,  # Admin / Collections
        DeepResearchConfigController,  # Admin / Deep Research Configs
        DeepResearchRunController,  # Admin / Deep Research Runs
        EvaluationSetsController,  # Admin / Evaluation Sets
        EvaluationsController,  # Admin / Evaluations
        JobsController,  # Admin / Jobs
        knowledge_sources_router_deprecated,  # Admin / Knowledge Sources
        MCPServersController,  # Admin / MCP Servers
        MetricsController,  # Admin / Metrics
        AIModelsController,  # Admin / Models
        observability_router,  # Admin / Observability
        PromptsController,  # Admin / Prompt Templates
        ProvidersController,  # Admin / Providers
        RagToolsController,  # Admin / RAG Tools
        RetrievalToolsController,  # Admin / Retrieval Tools
        SchedulerController,  # Admin / Scheduler
        TracesController,  # Admin / Traces
        TransferController,  # Admin / Transfer
        UtilsController,  # Admin / Utils
        KnowledgeGraphController,  # Admin / Knowledge Graph
        # Deprecated routes first (with [Deprecated] prefix)
        knowledge_sources_router,  # [Deprecated] Knowledge Sources
        RagController,  # [Deprecated] RAG
    ]

    if (os.getenv("STT_ENABLED", "").lower()) == "true":
        from .admin.recordings import RecordingsController
        from .admin.upload_sessions import UploadSessionsController

        route_handlers_admin.extend(
            [
                RecordingsController,  # Admin / Recordings
                UploadSessionsController,  # Admin / Upload Sessions
            ]
        )

    route_handlers_user: list[ControllerRouterHandler] = [
        AskMagnetController,  # User / Ask Magnet (form submissions)
        AgentConversationsController,  # User / Agent Conversations
        UserAgentsController,  # User / Agents Messages
        UserAiAppsController,  # User / AI Apps
        UserExecuteController,  # User / Execute
        TelemetryController,  # User / Telemetry
        UserUtilsController,  # User / Utils
    ]

    route_handlers_public: list[ControllerRouterHandler] = [
        health_route_handler,
        serve_static_file,
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

    routes = [
        router_api,
        router_api_public,
    ]

    if web_included:
        # Serve static assets for each app
        static_router_admin_assets = create_static_files_router(
            path="/admin/assets",
            directories=["web/admin/assets"],
            html_mode=False,
            opt={"exclude_from_auth": True},
        )

        static_router_panel_assets = create_static_files_router(
            path="/panel/assets",
            directories=["web/panel/assets"],
            html_mode=False,
            opt={"exclude_from_auth": True},
        )

        static_router_help_assets = create_static_files_router(
            path="/help/assets",
            directories=["web/help/assets"],
            html_mode=False,
            opt={"exclude_from_auth": True},
        )

        # Serve HTML and other root files
        static_router_admin = create_static_files_router(
            path="/admin",
            directories=["web/admin"],
            html_mode=True,
            opt={"exclude_from_auth": True},
        )

        static_router_panel = create_static_files_router(
            path="/panel",
            directories=["web/panel"],
            html_mode=True,
            opt={"exclude_from_auth": True},
        )

        static_router_help = create_static_files_router(
            path="/help",
            directories=["web/help"],
            html_mode=True,
            opt={"exclude_from_auth": True},
        )

        routes.extend(
            [
                static_router_admin_assets,
                static_router_panel_assets,
                static_router_help_assets,
                static_router_admin,
                static_router_panel,
                static_router_help,
            ]
        )

    return routes
