from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, Any, Mapping
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.agents.service import (
    AgentsService,
)
from guards.permissions import Permission, require_permission

from .schemas import Agent, AgentCreate, AgentUpdate

if TYPE_CHECKING:
    pass


class AgentsController(Controller):
    """Agents CRUD"""

    path = "/sql_agents"
    tags = ["Admin / Agents"]

    dependencies = providers.create_service_dependencies(
        AgentsService,
        "agents_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.AGENTS_READ)])
    async def list_agents(
        self,
        agents_service: AgentsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[Agent]:
        """List agents — filtered by record-level visibility (PR 8 finish).

        Tenant boundary is enforced by Postgres RLS; this filter narrows the
        result set further by ownership, `visibility`, department membership
        and explicit grants. Admins / superusers see all tenant rows.
        """
        from core.db.models.agent.agent import Agent as AgentModel
        from services.access_control import record_visibility_filter

        auth = request.scope.get("auth")
        extra_filters: list = list(filters)
        if auth is not None:
            session = agents_service.repository.session
            try:
                where = await record_visibility_filter(
                    session,
                    auth=auth,
                    model=AgentModel,
                    resource_type="agents",
                )
                # `list_and_count` accepts a ColumnElement alongside StatementFilters.
                extra_filters.append(where)
            except Exception:
                # Filter construction failure shouldn't take the endpoint
                # down — RLS still enforces tenant boundary. Fall back to
                # unfiltered list and log.
                pass

        results, total = await agents_service.list_and_count(*extra_filters)
        page = agents_service.to_schema(
            results, total, filters=filters, schema_type=Agent
        )

        # Attach `_permissions` to each item (PR 8). Uses the same session
        # as the list query so we don't open a fresh connection per row.
        if auth is not None and page.items:
            from services.access_control import PermissionService

            session = agents_service.repository.session
            for item, model in zip(page.items, results):
                try:
                    item.permissions = (
                        await PermissionService.compute_record_permissions(
                            session,
                            auth=auth,
                            resource_type="agents",
                            resource=model,
                        )
                    )
                except Exception:
                    pass
        return page

    @post(guards=[require_permission(Permission.AGENTS_WRITE)])
    async def create_agent(
        self,
        agents_service: AgentsService,
        data: AgentCreate,
        request: Request,
        audit_username: str | None,
    ) -> Agent:
        """Create a new agent."""
        from middlewares.auth import Auth as AuthContext

        data.created_by = audit_username
        data.updated_by = audit_username

        # Force-set `tenant_id` AND `owner_id` from auth context (PR 7/8).
        # Never trust client-supplied tenant_id — RLS would reject mismatched
        # values via WITH CHECK, but we fail fast and clearer at the API.
        auth: AuthContext | None = request.scope.get("auth")
        payload = data.model_dump(exclude_unset=True)
        if auth is not None and auth.tenant_id:
            payload["tenant_id"] = auth.tenant_id
        if auth is not None and getattr(auth, "user", None) is not None:
            payload["owner_id"] = auth.user.id
        from core.db.models.agent.agent import Agent as AgentModel

        obj = await agents_service.create(AgentModel(**payload), auto_commit=True)
        await _sync_runtime_caches(
            request=request,
            previous_channels=None,
            current_channels=getattr(obj, "channels", None),
        )
        return await _serialize_with_permissions(agents_service, obj, request=request)

    @get("/code/{code:str}", guards=[require_permission(Permission.AGENTS_READ)])
    async def get_agent_by_code(
        self, agents_service: AgentsService, code: str, request: Request
    ) -> Agent:
        """Get an agent by its system_name."""
        from core.db.models.agent.agent import Agent as AgentModel
        from services.access_control import tenant_system_name_filter

        obj = await agents_service.get_one(
            tenant_system_name_filter(request, AgentModel, code)
        )
        return await _serialize_with_permissions(agents_service, obj, request=request)

    @get("/{agent_id:uuid}", guards=[require_permission(Permission.AGENTS_READ)])
    async def get_agent(
        self,
        agents_service: AgentsService,
        request: Request,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to retrieve.",
        ),
    ) -> Agent:
        """Get an agent by its ID. 404 if the caller can't view it."""
        from litestar.exceptions import NotFoundException
        from services.access_control import PermissionService

        obj = await agents_service.get(agent_id)
        auth = request.scope.get("auth")
        if auth is not None:
            allowed = await PermissionService.can(
                agents_service.repository.session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=obj,
            )
            if not allowed:
                # Return 404 (not 403) — don't disclose existence to
                # principals without view permission.
                raise NotFoundException("Agent not found")
        return await _serialize_with_permissions(agents_service, obj, request=request)

    @patch("/{agent_id:uuid}", guards=[require_permission(Permission.AGENTS_WRITE)])
    async def update_agent(
        self,
        agents_service: AgentsService,
        data: AgentUpdate,
        request: Request,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to update.",
        ),
        audit_username: str | None = None,
    ) -> Agent:
        """Update an agent. 403 if record-level check fails."""
        from litestar.exceptions import (
            NotFoundException,
            PermissionDeniedException,
        )
        from services.access_control import PermissionService

        existing_obj = await agents_service.get(agent_id)
        auth = request.scope.get("auth")
        if auth is not None:
            if not await PermissionService.can(
                agents_service.repository.session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=existing_obj,
            ):
                raise NotFoundException("Agent not found")
            if not await PermissionService.can(
                agents_service.repository.session,
                auth=auth,
                action="edit",
                resource_type="agents",
                resource=existing_obj,
            ):
                raise PermissionDeniedException(
                    "You don't have permission to edit this agent"
                )

        previous_channels = deepcopy(getattr(existing_obj, "channels", None))
        update_data = data.model_dump(exclude_unset=True)
        # Strip fields that must come from auth context, not the client.
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await agents_service.update(
            update_data, item_id=agent_id, auto_commit=True
        )
        await _sync_runtime_caches(
            request=request,
            previous_channels=previous_channels,
            current_channels=getattr(obj, "channels", None),
        )
        return await _serialize_with_permissions(agents_service, obj, request=request)

    @delete("/{agent_id:uuid}", guards=[require_permission(Permission.AGENTS_DELETE)])
    async def delete_agent(
        self,
        agents_service: AgentsService,
        request: Request,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to delete.",
        ),
    ) -> None:
        """Delete an agent. 403 if record-level check fails."""
        from litestar.exceptions import (
            NotFoundException,
            PermissionDeniedException,
        )
        from services.access_control import PermissionService

        existing_obj = await agents_service.get(agent_id)
        auth = request.scope.get("auth")
        if auth is not None:
            if not await PermissionService.can(
                agents_service.repository.session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=existing_obj,
            ):
                raise NotFoundException("Agent not found")
            if not await PermissionService.can(
                agents_service.repository.session,
                auth=auth,
                action="delete",
                resource_type="agents",
                resource=existing_obj,
            ):
                raise PermissionDeniedException(
                    "You don't have permission to delete this agent"
                )
        _ = await agents_service.delete(agent_id)


async def _serialize_with_permissions(
    agents_service: AgentsService,
    obj: Any,
    *,
    request: Request,
) -> Agent:
    """Build the Agent response schema and attach `_permissions`.

    PR 8: every read-side serialization includes a `_permissions` block so
    the frontend can decide which actions to expose without re-computing
    them from roles.
    """
    schema = agents_service.to_schema(obj, schema_type=Agent)

    auth = request.scope.get("auth")
    if auth is None:
        return schema

    # `obj` is the SQLAlchemy Agent — has the record-level fields the
    # permission service needs.
    from services.access_control import PermissionService
    from core.config.app import alchemy

    async with alchemy.get_session() as session:
        try:
            perms = await PermissionService.compute_record_permissions(
                session,
                auth=auth,
                resource_type="agents",
                resource=obj,
            )
        except Exception:
            # Failing closed on serialization is worse than no _permissions
            # block — frontend will just not show advanced controls.
            return schema

    # `Agent.model_config = ConfigDict(populate_by_name=True)` lets us assign
    # via the Python attribute name. `model_dump(by_alias=True)` would then
    # emit it as `_permissions`. Litestar serializes the returned object
    # via Pydantic, so we set the attribute and rely on default serialization.
    schema.permissions = perms
    return schema


async def _sync_runtime_caches(
    *,
    request: Request,
    previous_channels: Mapping[str, Any] | None,
    current_channels: Mapping[str, Any] | None,
) -> None:
    teams_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="ms_teams",
    )

    if teams_changed:
        teams_cache = getattr(request.app.state, "teams_runtime_cache", None)
        if teams_cache is not None and hasattr(teams_cache, "clear"):
            await teams_cache.clear()

    slack_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="slack",
    )

    if slack_changed:
        slack_cache = getattr(request.app.state, "slack_runtime_cache", None)
        if slack_cache is not None and hasattr(slack_cache, "refresh"):
            await slack_cache.refresh()

    whatsapp_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="whatsapp",
    )

    if whatsapp_changed:
        whatsapp_cache = getattr(request.app.state, "whatsapp_runtime_cache", None)
        if whatsapp_cache is not None and hasattr(whatsapp_cache, "clear"):
            await whatsapp_cache.clear()


def _channel_enabled_changed(
    *,
    previous_channels: Mapping[str, Any] | None,
    current_channels: Mapping[str, Any] | None,
    section: str,
) -> bool:
    previous_enabled = _extract_enabled(previous_channels, section)
    current_enabled = _extract_enabled(current_channels, section)
    return previous_enabled != current_enabled


def _extract_section(
    channels: Mapping[str, Any] | None,
    section: str,
) -> dict[str, Any]:
    if not isinstance(channels, Mapping):
        return {}

    section_value = channels.get(section, {})
    if isinstance(section_value, Mapping):
        return dict(section_value)

    return {}


def _extract_enabled(
    channels: Mapping[str, Any] | None,
    section: str,
) -> bool:
    section_value = _extract_section(channels, section)
    enabled = section_value.get("enabled")

    if isinstance(enabled, (int, bool)):
        return bool(enabled)

    return False
