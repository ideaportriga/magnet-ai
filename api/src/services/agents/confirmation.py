"""Action call confirmation handling."""

from logging import getLogger

from services.agents.actions.execute import execute_agent_action
from services.agents.models import (
    AgentActionCallConfirmation,
    AgentActionCallRequest,
    AgentActionCallResponse,
    AgentConversationRunStep,
    AgentConversationRunStepTopicActionCall,
    AgentTopicActionCall,
)
from services.agents.topic_execution import _sanitize_action_error
from utils.datetime_utils import utc_now

logger = getLogger(__name__)


async def create_action_call_steps(
    action_call_requests: list[AgentActionCallRequest],
    action_call_confirmations: list[AgentActionCallConfirmation],
) -> list[AgentConversationRunStep]:
    confirmations_by_request_id = {
        confirmation.request_id: confirmation
        for confirmation in action_call_confirmations
    }

    steps: list[AgentConversationRunStep] = []

    for action_call_request in action_call_requests:
        confirmation = confirmations_by_request_id.get(action_call_request.id)

        if action_call_request.requires_confirmation:
            if not confirmation:
                raise ValueError(
                    f"Confirmation missing for action call request ID: {action_call_request.id}"
                )

            if not confirmation.confirmed:
                error_message = f"Error: User denied execution of this tool. Comment: {confirmation.comment}"
                action_call_step = AgentConversationRunStepTopicActionCall(
                    started_at=utc_now(),
                    details=AgentTopicActionCall(
                        request=action_call_request,
                        response=AgentActionCallResponse(content=error_message),
                    ),
                )
                steps.append(action_call_step)
                continue

        action_call_step_started_at = utc_now()

        try:
            action_call_response = await execute_agent_action(action_call_request)
        except Exception as e:
            logger.exception(
                "Confirmed action '%s' (type=%s) failed",
                action_call_request.action_system_name,
                action_call_request.action_type,
            )
            action_call_response = AgentActionCallResponse(
                content=_sanitize_action_error(e),
            )

        action_call_step = AgentConversationRunStepTopicActionCall(
            started_at=action_call_step_started_at,
            details=AgentTopicActionCall(
                request=action_call_request,
                response=action_call_response,
            ),
        )
        steps.append(action_call_step)

    return steps
