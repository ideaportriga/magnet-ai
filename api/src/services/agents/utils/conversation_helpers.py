from __future__ import annotations

from logging import getLogger
from typing import Any, TypedDict

from services.agents.conversations import (
    add_user_message,
    create_conversation,
    get_last_conversation_by_client_id,
)
from services.agents.models import (
    AgentActionCallConfirmation,
    AgentConversationMessageRole,
)
from services.observability import observe, observability_context


logger = getLogger(__name__)


class ActionRequest(TypedDict):
    id: str
    action_message: str | None


class AssistantPayload(TypedDict):
    conversation_id: str | None
    trace_id: str | None
    message_id: str | None
    content: Any
    agent_system_name: str
    requires_confirmation: bool
    action_requests: list[ActionRequest]


def _extract_assistant_message(response: Any) -> Any:
    if not response:
        return None

    message = getattr(response, "assistant_message", None)
    if message:
        return message

    for candidate in (getattr(response, "messages", []) or []):
        role = getattr(candidate, "role", None)
        if role == AgentConversationMessageRole.ASSISTANT or str(role).lower() == "assistant":
            return candidate

    return None


def _get_action_requests(message: Any) -> list[ActionRequest]:
    if not message:
        return []

    results: list[ActionRequest] = []
    for request in (getattr(message, "action_call_requests", []) or []):
        request_id = str(getattr(request, "id", "") or "")
        if not request_id:
            continue
        results.append(
            {
                "id": request_id,
                "action_message": getattr(request, "action_message", None),
            }
        )
    return results


def _build_assistant_payload(
    conversation_id: str,
    message: Any,
    *,
    agent_system_name: str,
    trace_id: str | None = None,
) -> AssistantPayload:
    normalized_conversation_id = str(conversation_id or "") or None
    message_id = (str(getattr(message, "id", "")) or None) if message else None
    requests = _get_action_requests(message)
    payload: AssistantPayload = {
        "conversation_id": normalized_conversation_id,
        "message_id": message_id,
        "content": getattr(message, "content", None) if message else None,
        "agent_system_name": agent_system_name,
        "requires_confirmation": bool(requests),
        "action_requests": requests,
    }
    if trace_id:
        payload["trace_id"] = trace_id

    return payload

# TODO - refactor it
@observe(
    name="New user message",
    description="User sent a new message.",
    channel="production",
    source="Teams App",
)
async def _continue_conversation_for_obsevability(
    conversation_id: str | None,
    agent_system_name: str,
    aad_object_id: str,
    text: str,
    trace_id: str | None = None,
) -> AssistantPayload:
    """Continue or start an agent conversation and return the assistant's reply payload."""
    client_id = f"{aad_object_id}@{agent_system_name}"
    logger.info("[agents] _continue_conversation_for_obsevability started: client_id=%s", client_id)
    observability_context.update_current_trace(name=agent_system_name, type="agent")

    if conversation_id is None:
        try:
            resp = await create_conversation(
                agent_system_name_or_config=agent_system_name,
                content=text,
                client_id=client_id,
            )
            conv_id = str(getattr(resp, "id", "")) or ""
            assistant = _extract_assistant_message(resp)
            logger.info("[agents] created conversation %s", conv_id)
            return _build_assistant_payload(conv_id, assistant, agent_system_name=agent_system_name)
        except Exception as exc:
            logger.exception("[agents] create_conversation error for %s", client_id)
            raise exc

    try:
        resp = await add_user_message(
            agent_system_name_or_config=agent_system_name,
            conversation_or_id=conversation_id,
            user_message_content=text,
        )
        assistant = _extract_assistant_message(resp)
        logger.info("[agents] appended user message to %s", conversation_id)
        return _build_assistant_payload(conversation_id, assistant, agent_system_name=agent_system_name, trace_id=trace_id)
    except Exception as exc:
        logger.exception("[agents] add_user_message error for conversation %s", conversation_id)
        raise exc


async def continue_conversation(
    agent_system_name: str,
    aad_object_id: str,
    text: str,
) -> AssistantPayload:
    """Continue or start an agent conversation and return the assistant's reply payload."""
    client_id = f"{aad_object_id}@{agent_system_name}"
    logger.debug("[agents] continue_conversation started: client_id=%s", client_id)

    try:
        last = await get_last_conversation_by_client_id(client_id)
    except Exception as exc:
        logger.exception("[agents] failed to fetch last conversation for %s", client_id)
        raise exc

    if last:
        conv_id = str(getattr(last, "id", "")) or ""
        trace_id = str(getattr(last, "trace_id", "")) or ""
        return await _continue_conversation_for_obsevability(conversation_id=conv_id, agent_system_name=agent_system_name, aad_object_id=aad_object_id, text=text, trace_id=trace_id, _observability_overrides={"trace_id": trace_id})

    return await _continue_conversation_for_obsevability(conversation_id=None, agent_system_name=agent_system_name, aad_object_id=aad_object_id, text=text)

@observe(
    name="Action confirmation",
    description="User confirmed an action.",
    channel="production",
    source="Teams App",
)
async def handle_action_confirmation(
    agent_system_name: str,
    aad_object_id: str,
    conversation_id: str,
    request_ids: list[str],
    confirmed: bool,
) -> AssistantPayload | None:
    """Submit action call confirmations and return the follow-up assistant payload."""
    client_id = f"{aad_object_id}@{agent_system_name}"
    logger.info(
        "[agents] action confirmation: client_id=%s conversation_id=%s confirmed=%s request_ids=%s",
        client_id,
        conversation_id,
        confirmed,
        request_ids,
    )
    if confirmed:
        observability_context.update_current_trace(
            name=agent_system_name, type="agent", description='User confirmed an action.'
        )
    else:
        observability_context.update_current_trace(
            name=agent_system_name, type="agent", description='User rejected an action.'
        )

    confirmations = [
        AgentActionCallConfirmation(request_id=request_id, confirmed=confirmed)
        for request_id in request_ids
        if request_id
    ]

    if not confirmations:
        logger.warning(
            "[agents] action confirmation skipped: no valid request IDs for conversation %s",
            conversation_id,
        )
        return None

    try:
        response = await add_user_message(
            agent_system_name_or_config=agent_system_name,
            conversation_or_id=conversation_id,
            user_message_content=None,
            action_call_confirmations=confirmations,
        )
    except Exception:
        logger.exception(
            "[agents] add_user_message failed while submitting confirmations (conversation=%s)",
            conversation_id,
        )
        raise

    assistant = _extract_assistant_message(response)
    return _build_assistant_payload(conversation_id, assistant, agent_system_name=agent_system_name)


__all__ = [
    "AssistantPayload",
    "continue_conversation",
    "handle_action_confirmation",
]
