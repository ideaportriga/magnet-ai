from decimal import Decimal

from pytest_mock import MockerFixture

from models import DocumentSearchResultItem
from services.agents.actions.action_execute_retrieval import action_execute_retrieval
from services.flow_retrieval_test import RetrievalToolTestResult
from validation.retrieval_tools import RetrievalToolExecute


def test_execute_agent_action_rag(mocker: MockerFixture):
    results = [
        DocumentSearchResultItem(
            id="1",
            collection_id="",
            metadata={"title": "Chunk title #1", "source": "Chunk source #1"},
            content="Chunk content #1",
            score=Decimal(0.89),
        ),
        DocumentSearchResultItem(
            id="2",
            collection_id="",
            metadata={"title": "Chunk title #2", "source": "Chunk source #2"},
            content="Chunk content #2",
            score=Decimal(0.85),
        ),
    ]
    mock_execute_retrieval_tool = mocker.patch(
        "services.agents.actions.action_execute_retrieval.flow_retrieval_execute",
        return_value=RetrievalToolTestResult(
            results=results,
        ),
    )

    tool_system_name = "retrieval_tool_test"
    query = "test_query"
    arguments = {"query": query}

    response = action_execute_retrieval(tool_system_name, arguments)

    mock_execute_retrieval_tool.assert_called_once_with(
        RetrievalToolExecute(system_name=tool_system_name, user_message=query),
    )

    print("response: ", response)

    assert response.content.splitlines() == [
        "Title: Chunk title #1",
        "URL: Chunk source #1",
        "Chunk content #1",
        "",
        "Title: Chunk title #2",
        "URL: Chunk source #2",
        "Chunk content #2",
    ]

    assert response.verbose_details
    assert len(response.verbose_details.get("results")) == 2
