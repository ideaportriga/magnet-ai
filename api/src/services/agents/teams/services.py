from logging import getLogger

from sqlalchemy import func, select

from core.config.app import alchemy
from core.db.models.agent.agent import Agent
from utils.secrets import decrypt_string

logger = getLogger(__name__)


async def resolve_teams_by_client_id(
    client_id: str,
) -> tuple[str | None, str | None, str | None]:
    """Resolve attributes by OAuth client_id stored in agents.variants.

    Returns (agent_system_name, azure_tenant_id, secret_value).

    `azure_tenant_id` is the Azure AD tenant of the Teams app (NOT our
    organization-tenant). The stored JSON key remains `tenant_id` for wire
    compatibility — only Python identifiers were renamed.

    secret_value is returned for internal use (e.g., logging), do not expose
    in API responses.
    """
    ms = Agent.channels["ms_teams"]

    stmt = (
        select(
            Agent.system_name.label("agent_system_name"),
            # JSON key stays `tenant_id` (see MsTeamsChannelBase alias);
            # we relabel the column to azure_tenant_id for clarity in code.
            ms["tenant_id"].astext.label("azure_tenant_id"),
            ms["secret_value"].astext.label("secret_value"),
        )
        .where(func.coalesce(ms["client_id"].astext, "") == client_id)
        .where(func.coalesce(ms["enabled"].as_boolean(), False).is_(True))
        .limit(1)
    )

    async with alchemy.get_session() as session:
        result = await session.execute(stmt)
        row = result.first()

    if not row:
        return None, None, None

    return row.agent_system_name, row.azure_tenant_id, decrypt_string(row.secret_value)
