"""
Service for agent conversation operations.
"""

from __future__ import annotations

import logging
from typing import Any

from advanced_alchemy.extensions.litestar import repository, service
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from core.db.models.agent_conversation import AgentConversation
from utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class AgentConversationService(
    service.SQLAlchemyAsyncRepositoryService[AgentConversation]
):
    """Agent conversation service."""

    async def bump_processing_generation(
        self,
        db_session,
        conversation_id: str,
        *,
        append_message: dict[str, Any] | None = None,
        status: str | None = None,
        callback: dict[str, Any] | None = None,
    ) -> int | None:
        """Atomically start a new turn.

        Locks the conversation row, increments ``processing_generation`` (so any
        in-flight turn becomes stale), optionally appends a (user) message, sets
        the processing status and refreshes the callback config. Returns the new
        generation, or None if the conversation does not exist. The returned
        value is what a turn must still match at persist time to write its reply.
        """
        result = await db_session.execute(
            select(AgentConversation)
            .where(AgentConversation.id == conversation_id)
            .with_for_update()
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        conversation.processing_generation = (
            conversation.processing_generation or 0
        ) + 1

        if append_message is not None:
            messages = list(conversation.messages or [])
            messages.append(append_message)
            conversation.messages = messages
            flag_modified(conversation, "messages")
            conversation.last_user_message_at = utc_now()

        if status is not None:
            conversation.message_processing_status = status

        if callback is not None:
            conversation.callback = callback

        await db_session.commit()
        return conversation.processing_generation

    async def persist_turn_result_if_current(
        self,
        db_session,
        conversation_id: str,
        generation: int,
        *,
        append_message: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> bool:
        """Append a turn's result only if it is still the current generation.

        This is the multi-worker-safe guard: a turn started on any worker writes
        its assistant reply (and final status) only when no newer user message
        has superseded it. A superseded turn is silently discarded.
        """
        result = await db_session.execute(
            select(AgentConversation)
            .where(AgentConversation.id == conversation_id)
            .with_for_update()
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return False

        if (conversation.processing_generation or 0) != generation:
            logger.info(
                "Discarding superseded turn for conversation %s (gen %s != current %s)",
                conversation_id,
                generation,
                conversation.processing_generation,
            )
            return False

        if append_message is not None:
            messages = list(conversation.messages or [])
            messages.append(append_message)
            conversation.messages = messages
            flag_modified(conversation, "messages")

        if status is not None:
            conversation.message_processing_status = status

        await db_session.commit()
        return True

    async def update_message_content(
        self,
        db_session,
        conversation_id: str,
        message_id: str,
        content: str,
        edited_by: str | None = None,
    ) -> bool:
        """Override the content of a stored message (operator/external edit).

        Preserves the first-seen text in ``original_content`` and stamps audit
        fields. The corrected ``content`` is what subsequent turns feed to the
        LLM, since conversation context is rebuilt from the stored messages.
        """
        conversation = await db_session.get(AgentConversation, conversation_id)
        if not conversation or not conversation.messages:
            return False

        messages = (
            conversation.messages if isinstance(conversation.messages, list) else []
        )
        updated = False
        for message in messages:
            if str(message.get("id")) == str(message_id):
                if not message.get("is_operator_edited"):
                    message["original_content"] = message.get("content")
                message["content"] = content
                message["is_operator_edited"] = True
                message["edited_at"] = utc_now().isoformat()
                message["edited_by"] = edited_by
                flag_modified(conversation, "messages")
                updated = True
                break

        if updated:
            await db_session.commit()
        else:
            logger.warning(
                "update_message_content: message %s not found in conversation %s",
                message_id,
                conversation_id,
            )
        return updated

    async def update_message_feedback(
        self,
        db_session,
        conversation_id: str,
        message_id: str,
        feedback_data: dict[str, Any],
    ) -> bool:
        """
        Update feedback for a specific message in conversation messages.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_message_feedback] Called with conversation_id={conversation_id}, message_id={message_id}"
        )

        conversation = await db_session.get(AgentConversation, conversation_id)
        if not conversation:
            logger.warning(
                f"[update_message_feedback] Conversation not found: {conversation_id}"
            )
            return False

        if not conversation.messages:
            logger.warning(
                f"[update_message_feedback] Conversation {conversation_id} has no messages"
            )
            return False

        updated = False
        messages = (
            conversation.messages if isinstance(conversation.messages, list) else []
        )

        for message in messages:
            if str(message.get("id")) == str(message_id):
                logger.info(
                    f"[update_message_feedback] Found message {message_id}, updating feedback"
                )
                message["feedback"] = feedback_data
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(conversation, "messages")
                updated = True
                break

        if updated:
            logger.info(
                f"[update_message_feedback] Committing changes for conversation {conversation_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_message_feedback] Message {message_id} not found in conversation {conversation_id}"
            )
        return updated

    async def update_message_custom_feedback(
        self,
        db_session,
        conversation_id: str,
        message_id: str,
        custom_feedback_data: dict[str, Any],
    ) -> bool:
        """
        Update custom feedback for a specific message in conversation messages.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_message_custom_feedback] Called with conversation_id={conversation_id}, message_id={message_id}"
        )

        conversation = await db_session.get(AgentConversation, conversation_id)
        if not conversation:
            logger.warning(
                f"[update_message_custom_feedback] Conversation not found: {conversation_id}"
            )
            return False

        if not conversation.messages:
            logger.warning(
                f"[update_message_custom_feedback] Conversation {conversation_id} has no messages"
            )
            return False

        updated = False
        messages = (
            conversation.messages if isinstance(conversation.messages, list) else []
        )

        for message in messages:
            if str(message.get("id")) == str(message_id):
                logger.info(
                    f"[update_message_custom_feedback] Found message {message_id}, updating custom feedback"
                )
                message["custom_feedback"] = custom_feedback_data
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(conversation, "messages")
                updated = True
                break

        if updated:
            logger.info(
                f"[update_message_custom_feedback] Committing changes for conversation {conversation_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_message_custom_feedback] Message {message_id} not found in conversation {conversation_id}"
            )
        return updated

    async def update_message_copied_status(
        self,
        db_session,
        conversation_id: str,
        message_id: str,
        copied: bool = True,
    ) -> bool:
        """
        Update copied status for a specific message in conversation messages.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_message_copied_status] Called with conversation_id={conversation_id}, message_id={message_id}, copied={copied}"
        )

        conversation = await db_session.get(AgentConversation, conversation_id)
        if not conversation:
            logger.warning(
                f"[update_message_copied_status] Conversation not found: {conversation_id}"
            )
            return False

        if not conversation.messages:
            logger.warning(
                f"[update_message_copied_status] Conversation {conversation_id} has no messages"
            )
            return False

        updated = False
        messages = (
            conversation.messages if isinstance(conversation.messages, list) else []
        )

        for message in messages:
            if str(message.get("id")) == str(message_id):
                logger.info(
                    f"[update_message_copied_status] Found message {message_id}, updating copied status"
                )
                message["copied"] = copied
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(conversation, "messages")
                updated = True
                break

        if updated:
            logger.info(
                f"[update_message_copied_status] Committing changes for conversation {conversation_id}"
            )
            await db_session.commit()
        else:
            logger.warning(
                f"[update_message_copied_status] Message {message_id} not found in conversation {conversation_id}"
            )
        return updated

    async def update_conversation_status(
        self,
        db_session,
        conversation_id: str,
        status: str,
    ) -> bool:
        """
        Update status for a conversation.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"[update_conversation_status] Called with conversation_id={conversation_id}, status={status}"
        )

        conversation = await db_session.get(AgentConversation, conversation_id)
        if not conversation:
            logger.warning(
                f"[update_conversation_status] Conversation not found: {conversation_id}"
            )
            return False

        logger.info(
            f"[update_conversation_status] Found conversation {conversation_id}, updating status to {status}"
        )
        conversation.status = status

        logger.info(
            f"[update_conversation_status] Committing changes for conversation {conversation_id}"
        )
        await db_session.commit()
        return True

    class Repo(repository.SQLAlchemyAsyncRepository[AgentConversation]):
        """Agent conversation repository."""

        model_type = AgentConversation

    repository_type = Repo
