"""Memory strategies for managing conversation context size.

Provides pluggable strategies to control how many / which messages
are passed to the LLM as context within the agent loop.
"""

from __future__ import annotations

from typing import Protocol

from services.agents.models import AgentConversationMessage

DEFAULT_LAST_N_MESSAGES = 10


class MemoryStrategy(Protocol):
    """Interface for conversation memory strategies."""

    def select_messages(
        self,
        messages: list[AgentConversationMessage],
    ) -> list[AgentConversationMessage]:
        """Return the subset of messages to use as LLM context."""
        ...


class LastNMessagesStrategy:
    """Keep only the last *n* messages for context.

    This is the default strategy.  The most recent message (the current
    user turn) is always included.
    """

    def __init__(self, n: int = DEFAULT_LAST_N_MESSAGES) -> None:
        self.n = n

    def select_messages(
        self,
        messages: list[AgentConversationMessage],
    ) -> list[AgentConversationMessage]:
        if len(messages) <= self.n:
            return messages
        return messages[-self.n :]
