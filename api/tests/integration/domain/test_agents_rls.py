"""Integration tests for PR 7 — RLS tenant isolation on `agents`.

These run against the real Postgres container with RLS enabled and FORCED
in conftest. Each test switches into a non-priv role (`magnet_test_app`)
because the default test connection is superuser and superusers always
bypass RLS regardless of FORCE. Production runtime never runs as superuser.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select, text


async def _drop_into_unprivileged_role(session) -> None:
    """SET LOCAL ROLE to the non-priv test role so RLS actually applies."""
    await session.execute(text("SET LOCAL ROLE magnet_test_app"))


@pytest.fixture
async def other_tenant(db_session):
    """Create a second tenant for cross-tenant scenarios."""
    from core.db.models.tenant.tenant import Tenant

    t = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
    db_session.add(t)
    await db_session.flush()
    return t


def _make_agent(tenant_id, system_name=None):
    from core.db.models.agent.agent import Agent

    return Agent(
        name=f"Agent {uuid4().hex[:6]}",
        system_name=system_name or f"agent-{uuid4().hex[:8]}",
        tenant_id=tenant_id,
        category="default",
        active_variant="default",
        variants=[{"name": "default", "system_prompt": "You are a helpful assistant."}],
        channels={},
    )


@pytest.mark.integration
class TestAgentsTenantIsolation:
    async def test_default_tenant_sees_its_own_agent(self, db_session, default_tenant):
        from core.db.models.agent.agent import Agent

        await _drop_into_unprivileged_role(db_session)
        agent = _make_agent(default_tenant.id)
        db_session.add(agent)
        await db_session.flush()

        rows = (
            (await db_session.execute(select(Agent).where(Agent.id == agent.id)))
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].tenant_id == default_tenant.id

    async def test_cross_tenant_select_returns_zero_rows(
        self, db_session, default_tenant, other_tenant
    ):
        """An agent created under tenant B is invisible under tenant A's GUC."""
        from core.db.rls_context import apply_session_rls
        from core.db.models.agent.agent import Agent

        # Drop priv first; otherwise INSERT under other_tenant from superuser
        # would bypass WITH CHECK and create the row without RLS attention.
        await _drop_into_unprivileged_role(db_session)

        await apply_session_rls(db_session, tenant_id=str(other_tenant.id))
        b_agent = _make_agent(other_tenant.id)
        db_session.add(b_agent)
        await db_session.flush()
        b_id = b_agent.id
        db_session.expunge(b_agent)

        await apply_session_rls(db_session, tenant_id=str(default_tenant.id))
        rows = (
            (await db_session.execute(select(Agent).where(Agent.id == b_id)))
            .scalars()
            .all()
        )
        assert rows == []

    async def test_insert_spoofing_other_tenant_rejected(
        self, db_session, default_tenant, other_tenant
    ):
        """WITH CHECK rejects INSERTs whose tenant_id ≠ current GUC."""
        await _drop_into_unprivileged_role(db_session)
        spoof = _make_agent(other_tenant.id)
        db_session.add(spoof)
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    async def test_no_guc_means_no_rows(self, db_session, default_tenant):
        """Without `app.tenant_id`, USING matches nothing → zero rows."""
        from core.db.rls_context import apply_session_rls
        from core.db.models.agent.agent import Agent

        # Seed an agent under default tenant (as superuser to avoid the
        # cross-action complexity; the test that matters is the SELECT
        # below under a stripped GUC and non-priv role).
        agent = _make_agent(default_tenant.id)
        db_session.add(agent)
        await db_session.flush()

        # Drop priv + clear the GUC. Emulates a worker that forgot to
        # propagate tenant_id. RLS hides everything.
        await _drop_into_unprivileged_role(db_session)
        await apply_session_rls(db_session, tenant_id=None)
        rows = (await db_session.execute(select(Agent))).scalars().all()
        assert rows == []

    async def test_partial_unique_allows_same_system_name_in_different_tenants(
        self, db_session, default_tenant, other_tenant
    ):
        """`(tenant_id, system_name)` UNIQUE — same system_name across tenants OK."""
        from core.db.rls_context import apply_session_rls
        from core.db.models.agent.agent import Agent

        await _drop_into_unprivileged_role(db_session)
        shared_name = f"shared-{uuid4().hex[:6]}"

        a = _make_agent(default_tenant.id, system_name=shared_name)
        db_session.add(a)
        await db_session.flush()

        await apply_session_rls(db_session, tenant_id=str(other_tenant.id))
        b = _make_agent(other_tenant.id, system_name=shared_name)
        db_session.add(b)
        await db_session.flush()

        from_other = (
            (
                await db_session.execute(
                    select(Agent).where(Agent.system_name == shared_name)
                )
            )
            .scalars()
            .all()
        )
        assert len(from_other) == 1
        assert from_other[0].tenant_id == other_tenant.id

        await apply_session_rls(db_session, tenant_id=str(default_tenant.id))
        from_default = (
            (
                await db_session.execute(
                    select(Agent).where(Agent.system_name == shared_name)
                )
            )
            .scalars()
            .all()
        )
        assert len(from_default) == 1
        assert from_default[0].tenant_id == default_tenant.id

    async def test_duplicate_system_name_in_same_tenant_rejected(
        self, db_session, default_tenant
    ):
        """Same-tenant duplicate system_name fails (partial UNIQUE)."""
        await _drop_into_unprivileged_role(db_session)
        shared = f"dup-{uuid4().hex[:6]}"
        db_session.add(_make_agent(default_tenant.id, system_name=shared))
        await db_session.flush()

        db_session.add(_make_agent(default_tenant.id, system_name=shared))
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()
