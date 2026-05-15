"""Parametrized coverage for the PR 10 tenant + record-level rollout.

For every entity rolled out in PR 10 (#1–#8) and the earlier PR 7 pilot
(`agents`), we assert the same three invariants — the ones each migration
template encodes:

  1. Cross-tenant SELECT under a different `app.tenant_id` returns zero rows
     (RLS USING clause).
  2. `(tenant_id, system_name)` partial UNIQUE allows the same system_name
     in two different tenants but rejects duplicates within one tenant.
  3. The `_populate_tenant_id` before_flush listener fills `tenant_id`
     from the contextvar when the caller omitted it.

Running these as parametrized cases means new rollouts only need a row in
`ROLLOUT_TABLES` to be covered. The agents file (`test_agents_rls.py`)
remains the source of truth for edge cases (GUC stripped, spoof rejection);
this file is the cross-entity smoke matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text


async def _drop_into_unprivileged_role(session) -> None:
    await session.execute(text("SET LOCAL ROLE magnet_test_app"))


@pytest.fixture
async def other_tenant(db_session):
    from core.db.models.tenant.tenant import Tenant

    t = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
    db_session.add(t)
    await db_session.flush()
    return t


# ---------------------------------------------------------------------------
# Per-entity build helpers — minimal valid construction for each table.
# Add a row here when a new entity joins the rollout; the matrix below will
# pick it up automatically.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RolloutCase:
    label: str
    table: str
    model_path: str  # dotted import path, e.g. "core.db.models.agent.agent.Agent"
    make_kwargs: Callable[[UUID, str], dict[str, Any]]


def _kwargs_simple(tenant_id: UUID, system_name: str) -> dict[str, Any]:
    return {
        "name": f"Test {system_name}",
        "system_name": system_name,
        "tenant_id": tenant_id,
    }


def _kwargs_agent(tenant_id: UUID, system_name: str) -> dict[str, Any]:
    return {
        **_kwargs_simple(tenant_id, system_name),
        "category": "default",
        "active_variant": "default",
        "variants": [{"name": "default", "system_prompt": "You are helpful."}],
        "channels": {},
    }


def _kwargs_collection(tenant_id: UUID, system_name: str) -> dict[str, Any]:
    return {**_kwargs_simple(tenant_id, system_name), "type": "documents"}


def _kwargs_api_server(tenant_id: UUID, system_name: str) -> dict[str, Any]:
    return {**_kwargs_simple(tenant_id, system_name), "url": "http://localhost:8080"}


def _kwargs_mcp_server(tenant_id: UUID, system_name: str) -> dict[str, Any]:
    return {
        **_kwargs_simple(tenant_id, system_name),
        "transport": "sse",
        "url": "http://localhost:9000",
    }


ROLLOUT_TABLES: list[RolloutCase] = [
    RolloutCase(
        label="agents",
        table="agents",
        model_path="core.db.models.agent.agent.Agent",
        make_kwargs=_kwargs_agent,
    ),
    RolloutCase(
        label="collections",
        table="collections",
        model_path="core.db.models.collection.collection.Collection",
        make_kwargs=_kwargs_collection,
    ),
    RolloutCase(
        label="prompts",
        table="prompts",
        model_path="core.db.models.prompt.prompt.Prompt",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="ai_apps",
        table="ai_apps",
        model_path="core.db.models.ai_app.ai_app.AIApp",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="rag_tools",
        table="rag_tools",
        model_path="core.db.models.rag_tool.rag_tool.RagTool",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="retrieval_tools",
        table="retrieval_tools",
        model_path="core.db.models.retrieval_tool.retrieval_tool.RetrievalTool",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="api_servers",
        table="api_servers",
        model_path="core.db.models.api_server.api_server.APIServer",
        make_kwargs=_kwargs_api_server,
    ),
    RolloutCase(
        label="mcp_servers",
        table="mcp_servers",
        model_path="core.db.models.mcp_server.mcp_server.MCPServer",
        make_kwargs=_kwargs_mcp_server,
    ),
    RolloutCase(
        label="evaluation_sets",
        table="evaluation_sets",
        model_path="core.db.models.evaluation_set.evaluation_set.EvaluationSet",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="deep_research_configs",
        table="deep_research_configs",
        model_path="core.db.models.deep_research.config.DeepResearchConfig",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="note_taker_settings",
        table="note_taker_settings",
        model_path="core.db.models.teams.note_taker_settings.NoteTakerSettings",
        make_kwargs=_kwargs_simple,
    ),
    RolloutCase(
        label="knowledge_graphs",
        table="knowledge_graphs",
        model_path="core.db.models.knowledge_graph.knowledge_graph.KnowledgeGraph",
        make_kwargs=_kwargs_simple,
    ),
]


def _resolve(model_path: str):
    module_path, _, attr = model_path.rpartition(".")
    module = __import__(module_path, fromlist=[attr])
    return getattr(module, attr)


# ---------------------------------------------------------------------------
# 1. Cross-tenant SELECT → zero rows
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    ROLLOUT_TABLES,
    ids=[c.label for c in ROLLOUT_TABLES],
)
async def test_cross_tenant_select_returns_zero_rows(
    case: RolloutCase, db_session, default_tenant, other_tenant
):
    from core.db.rls_context import apply_session_rls

    Model = _resolve(case.model_path)
    await _drop_into_unprivileged_role(db_session)

    # Create under "other" tenant (switch GUC first so WITH CHECK accepts).
    await apply_session_rls(db_session, tenant_id=str(other_tenant.id))
    sys_name = f"{case.label}-{uuid4().hex[:6]}"
    obj = Model(**case.make_kwargs(other_tenant.id, sys_name))
    db_session.add(obj)
    await db_session.flush()
    obj_id = obj.id
    db_session.expunge(obj)

    # Re-context to default tenant and query for the row by id.
    await apply_session_rls(db_session, tenant_id=str(default_tenant.id))
    rows = (
        (await db_session.execute(select(Model).where(Model.id == obj_id)))
        .scalars()
        .all()
    )
    assert rows == [], f"{case.label}: cross-tenant row should not be visible"


# ---------------------------------------------------------------------------
# 2. Per-tenant UNIQUE on (tenant_id, system_name)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    ROLLOUT_TABLES,
    ids=[c.label for c in ROLLOUT_TABLES],
)
async def test_partial_unique_allows_same_system_name_across_tenants(
    case: RolloutCase, db_session, default_tenant, other_tenant
):
    from core.db.rls_context import apply_session_rls

    Model = _resolve(case.model_path)
    await _drop_into_unprivileged_role(db_session)
    shared = f"shared-{case.label}-{uuid4().hex[:6]}"

    # Insert in default tenant.
    db_session.add(Model(**case.make_kwargs(default_tenant.id, shared)))
    await db_session.flush()

    # Insert same system_name in other tenant — must succeed.
    await apply_session_rls(db_session, tenant_id=str(other_tenant.id))
    db_session.add(Model(**case.make_kwargs(other_tenant.id, shared)))
    await db_session.flush()


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    ROLLOUT_TABLES,
    ids=[c.label for c in ROLLOUT_TABLES],
)
async def test_duplicate_system_name_in_same_tenant_rejected(
    case: RolloutCase, db_session, default_tenant
):
    Model = _resolve(case.model_path)
    await _drop_into_unprivileged_role(db_session)
    shared = f"dup-{case.label}-{uuid4().hex[:6]}"

    db_session.add(Model(**case.make_kwargs(default_tenant.id, shared)))
    await db_session.flush()

    db_session.add(Model(**case.make_kwargs(default_tenant.id, shared)))
    with pytest.raises(Exception):
        await db_session.flush()
    await db_session.rollback()


# ---------------------------------------------------------------------------
# 3. _populate_tenant_id before_flush safety net
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    ROLLOUT_TABLES,
    ids=[c.label for c in ROLLOUT_TABLES],
)
async def test_autopopulate_listener_fills_tenant_id_when_omitted(
    case: RolloutCase, db_session, default_tenant
):
    """If the contextvar is set and the caller forgot tenant_id, the listener
    fills it before INSERT. Mirrors what `service.create({...})` calls do."""
    Model = _resolve(case.model_path)
    kwargs = case.make_kwargs(default_tenant.id, f"{case.label}-{uuid4().hex[:6]}")
    kwargs.pop("tenant_id", None)

    obj = Model(**kwargs)
    db_session.add(obj)
    await db_session.flush()

    # Listener should have stamped the GUC's tenant id on the row.
    # Compare as strings — the listener stores the contextvar value (str)
    # while `default_tenant.id` is a UUID object.
    assert str(obj.tenant_id) == str(default_tenant.id)
