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

    Returns (agent_system_name, tenant_id, secret_value).
    secret_value is returned for internal use (e.g., logging), do not expose in API responses.
    """
    ms = Agent.channels["ms_teams"]

    stmt = (
        select(
            Agent.system_name.label("agent_system_name"),
            ms["tenant_id"].astext.label("tenant_id"),
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

    return row.agent_system_name, row.tenant_id, decrypt_string(row.secret_value)
