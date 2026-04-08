from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from services.agents.actions.action_execute_prompt_template import (
    action_execute_prompt_template,
)
from services.prompt_templates.models import PromptTemplateExecutionResponse


async def test_execute_agent_action_prompt_template(mocker: MockerFixture):
    mock_execute_prompt_template = mocker.patch(
        "services.agents.actions.action_execute_prompt_template.execute_prompt_template",
        new_callable=AsyncMock,
        return_value=PromptTemplateExecutionResponse(
            content="Prompt template response content",
        ),
    )

    tool_system_name = "prompt_template_test"
    user_message = "Test user message"
    arguments = {"userMessage": user_message}

    response = await action_execute_prompt_template(tool_system_name, arguments)

    mock_execute_prompt_template.assert_called_once_with(
        system_name_or_config=tool_system_name,
        template_additional_messages=[
            {
                "role": "user",
                "content": user_message,
            },
        ],
    )

    assert response.content == "Prompt template response content"
    assert not response.verbose_details
