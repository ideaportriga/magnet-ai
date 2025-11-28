import json
from urllib.parse import parse_qs
from logging import getLogger
from typing import Any

from litestar import Controller, Request, post
from litestar.exceptions import ValidationException
from pydantic import BaseModel, ConfigDict

from api.tags import TagNames
from services.agents.conversations import add_user_message, create_conversation
from services.agents.models import (
    AgentConversationMessageRole,
    AgentConversationWithMessagesPublic,
)
from services.agents.services import get_agent_by_system_name
from services.observability import (
    observability_context,
    observe,
    observability_overrides,
)

logger = getLogger(__name__)


class AskMagnetRequest(BaseModel):
    agent: str
    user_message_content: str
    user_id: str | None = None
    conversation_id: str | None = None
    trace_id: str | None = None

    model_config = ConfigDict(extra="ignore")


class AskMagnetResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    trace_id: str | None = None
    analytics_id: str | None = None


async def _extract_payload_from_request(
    request: Request,
    content_type: str,
    raw: bytes | bytearray | str | None,
) -> tuple[dict[str, Any], str]:
    payload: dict[str, Any] | None = None
    normalized_content_type = (content_type or "").split(";")[0].strip().lower()

    if raw and "application/json" in normalized_content_type:
        try:
            parsed_body = json.loads(
                raw.decode("utf-8", errors="replace")
                if isinstance(raw, (bytes, bytearray))
                else str(raw)
            )
            if isinstance(parsed_body, dict):
                payload = parsed_body
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode JSON body for agent conversation creation request."
            )

    if payload is None and normalized_content_type in {
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    }:
        try:
            form_data = await request.form()
        except Exception as exc:
            logger.warning(
                "Failed to parse form data for agent conversation creation request: %s",
                exc,
            )
        else:
            payload = {key: form_data[key] for key in form_data.keys()}

    if (
        payload is None
        and raw
        and normalized_content_type == "application/x-www-form-urlencoded"
    ):
        try:
            parsed_items = parse_qs(
                raw.decode("utf-8", errors="replace")
                if isinstance(raw, (bytes, bytearray))
                else str(raw)
            )
        except Exception:
            parsed_items = {}

        if parsed_items:
            payload = {
                key: values[0] if len(values) == 1 else values
                for key, values in parsed_items.items()
            }

    if payload is None and raw:
        try:
            parsed_body = json.loads(
                raw.decode("utf-8", errors="replace")
                if isinstance(raw, (bytes, bytearray))
                else str(raw)
            )
            if isinstance(parsed_body, dict):
                payload = parsed_body
        except json.JSONDecodeError:
            pass

    if not payload:
        raise ValidationException("Request body is required.")

    if (
        "body" in payload
        and isinstance(payload["body"], str)
        and not any(
            key in payload
            for key in ("agent", "user_message_content", "user_id", "conversation_id")
        )
    ):
        try:
            embedded_payload = json.loads(payload["body"])
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode JSON embedded in 'body' form field for agent conversation creation request."
            )
        else:
            if isinstance(embedded_payload, dict):
                payload = embedded_payload

    variables = payload.get("variables")
    if isinstance(variables, str):
        try:
            payload["variables"] = json.loads(variables)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode 'variables' field as JSON in agent conversation creation request; using raw string value."
            )

    return payload, normalized_content_type


@observe(
    name="The user asks a question to the agent",
    channel="production",
    source="Runtime API",
)
async def _process_ask_magnet_request(
    data: AskMagnetRequest,
    consumer_name: str | None = None,
) -> AskMagnetResponse:
    agent_config = await get_agent_by_system_name(data.agent)

    if consumer_name:
        observability_context.update_current_baggage(consumer_name=consumer_name)

    observability_context.update_current_trace(
        name=agent_config.name,
        type="agent",
        user_id=data.user_id,
    )

    if data.conversation_id:
        continuation = await add_user_message(
            agent_config.system_name,
            data.conversation_id,
            data.user_message_content,
        )
        assistant_message = continuation.assistant_message

        return AskMagnetResponse(
            conversation_id=data.conversation_id,
            message_id=str(assistant_message.id),
            content=assistant_message.content or "",
            trace_id=continuation.trace_id,
            analytics_id=str(continuation.analytics_id)
            if continuation.analytics_id is not None
            else None,
        )

    conversation: AgentConversationWithMessagesPublic = await create_conversation(
        agent_config,
        data.user_message_content,
        data.user_id,
    )

    assistant_message = next(
        (
            message
            for message in reversed(conversation.messages)
            if getattr(message, "role", None) == AgentConversationMessageRole.ASSISTANT
        ),
        None,
    )

    if assistant_message is None:
        raise ValidationException(
            "Assistant response is missing from the conversation."
        )

    return AskMagnetResponse(
        conversation_id=str(conversation.id),
        message_id=str(assistant_message.id),
        content=assistant_message.content,
        trace_id=conversation.trace_id,
        analytics_id=str(conversation.analytics_id)
        if conversation.analytics_id is not None
        else None,
    )


class AskMagnetController(Controller):
    path = "/ask_magnet"
    tags = [TagNames.UserAgentConversations]

    @post(
        summary="Accepts Ask Magnet form data",
        description=(
            "Receives form data for starting a new conversation with an agent or updating an existing conversation. Accepts only form-encoded payloads.",
        ),
    )
    async def ask_magnet(
        self,
        request: Request,
    ) -> AskMagnetResponse:
        headers = dict(request.headers)
        content_type = headers.get("content-type", "")
        consumer_name = request.headers.get("x-consumer-name")
        logger.info(f"AskMagnet consumer_name: {consumer_name}")
        raw = await request.body()
        try:
            body_preview = (
                raw[:200].decode("utf-8", errors="replace")
                if isinstance(raw, (bytes, bytearray))
                else str(raw)[:200]
            )
        except Exception:
            body_preview = "<unreadable>"

        logger.info(
            "AskMagnet create request: method=%s path=%s content_type=%s content_length=%s body_first_200=%s",
            request.method,
            request.url.path,
            content_type,
            headers.get("content-length"),
            body_preview,
        )

        payload, normalized_content_type = await _extract_payload_from_request(
            request, content_type, raw
        )

        if normalized_content_type not in {
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        }:
            raise ValidationException(
                "This endpoint accepts form submissions only. Please send data as form data."
            )

        request_model = AskMagnetRequest.model_validate(payload)

        observability_kwargs: dict[str, str | None] = {
            "trace_id": request_model.trace_id
        }
        if consumer_name:
            observability_kwargs["consumer_name"] = consumer_name

        response = await _process_ask_magnet_request(
            request_model,
            consumer_name=consumer_name,
            **observability_overrides(**observability_kwargs),
        )
        return response
