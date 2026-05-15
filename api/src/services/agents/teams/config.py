from dataclasses import dataclass
from logging import getLogger

from litestar.exceptions import NotFoundException

from services.agents.teams.services import resolve_teams_by_client_id

logger = getLogger(__name__)


SCOPE = ["https://api.botframework.com/.default"]
NOTE_TAKER_GRAPH_SCOPES = [
    # "Chat.ReadBasic",
    # "Files.Read.All",
    "offline_access",
    "OnlineMeetingRecording.Read.All",
    "OnlineMeetings.Read",
    "openid",
    "profile",
]
ISSUER = ["https://api.botframework.com"]


@dataclass(frozen=True, slots=True)
class ClientCredentials:
    """Resolved credentials for a configured audience.

    `azure_tenant_id` is the Azure AD tenant of the Teams bot/app — not our
    own organization-tenant. See `docs/access-control-tenancy-plan-v2.md`
    PR 3 for the naming convention.
    """

    audience: str
    client_secret: str
    azure_tenant_id: str
    agent_system_name: str


async def load_credentials(audience: str) -> ClientCredentials:
    agent_system_name, azure_tenant_id, secret_value = await resolve_teams_by_client_id(
        audience
    )
    if not agent_system_name:
        raise NotFoundException(f"Agent with client_id '{audience}' not found")
    if not secret_value or not azure_tenant_id:
        raise NotFoundException(
            f"Missing client_secret or tenant_id for audience '{audience}'"
        )

    masked_secret_value = secret_value[:4] + "-***-" + secret_value[-4:]
    logger.info(
        "Resolved secret and tenant_id for client_id=%s: %s and %s",
        audience,
        azure_tenant_id,
        masked_secret_value,
    )

    return ClientCredentials(
        audience=audience,
        client_secret=secret_value,
        azure_tenant_id=azure_tenant_id,
        agent_system_name=agent_system_name,
    )
