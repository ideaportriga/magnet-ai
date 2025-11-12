from dataclasses import dataclass
from logging import getLogger
from litestar.exceptions import NotFoundException

from services.agents.whatsapp.services import resolve_whatsapp_by_phone_number_id


logger = getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WhatsappCredentials:
    phone_number_id: str
    agent_system_name: str
    token: str
    app_secret: str


async def load_credentials(phone_number_id: str) -> WhatsappCredentials:
    agent_system_name, token, app_secret = await resolve_whatsapp_by_phone_number_id(
        phone_number_id
    )

    if not agent_system_name:
        raise NotFoundException(
            f"WhatsApp agent for phone_number_id '{phone_number_id}' not found"
        )

    if not token:
        raise NotFoundException(
            f"Missing WhatsApp access token for phone_number_id '{phone_number_id}'"
        )

    if not app_secret:
        raise NotFoundException(
            f"Missing WhatsApp app secret for phone_number_id '{phone_number_id}'"
        )

    logger.debug(
        "Resolved WhatsApp credentials for phone_number_id=%s agent=%s",
        phone_number_id,
        agent_system_name,
    )

    return WhatsappCredentials(
        phone_number_id=phone_number_id,
        agent_system_name=agent_system_name,
        token=token,
        app_secret=app_secret,
    )
