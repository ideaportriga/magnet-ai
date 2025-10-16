from logging import getLogger
from sqlalchemy import text
from core.config.app import alchemy


logger = getLogger(__name__)


async def resolve_teams_by_client_id(client_id: str) -> tuple[str | None, str | None, str | None]:
    """Resolve attributes by OAuth client_id stored in agents.variants.

    Returns (agent_system_name, tenant_id, secret_value).
    secret_value is returned for internal use (e.g., logging), do not expose in API responses.
    """
    sql = text(
        """
        SELECT a.system_name AS agent_system_name,
               elem->'value'->'credentials'->>'tenant_id' AS tenant_id,
               elem->'value'->'secrets_encrypted'->>'secret_value' AS secret_value
        FROM agents a,
             jsonb_array_elements(a.variants) AS elem
        WHERE elem->'value'->'credentials'->>'client_id' = :client_id
        LIMIT 1
        """
    )

    async with alchemy.get_session() as session:
        result = await session.execute(sql, {"client_id": client_id})
        row = result.first()

    if not row:
        return None, None, None

    return row.agent_system_name, row.tenant_id, row.secret_value


