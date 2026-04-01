from logging import getLogger

from sqlalchemy import func, select

from core.config.app import alchemy
from core.db.models.agent.agent import Agent
from utils.secrets import decrypt_string

logger = getLogger(__name__)


async def resolve_whatsapp_by_phone_number_id(
    phone_number_id: str,
) -> tuple[str | None, str | None, str | None]:
    """Resolve WhatsApp credentials by phone_number_id stored in agent channels.

    Returns (agent_system_name, token, app_secret).
    Secrets are returned for internal use (e.g., logging), do not expose in API responses.
    """
    wa = Agent.channels["whatsapp"]

    stmt = (
        select(
            Agent.system_name.label("agent_system_name"),
            wa["token"].astext.label("token"),
            wa["app_secret"].astext.label("app_secret"),
        )
        .where(func.coalesce(wa["phone_number_id"].astext, "") == phone_number_id)
        .where(func.coalesce(wa["enabled"].as_boolean(), False).is_(True))
        .limit(1)
    )

    async with alchemy.get_session() as session:
        result = await session.execute(stmt)
        row = result.first()

    if not row:
        return None, None, None

    token = decrypt_string(row.token) if row.token else None
    app_secret = decrypt_string(row.app_secret) if row.app_secret else None

    return row.agent_system_name, token, app_secret
