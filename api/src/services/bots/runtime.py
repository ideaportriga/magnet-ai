from dataclasses import dataclass

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration, TurnState


@dataclass(slots=True)
class BotRuntime:
    """Container for a lazily created bot runtimes."""

    validation_config: AgentAuthConfiguration
    adapter: CloudAdapter
    agent_app: AgentApplication[TurnState]
