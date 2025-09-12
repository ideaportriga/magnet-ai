"""
Service for agent conversation operations.
"""

from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.agent_conversation import AgentConversation

class AgentConversationService(service.SQLAlchemyAsyncRepositoryService[AgentConversation]):
    """Agent conversation service."""

    class Repo(repository.SQLAlchemyAsyncRepository[AgentConversation]):
        """Agent conversation repository."""

        model_type = AgentConversation

    repository_type = Repo