from pytest_mock import MockerFixture

from services.agents.actions.action_execute_rag import action_execute_rag
from services.rag_tools.models import RagToolTestResult


def test_execute_agent_action_rag(mocker: MockerFixture):
    mock_execute_rag_tool = mocker.patch(
        "services.agents.actions.action_execute_rag.execute_rag_tool",
        return_value=RagToolTestResult(
            answer="RAG answer",
            results=[
                {"content": "Chunk content #1", "score": 0.89},
                {"content": "Chunk content #2", "score": 0.85},
            ],
        ),
    )

    tool_system_name = "rag_tool_test"
    arguments = {"query": "test_query"}

    response = action_execute_rag(tool_system_name, arguments)

    mock_execute_rag_tool.assert_called_once_with(
        system_name_or_config="rag_tool_test", user_message="test_query"
    )

    assert response.content == "RAG answer"
    assert response.verbose_details
    assert response.verbose_details.get("answer") == "RAG answer"
    assert response.verbose_details.get("results") == [
        {"content": "Chunk content #1", "score": 0.89},
        {"content": "Chunk content #2", "score": 0.85},
    ]
