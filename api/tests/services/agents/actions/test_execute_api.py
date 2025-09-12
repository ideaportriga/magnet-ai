import pytest
from pytest_mock import MockerFixture

from services.agents.actions.action_execute_api import action_execute_api
from services.api_tools.types import (
    ApiToolExecute,
    ApiToolExecuteInputParams,
    ApiToolExecuteResult,
)


@pytest.mark.parametrize(
    "arguments, expected_input_params",
    [
        (
            {},
            ApiToolExecuteInputParams(),
        ),
        (
            {"requestBody": {"Field1": "FieldValue1", "Field2": "FieldValue2"}},
            ApiToolExecuteInputParams(
                requestBody={"Field1": "FieldValue1", "Field2": "FieldValue2"},
            ),
        ),
        (
            {"pathParams": {"id": "123"}, "queryParams": {"search": "test"}},
            ApiToolExecuteInputParams(
                pathParams={"id": "123"},
                queryParams={"search": "test"},
            ),
        ),
        (
            {"pathParams": {"id": "123"}, "requestBody": {"Field1": "FieldValue1"}},
            ApiToolExecuteInputParams(
                pathParams={"id": "123"},
                requestBody={"Field1": "FieldValue1"},
            ),
        ),
    ],
)
def test_execute_agent_action_api(
    mocker: MockerFixture,
    arguments: dict,
    expected_input_params: ApiToolExecuteInputParams,
):
    mock_api_tool_execute = mocker.patch(
        "services.agents.actions.action_execute_api.api_tool_execute",
        return_value=ApiToolExecuteResult(
            status_code=200,
            headers={
                "Content-Type": "application/json",
            },
            content="Response content",
        ),
    )

    tool_system_name = "api_tool_test"

    response = action_execute_api(tool_system_name, arguments)

    mock_api_tool_execute.assert_called_once_with(
        ApiToolExecute(
            system_name=tool_system_name,
            input_params=expected_input_params,
        ),
    )

    assert response.content == "Response content"
    assert response.verbose_details
    assert response.verbose_details.get("content") == "Response content"
    assert response.verbose_details.get("status_code") == 200
    assert response.verbose_details.get("headers") == {
        "Content-Type": "application/json",
    }


# Currently extra parameters are allowed in order to have action message
# TODO - think about different tool input validation
# @pytest.mark.parametrize(
#     "invalid_arguments",
#     [
#         ({"request": {"Field1": "FieldValue1", "Field2": "FieldValue2"}}),
#         ({"pathParams": {"id": "123"}, "body": {"Field1": "FieldValue1"}}),
#     ],
# )
# def test_execute_agent_action_api_invalid_arguments(mocker: MockerFixture, invalid_arguments: dict):
#     mock_api_tool_execute = mocker.patch("services.agents.actions.action_execute_api.api_tool_execute")

#     tool_system_name = "api_tool_test"

#     with pytest.raises(Exception):
#         action_execute_api(tool_system_name, invalid_arguments)

#     mock_api_tool_execute.assert_not_called()
