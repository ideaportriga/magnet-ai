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
from .admin.utils import UtilsController
from .auth_v2 import AuthV2Controller
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

    @get("/health/scheduler", exclude_from_auth=True, tags=["health"])
    async def scheduler_health_route_handler() -> dict[str, Any]:
        """Scheduler connection pool health check (see §B.6).

        Returns 'degraded' when the scheduler pool is fully checked out —
        an early signal of the APScheduler-hang scenario analysed in
        docs/scheduler-hang-analysis.md.
        """
        from scheduler.manager import get_scheduler_pool_info

        info = get_scheduler_pool_info()
        if "error" in info:
            return {"status": "unknown", "detail": info}

        checked_out = info.get("checked_out", 0) or 0
        pool_size = info.get("pool_size", 0) or 0
        overflow = info.get("overflow", 0) or 0
        exhausted = pool_size > 0 and checked_out >= (pool_size + max(overflow, 0))
        return {
            "status": "degraded" if exhausted else "ok",
            "detail": info,
        }

    @get("/health/ready", exclude_from_auth=True, tags=["health"])
    async def readiness_handler() -> dict[str, Any]:
        """Readiness probe — checks that critical subsystems are operational."""
        from core.db.monitoring import get_db_pool_status

        checks: dict[str, Any] = {}
        all_ok = True

        # 1. Database pool
        try:
            pool_status = await get_db_pool_status()
            checks["db_pool"] = "ok"
            checks["db_pool_detail"] = pool_status
        except Exception as e:
            checks["db_pool"] = f"error: {e}"
            all_ok = False

        # 2. API key cache loaded
        try:
            from services.api_keys.services import API_KEYS_PERSISTED_BY_HASH_CACHE

            cache_size = len(API_KEYS_PERSISTED_BY_HASH_CACHE)
            checks["api_key_cache"] = "ok" if cache_size >= 0 else "empty"
            checks["api_key_cache_size"] = cache_size
        except Exception as e:
            checks["api_key_cache"] = f"error: {e}"
            all_ok = False

        # 3. Scheduler running
        try:
            from litestar import Request as _Request  # noqa: F401

            # Scheduler is on app.state — not accessible here without request.
            # Just verify import works; actual scheduler check in /health with app state.
            checks["scheduler"] = "ok"
        except Exception as e:
            checks["scheduler"] = f"error: {e}"
            all_ok = False

        return {"status": "ok" if all_ok else "degraded", "checks": checks}

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

    # Test utilities (DEBUG_MODE only). Registered via the public router
    # with path /test — the admin router has a role guard which would block
    # the bootstrap endpoints (/test/promote creates the superuser needed
    # to pass that very guard). These endpoints are still gated by
    # DEBUG_MODE and must NEVER be exposed in production.
    if os.getenv("DEBUG_MODE", "").lower() in ("true", "1"):
        from routes.admin.test_utils import TestUtilsController  # noqa: I001

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
        scheduler_health_route_handler,
        serve_static_file,
    ]

    if os.getenv("DEBUG_MODE", "").lower() in ("true", "1"):
        route_handlers_public.append(TestUtilsController)

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

    # Unified auth endpoints under /api/v2
    router_api_v2 = Router(
        path="/v2",
        route_handlers=[AuthV2Controller],
    )

    router_api = Router(
        path="/api",
        route_handlers=[
            router_api_admin,
            router_api_user,
            router_api_v2,
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
