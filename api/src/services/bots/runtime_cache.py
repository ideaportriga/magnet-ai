import asyncio
from typing import Dict

from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration, AuthTypes, TurnState
from microsoft_agents.hosting.core.storage import MemoryStorage
from microsoft_agents.hosting.core.rest_channel_service_client_factory import (
    RestChannelServiceClientFactory,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalAuth

from .config import SCOPE, ISSUER, load_credentials
from .static_connections import StaticConnections
from .teams_handlers import register_handlers
from .runtime import BotRuntime


class BotRuntimeCache:
    """Bot runtimes keyed by audience."""

    def __init__(self) -> None:
        self._runtimes: Dict[str, BotRuntime] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, audience: str) -> BotRuntime:
        print ("getting or creating bot runtime", audience) # TOOD - REMOVE Print
        async with self._lock:
            runtime = self._runtimes.get(audience)
            if runtime is not None:
                print("bot runtime already exists") # TOOD - REMOVE Print
                return runtime
            runtime = await self._build_runtime(audience)
            self._runtimes[audience] = runtime
            return runtime

    async def _build_runtime(self, audience: str) -> BotRuntime:
        print ("building bot runtime", audience) # TOOD - REMOVE Print
        credentials = await load_credentials(audience)

        auth_config = AgentAuthConfiguration(
            client_id=credentials.audience,
            client_secret=credentials.client_secret,
            tenant_id=credentials.tenant_id,
        )
        auth_config.AUTH_TYPE = AuthTypes.client_secret
        auth_config.SCOPES = SCOPE

        validation_config = AgentAuthConfiguration(
            client_id=credentials.audience,
            issuers=ISSUER,
        )

        token_provider = MsalAuth(auth_config)
        channel_factory = RestChannelServiceClientFactory(StaticConnections(token_provider))
        adapter = CloudAdapter(channel_service_client_factory=channel_factory)

        agent_app = AgentApplication[TurnState](storage=MemoryStorage(), adapter=adapter, start_typing_timer=False)
        register_handlers(agent_app, agent_system_name=credentials.agent_system_name)

        return BotRuntime(
            validation_config=validation_config,
            adapter=adapter,
            agent_app=agent_app,
        )
