from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from services.transfer import import_entities
from stores.cosmos_db.store import CosmosDbStore


@pytest.fixture
def mock_db_client(mocker):
    mocked_datetime = mocker.patch("services.transfer.client")

    return mocked_datetime


@pytest.fixture
def mock_embedding_function():
    return MagicMock()


@pytest.fixture
def cosmos_db_store(mock_db_client, mock_embedding_function):
    return CosmosDbStore(
        client=mock_db_client, embedding_function=mock_embedding_function
    )


# TODO - make reusable?
def get_mongo_cursor_mock(mock_cursor_data):
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(mock_cursor_data)

    return mock_cursor


# TODO - make reusable?
def get_collection_side_effect(data: dict) -> Callable:
    def side_effect(*args):
        return_value = data.get(args[0])

        if not return_value:
            raise ValueError("Invalid input")

        return return_value

    return side_effect


# TODO - refactor
def test_import_entities(mock_db_client):
    ai_apps_to_transfer = [
        {"name": "AI_APP_1", "code": "AI_APP_1"},
        {"name": "AI_APP_2", "code": "AI_APP_2"},
    ]

    rag_tools_to_transfer = [
        {"name": "RAG_TOOL_1", "code": "RAG_TOOL_1"},
        {"name": "RAG_TOOL_2", "code": "RAG_TOOL_2"},
    ]

    retrieval_tools_to_transfer = [
        {"name": "RETRIEVAL_TOOL_1", "system_name": "RETRIEVAL_TOOL_1"},
        {"name": "RETRIEVAL_TOOL_2", "system_name": "RETRIEVAL_TOOL_2"},
    ]

    prompt_templates_to_transfer = [
        {"name": "PROMPT_TEMPLATE_1", "code": "PROMPT_TEMPLATE_1"},
        {"name": "PROMPT_TEMPLATE_2", "code": "PROMPT_TEMPLATE_2"},
    ]

    models_to_transfer = [
        {"name": "PROMPT_TEMPLATE_1", "code": "PROMPT_TEMPLATE_1"},
        {"name": "PROMPT_TEMPLATE_2", "code": "PROMPT_TEMPLATE_2"},
    ]

    import_data = {
        "ai_apps": ai_apps_to_transfer,
        "rag_tools": rag_tools_to_transfer,
        "retrieval_tools": retrieval_tools_to_transfer,
        "prompt_templates": prompt_templates_to_transfer,
        "models": models_to_transfer,
        # TODO - knowledge sources
    }

    mock_collection_ai_apps = MagicMock()
    mock_collection_rag_tools = MagicMock()
    mock_collection_retrieval_tools = MagicMock()
    mock_collection_prompt_templates = MagicMock()
    mock_collection_models = MagicMock()

    mock_db_client.get_collection.side_effect = get_collection_side_effect(
        {
            "ai_apps": mock_collection_ai_apps,
            "rag_tools": mock_collection_rag_tools,
            "retrieval_tools": mock_collection_retrieval_tools,
            "prompts": mock_collection_prompt_templates,  # TODO - rename collection
            "models": mock_collection_models,
        },
    )

    import_entities(import_data)

    mock_collection_ai_apps.insert_many.assert_called_once_with(ai_apps_to_transfer)
    mock_collection_rag_tools.insert_many.assert_called_once_with(rag_tools_to_transfer)
    mock_collection_retrieval_tools.insert_many.assert_called_once_with(
        retrieval_tools_to_transfer
    )
    mock_collection_prompt_templates.insert_many.assert_called_once_with(
        prompt_templates_to_transfer
    )
    mock_collection_models.insert_many.assert_called_once_with(models_to_transfer)
