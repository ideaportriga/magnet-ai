from http import HTTPMethod
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from services.api_tools.flow_test import api_tool_test
from services.api_tools.types import (
    ApiToolBase,
    ApiToolExecuteInputParams,
    ApiToolExecuteResult,
    ApiToolTest,
)


@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "GET request with query params",
            "config": ApiToolBase(api_provider="PROVIDER_1", path="/api/test", method=HTTPMethod.GET),
            "input_params": ApiToolExecuteInputParams(queryParams={"filter": "active", "page": "1"}),
            "mock_api_response": Mock(status_code=200, text='{"success": true}', ok=True, headers={"Content-Type": "application/json"}),
            "api_url": "https://api.example.com",
            "api_method": "GET",
            "expected_url": "https://api.example.com/api/test",
        },
        {
            "name": "POST with path params and body",
            "config": ApiToolBase(api_provider="PROVIDER_1", path="/api/users/{userId}/posts", method=HTTPMethod.POST),
            "input_params": ApiToolExecuteInputParams(
                queryParams={"draft": "true"}, pathParams={"userId": "123"}, requestBody={"title": "Test Post"},
            ),
            "mock_api_response": Mock(status_code=201, text='{"id": 1}', ok=True, headers={"Content-Type": "application/json"}),
            "api_url": "https://api.example.com",
            "api_method": "POST",
            "expected_url": "https://api.example.com/api/users/123/posts",
        },
        {
            "name": "Error response",
            "config": ApiToolBase(api_provider="PROVIDER_1", path="/api/invalid", method=HTTPMethod.GET),
            "input_params": ApiToolExecuteInputParams(),
            "mock_api_response": Mock(status_code=404, text='{"error": "Not Found"}', ok=False, headers={"Content-Type": "application/json"}),
            "api_url": "https://api.example.com",
            "api_method": "GET",
            "expected_url": "https://api.example.com/api/invalid",
        },
    ],
)
def test_api_tool_test(mocker: MockerFixture, test_case):
    mocker.patch(
        "services.api_tools.flow_test.API_TOOL_PROVIDER_CONFIG_MAPPING",
        {
            "PROVIDER_1": {
                "server_url": test_case["api_url"],
                "security_schema": {"scheme": "basic", "type": "http"},
                "auth_params": {"username": "USERNAME", "password": "PASSWORD"},
            },
        },
    )

    mock_api_client = Mock()
    mock_api_client.request.return_value = test_case["mock_api_response"]
    mock_api_client.return_value = mock_api_client
    mocker.patch("services.api_tools.flow_test.create_api_client", mock_api_client)

    test_params = ApiToolTest(api_tool_config=test_case["config"], input_params=test_case["input_params"])

    result = api_tool_test(test_params)

    assert isinstance(result, ApiToolExecuteResult)
    assert result.status_code == test_case["mock_api_response"].status_code
    assert result.content == test_case["mock_api_response"].text
    assert result.headers == test_case["mock_api_response"].headers

    mock_api_client.request.assert_called_once_with(
        test_case["api_method"],
        test_case["expected_url"],
        params=test_case["input_params"].queryParams,
        json=test_case["input_params"].requestBody,
    )
