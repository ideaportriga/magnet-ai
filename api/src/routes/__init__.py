import os
from typing import Any

from litestar import Router, get
from litestar.static_files import create_static_files_router
from litestar.types import ControllerRouterHandler

from core.domain.ai_apps import AiAppsController
from core.domain.catalog import CatalogController
from core.domain.ai_models.controller import AIModelsController
from core.domain.api_servers import ApiServersController
from core.domain.collections import CollectionsController
from core.domain.evaluation_sets import EvaluationSetsController
from core.domain.evaluations import EvaluationsController
from core.domain.jobs import JobsController
from core.domain.knowledge_graph import KnowledgeGraphController
from core.domain.mcp_servers import MCPServersController
from core.domain.metrics import MetricsController
from core.domain.prompts.controller import PromptsController
from core.domain.providers import ProvidersController
from core.domain.rag_tools import RagToolsController
from core.domain.retrieval_tools import RetrievalToolsController
from core.domain.traces import TracesController
from guards.role import UserRole, create_role_guard
from routes.admin.api_keys import ApiKeysController
from routes.admin.groups import GroupsController
from routes.admin.roles import RolesController
from routes.admin.users import UsersController
from routes.user.telemetry import TelemetryController

from .admin.agents import AgentsController
from .admin.files import FilesController
from .admin.deep_research import DeepResearchConfigController, DeepResearchRunController
from .admin.prompt_queue import PromptQueueConfigController
from .admin.knowledge_sources import (
    knowledge_sources_router,
    knowledge_sources_router_deprecated,
)
from core.domain.note_taker_jobs import NoteTakerJobsController
from services.agents.teams.note_taker_settings import NoteTakerSettingsController
from .admin.observability import observability_router
from .admin.rag import RagController
from .admin.scheduler import SchedulerController
from .admin.settings import SettingsController
from .admin.transfer import TransferController
from .admin.utils import UtilsController
from .auth import AuthController
from .local_auth import LocalAuthController
from .mfa import MfaController
from .oauth import OAuthController
from .static import serve_static_file
from .user.agent_conversations import AgentConversationsController
from .user.agents import UserAgentsController
from .user.ai_apps import UserAiAppsController
from .user.ask_magnet import AskMagnetController
from .user.execute import UserExecuteController
from .user.knowledge_graph import UserKnowledgeGraphController
from .user.utils import UserUtilsController


def get_route_handlers(
    auth_enabled: bool, web_included: bool
) -> list[ControllerRouterHandler]:
    @get("/health", exclude_from_auth=True, tags=["health"])
    async def health_route_handler() -> dict[str, Any]:
        """Health Check endpoint"""
        import os
        import resource

        from core.server.background_tasks import active_task_count

        rusage = resource.getrusage(resource.RUSAGE_SELF)
        rss_bytes = rusage.ru_maxrss
        # macOS reports in bytes, Linux in kilobytes
        if os.uname().sysname == "Darwin":
            rss_mb = rss_bytes / (1024 * 1024)
        else:
            rss_mb = rss_bytes / 1024

        return {
            "status": "ok",
            "memory_rss_mb": round(rss_mb, 1),
            "background_tasks_active": active_task_count(),
        }

    @get("/health/db", exclude_from_auth=True, tags=["health"])
    async def db_health_route_handler() -> dict[str, Any]:
        """Database connection pool health check"""
        from core.db.monitoring import get_db_pool_status

        return await get_db_pool_status()

    route_handlers_admin: list[ControllerRouterHandler] = [
        # Admin routes (alphabetically sorted)
        AgentsController,  # Admin / Agents
        AiAppsController,  # Admin / AI Apps
        CatalogController,  # Admin / Catalog (global search)
        ApiKeysController,  # Admin / API Keys
        GroupsController,  # Admin / Groups
        RolesController,  # Admin / Roles
        ApiServersController,  # Admin / API Servers
        CollectionsController,  # Admin / Collections
        DeepResearchConfigController,  # Admin / Deep Research Configs
        DeepResearchRunController,  # Admin / Deep Research Runs
        PromptQueueConfigController,  # Admin / Prompt Queue
        EvaluationSetsController,  # Admin / Evaluation Sets
        EvaluationsController,  # Admin / Evaluations
        FilesController,  # Admin / Files
        JobsController,  # Admin / Jobs
        knowledge_sources_router_deprecated,  # Admin / Knowledge Sources
        MCPServersController,  # Admin / MCP Servers
        MetricsController,  # Admin / Metrics
        NoteTakerSettingsController,  # Admin / Note Taker Settings
        NoteTakerJobsController,  # Admin / Note Taker Preview Jobs
        AIModelsController,  # Admin / Models
        observability_router,  # Admin / Observability
        PromptsController,  # Admin / Prompt Templates
        ProvidersController,  # Admin / Providers
        RagToolsController,  # Admin / RAG Tools
        RetrievalToolsController,  # Admin / Retrieval Tools
        SchedulerController,  # Admin / Scheduler
        SettingsController,  # Admin / Settings
        TracesController,  # Admin / Traces
        TransferController,  # Admin / Transfer
        UsersController,  # Admin / Users
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

    if os.getenv("DEBUG_MODE", "").lower() in ("true", "1"):
        from routes.admin.test_utils import TestUtilsController

        route_handlers_admin.append(
            TestUtilsController
        )  # Admin / Test Utils (debug only)

    route_handlers_user: list[ControllerRouterHandler] = [
        AskMagnetController,  # User / Ask Magnet (form submissions)
        AgentConversationsController,  # User / Agent Conversations
        UserAgentsController,  # User / Agents Messages
        UserAiAppsController,  # User / AI Apps
        UserExecuteController,  # User / Execute
        UserKnowledgeGraphController,  # User / Knowledge Graph
        TelemetryController,  # User / Telemetry
        UserUtilsController,  # User / Utils
    ]

    route_handlers_public: list[ControllerRouterHandler] = [
        health_route_handler,
        db_health_route_handler,
        serve_static_file,
    ]

    # OIDC endpoints (existing flow, under / not /api)
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

    # New auth endpoints under /api (local auth, MFA, OAuth social)
    route_handlers_api_auth: list[ControllerRouterHandler] = [
        LocalAuthController,
        MfaController,
        OAuthController,
    ]

    router_api = Router(
        path="/api",
        route_handlers=[
            router_api_admin,
            router_api_user,
            *route_handlers_api_auth,
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
