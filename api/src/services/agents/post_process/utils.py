import json
from logging import getLogger
from typing import Any

from dateutil import parser as date_parser

from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.observability import observe
from stores import RecordNotFoundError

logger = getLogger(__name__)


async def extract_analytics_from_conversation(
    conversation_or_id: dict | str,
) -> dict[str, Any]:
    from services.agents.conversations.services import get_conversation_by_id

    if isinstance(conversation_or_id, str):
        conversation = await get_conversation_by_id(conversation_id=conversation_or_id)
    else:
        conversation = conversation_or_id

    messages = conversation.get("messages", [])

    # avg_tool_call_latency

    total_latency = 0
    latency_count = 0

    # topics
    topic_set = set()

    # dislikes & likes
    dislikes = 0
    likes = 0

    for msg in messages:
        # feedback
        feedback = msg.get("feedback")
        if feedback and feedback.get("type"):
            if feedback["type"] == "dislike":
                dislikes += 1
            if feedback["type"] == "like":
                likes += 1

        # steps
        run = msg.get("run")
        steps = run.get("steps") if run else None
        if steps and isinstance(steps, list) and steps:
            first_started_at = steps[0].get("started_at")
            last_completed_at = steps[-1].get("completed_at")
            if first_started_at and last_completed_at:
                try:
                    # Parse datetime strings to datetime objects
                    dt_first = (
                        date_parser.parse(first_started_at)
                        if isinstance(first_started_at, str)
                        else first_started_at
                    )
                    dt_last = (
                        date_parser.parse(last_completed_at)
                        if isinstance(last_completed_at, str)
                        else last_completed_at
                    )
                    total_latency += (dt_last - dt_first).total_seconds() * 1000
                    latency_count += 1
                except Exception as e:
                    print(
                        f"Error parsing datetime in extract_metrics_from_conversation: {e}",
                    )
            # topics
            for step in steps:
                topic = None
                details = step.get("details")
                if details and details.get("topic"):
                    topic_val = details["topic"]
                    if isinstance(topic_val, str):
                        topic = topic_val
                    elif isinstance(topic_val, dict) and topic_val.get("system_name"):
                        topic = topic_val["system_name"]
                if topic:
                    topic_set.add(topic)

    avg_tool_call_latency = (
        (total_latency / latency_count) if latency_count > 0 else None
    )
    messages_count = len(messages)

    return {
        "avg_tool_call_latency": avg_tool_call_latency,
        "topics": list(topic_set),
        "dislikes": dislikes,
        "likes": likes,
        "messages_count": messages_count,
    }


def extract_conversation_text(
    conversation: dict,
) -> str:
    messages = conversation.get("messages", [])
    if len(messages) > 6:
        messages = messages[-6:]
    return "\n".join(
        # prefix with speaker type if available
        (
            f"{msg.get('type')}: {msg.get('content', '') if msg.get('content', '') is not None else ''}"
            if msg.get("type")
            else (msg.get("content", "") if msg.get("content", "") is not None else "")
        )
        for msg in messages
    )


async def _post_process(prompt_template_system_name: str, conversation: str):
    """Calls prompt_template and extracts sentiment and resolution_status from the response.
    Returns a dict with keys: sentiment, resolution_status.
    """
    prompt_template_config = await get_prompt_template_by_system_name_flat(
        prompt_template_system_name=prompt_template_system_name,
    )
    prompt_template_values = {
        "CONVERSATION": conversation,
    }
    chat_completion, _ = await create_chat_completion_from_prompt_template(
        prompt_template_config=prompt_template_config,
        prompt_template_values=prompt_template_values,
        additional_messages=[
            {
                "role": "user",
                "content": conversation,
            },
        ],
    )

    # Parse result with error handling
    content = chat_completion.choices[0].message.content
    if not content or not content.strip():
        return {}

    try:
        result = json.loads(content)
    except Exception:
        return {}

    return result


@observe(
    name="Post-process conversation",
    description="Post processing an existing conversation.",
    channel="production",
    source="Runtime API App",
)
async def post_process_conversation(
    conversation_or_id: dict[str, Any] | str, prompt_template_system_name: str | None
) -> dict:
    """Post-processes the conversations using the specified prompt template.
    Returns a dict with keys: sentiment, resolution_status.
    """

    from services.agents.conversations.services import get_conversation_by_id

    if isinstance(conversation_or_id, str):
        conversation = await get_conversation_by_id(conversation_id=conversation_or_id)
    else:
        conversation = conversation_or_id

    if not conversation:
        raise RecordNotFoundError()

    prompt_template_system_name = prompt_template_system_name or "PP_CONVERSATION"

    conversation_text = extract_conversation_text(conversation)

    # Call heavy post processing to get smart analytics, generated by LLM
    slow_post_processing = await _post_process(
        prompt_template_system_name, conversation_text
    )

    analytics_id = conversation.get("analytics_id")

    if analytics_id:
        # Update analytics with metrics service
        from core.config.app import alchemy
        from core.domain.metrics.service import MetricsService

        analytics_fields = {}

        for k, v in slow_post_processing.items():
            analytics_fields[f"conversation_data.{k}"] = v

        # Call lite post processing to get basic analytics
        fast_post_processing = await extract_analytics_from_conversation(conversation)
        for k, v in fast_post_processing.items():
            analytics_fields[f"conversation_data.{k}"] = v

        # Update analytics with closed status
        analytics_fields["extra_data.status"] = "Closed"

        # Update analytics with analytics data using metrics service
        async with alchemy.get_session() as session:
            metrics_service = MetricsService(session=session)
            await metrics_service.update_metric_fields(
                db_session=session,
                metric_id=analytics_id,
                fields_to_update=analytics_fields,
            )
    else:
        logger.warning(
            f"Conversation {conversation.get('_id')} doesn't have an analytics reference, skipping analytics update"
        )

    # Update conversation status to closed using agent_conversation domain
    from core.config.app import alchemy
    from core.domain.agent_conversation.service import AgentConversationService

    conversation_id = str(conversation.get("id") or conversation.get("_id"))
    async with alchemy.get_session() as session:
        service = AgentConversationService(session=session)
        await service.update_conversation_status(
            db_session=session,
            conversation_id=conversation_id,
            status="Closed",
        )

    return slow_post_processing


## How post_process should work for agents

# 1. A job is started that runs once a day
# 2. Find all agents that have a conversation closure interval
# 3. For each agent with a conversation closure interval, find all conversations where the time since last update exceeds the conversation closure interval
# 4. For each conversation where the time since last update exceeds the conversation closure interval, run post_process
# 5. Post_process updates the metric with additional data and sets the conversation status to closed
