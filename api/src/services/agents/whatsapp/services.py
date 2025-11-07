from logging import getLogger
from sqlalchemy import text
from core.config.app import alchemy

from utils.secrets import decrypt_string


logger = getLogger(__name__)


async def resolve_whatsapp_by_phone_number_id(phone_number_id: str) -> tuple[str | None, str | None, str | None]:
    """Resolve WhatsApp credentials by phone_number_id stored in agent channels.

    Returns (agent_system_name, token, app_secret).
    Secrets are returned for internal use (e.g., logging), do not expose in API responses.
    """
    sql = text(
        """
        SELECT
            a.system_name AS agent_system_name,
            a.channels #>> '{whatsapp,token}'  AS token,
            a.channels #>> '{whatsapp,app_secret}' AS app_secret
        FROM agents a
            WHERE COALESCE(a.channels -> 'whatsapp' ->> 'phone_number_id', '') = :phone_number_id
            AND COALESCE((a.channels -> 'whatsapp' -> 'enabled')::boolean, false ) = true
        LIMIT 1
        """
    )

    async with alchemy.get_session() as session:
        result = await session.execute(sql, {"phone_number_id": phone_number_id})
        row = result.first()

    if not row:
        return None, None, None

    token = decrypt_string(row.token) if row.token else None
    app_secret = decrypt_string(row.app_secret) if row.app_secret else None

    return row.agent_system_name, token, app_secret


