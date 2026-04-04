"""Agent and AgentConversation factories."""

from __future__ import annotations

import factory

from core.db.models.agent import Agent
from core.db.models.agent_conversation import AgentConversation

from .base import BaseFactory


class AgentFactory(BaseFactory):
    class Meta:
        model = Agent

    name = factory.Sequence(lambda n: f"Agent {n}")
    system_name = factory.Sequence(lambda n: f"agent-{n}")
    description = factory.Faker("sentence")
    category = "default"
    active_variant = "default"
    variants = factory.LazyFunction(
        lambda: [{"name": "default", "system_prompt": "You are a helpful assistant."}]
    )
    channels = factory.LazyFunction(dict)


class AgentConversationFactory(BaseFactory):
    class Meta:
        model = AgentConversation

    agent = factory.Sequence(lambda n: f"agent-{n}")
    client_id = factory.Faker("uuid4")
    status = "active"
    messages = factory.LazyFunction(list)
