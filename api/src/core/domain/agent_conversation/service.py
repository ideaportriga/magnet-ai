"""
Service for agent conversation operations.
"""

from __future__ import annotations

from typing import Any

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.agent_conversation import AgentConversation


class AgentConversationService(
    service.SQLAlchemyAsyncRepositoryService[AgentConversation]
):
    """Agent conversation service."""

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
