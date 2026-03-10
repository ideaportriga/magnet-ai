"""Conversation classification — determines user intent and selects the relevant topic."""

import json
import re
from logging import getLogger
from typing import Final

from services.agents.models import (
    AgentConversationClassification,
    AgentConversationMessage,
    AgentTopic,
    ConversationIntent,
)
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template

logger = getLogger(__name__)

_MAX_CLASSIFICATION_ATTEMPTS: Final[int] = 3


def _extract_json_string(text: str) -> str:
    """Best-effort extraction of a JSON object from LLM output.

    Handles common quirks: code fences, leading prose, trailing text,
    trailing commas, and single-line comments inside JSON.
    """
    stripped = text.strip()
    if not stripped:
        return stripped

    # Strip markdown code fences (```json ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()

    # Try to isolate the outermost JSON object
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        stripped = stripped[start : end + 1]

    # Fix common hallucination patterns
    # Remove trailing commas before } or ]
    stripped = re.sub(r",\s*([}\]])", r"\1", stripped)
    # Remove single-line // comments
    stripped = re.sub(r"//[^\n]*", "", stripped)

    # Handle wrapper pattern: {"final": "{...}"} or {"result": "{...}"} etc.
    # Some models wrap the actual JSON in a string value under a known key.
    try:
        outer = json.loads(stripped)
        if isinstance(outer, dict):
            for key in ("final", "result", "output", "response", "json", "answer"):
                inner_candidate = outer.get(key)
                if isinstance(inner_candidate, str):
                    inner = inner_candidate.strip()
                    if inner.startswith("{"):
                        stripped = inner
                        break
    except (json.JSONDecodeError, ValueError):
        pass

    return stripped


@observe(
    name="Determine intent & topic",
    description="Before processing user prompt, agent determines user's intent and conversation topic.",
)
async def classify_conversation(
    prompt_template: str,
    messages: list[AgentConversationMessage],
    topics: list[AgentTopic],
) -> AgentConversationClassification:
    valid_topic_system_names: set[str] = (
        {t.system_name for t in topics} if topics else set()
    )

    topic_definitions = "No topics."
    topic_system_names = ""

    if topics:
        topic_definitions = [
            {
                "system_name": topic.system_name,
                "name": topic.name,
                "description": topic.description,
            }
            for topic in topics
        ]

        topic_system_names = [topic.system_name for topic in topics]

    clean_conversation = [
        {"role": message.role, "content": message.content} for message in messages
    ]

    last_error: Exception | None = None
    last_result: AgentConversationClassification | None = None

    for attempt in range(_MAX_CLASSIFICATION_ATTEMPTS):
        template_additional_messages = [
            {
                "role": "user",
                "content": json.dumps(clean_conversation, indent=2, ensure_ascii=False),
            },
        ]

        # On retry, inject the parse error so the LLM can correct its output
        if attempt > 0 and last_error is not None:
            template_additional_messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous response could not be parsed. Error: {last_error}\n"
                        "Please return ONLY a valid JSON object matching the expected schema."
                    ),
                },
            )

        prompt_template_result = await execute_prompt_template(
            system_name_or_config=prompt_template,
            template_values={
                "TOPIC_DEFINITIONS": topic_definitions,
                "TOPIC_SYSTEM_NAMES": topic_system_names,
            },
            template_additional_messages=template_additional_messages,
        )

        raw_content = prompt_template_result.content or ""
        cleaned = _extract_json_string(raw_content)

        try:
            parsed = AgentConversationClassification.model_validate_json(cleaned)
            last_result = parsed

            # Validate: if intent is "topic", the topic must exist
            if parsed.intent == ConversationIntent.TOPIC:
                if not parsed.topic:
                    raise ValueError(
                        "Classification returned intent='topic' but topic is null"
                    )
                if parsed.topic not in valid_topic_system_names:
                    raise ValueError(
                        f"Classification returned unknown topic '{parsed.topic}'. "
                        f"Valid: {sorted(valid_topic_system_names)}"
                    )

            observability_context.update_current_span(
                input={
                    "User message": clean_conversation[-1]["content"],
                },
                output={
                    "Intent": parsed.intent,
                    "Topic": parsed.topic.upper() if parsed.topic else None,
                    "Reasoning": parsed.reason,
                    "Confidence": parsed.confidence,
                },
            )
            return parsed
        except Exception as e:
            last_error = e
            logger.warning(
                "Classification attempt %d/%d failed: %s (raw=%s)",
                attempt + 1,
                _MAX_CLASSIFICATION_ATTEMPTS,
                e,
                raw_content[:200],
            )

    # All retries exhausted — return a safe fallback classification
    # instead of crashing. Use the last LLM-generated reason as assistant_message
    # so the response is in the conversation's language.
    logger.warning(
        "Classification failed after %d attempts, falling back to REQUEST_NOT_CLEAR",
        _MAX_CLASSIFICATION_ATTEMPTS,
    )
    if last_result and isinstance(last_result, AgentConversationClassification):
        last_result.intent = ConversationIntent.REQUEST_NOT_CLEAR
        last_result.topic = None
        if not last_result.assistant_message:
            last_result.assistant_message = last_result.reason
        return last_result

    fallback_reason = str(last_error) if last_error else "Classification failed"
    return AgentConversationClassification(
        intent=ConversationIntent.REQUEST_NOT_CLEAR,
        reason=fallback_reason,
        assistant_message=fallback_reason,
    )
