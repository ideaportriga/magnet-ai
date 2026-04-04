from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from services.transfer import export_entities


@pytest.fixture
def mock_db_client(mocker):
    mock = mocker.patch("services.transfer.client")

    return mock


@pytest.fixture
def mock_db_store(mocker):
    mock = mocker.patch("services.transfer.store")

    return mock


# TODO - make reusable?
def get_mongo_cursor_mock(mock_cursor_data):
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(mock_cursor_data)

    return mock_cursor


# TODO - make reusable?
def create_side_effect(data: list[dict]) -> Callable:
    def side_effect(*args, **kwargs):
        for data_item in data:
            if args == data_item.get("args", ()) and kwargs == data_item.get(
                "kwargs", {}
            ):
                return data_item.get("return_value")

        raise ValueError("Invalid input")

    return side_effect


# TODO - refactor
def test_export_entities(mock_db_client, mock_db_store):
    ai_apps_mocked = [
        {"name": "AI_APP_1", "code": "AI_APP_1"},
        {"name": "AI_APP_2", "code": "AI_APP_2"},
    ]

    rag_tools_mocked = [
        {"name": "RAG_TOOL_1", "code": "RAG_TOOL_1"},
        {"name": "RAG_TOOL_2", "code": "RAG_TOOL_2"},
    ]

    retrieval_tools_mocked = [
        {"name": "RETRIEVAL_TOOL_1", "system_name": "RETRIEVAL_TOOL_1"},
        {"name": "RETRIEVAL_TOOL_2", "system_name": "RETRIEVAL_TOOL_2"},
    ]

    prompt_templates_mocked = [
        {"name": "PROMPT_TEMPLATE_1", "code": "PROMPT_TEMPLATE_1"},
        {"name": "PROMPT_TEMPLATE_2", "code": "PROMPT_TEMPLATE_2"},
    ]

    models_mocked = [
        {"name": "MODEL_1", "code": "MODEL_1"},
        {"name": "MODEL_2", "code": "MODEL_2"},
    ]

    collections_mocked = [
        {
            "name": "KNOWLEDGE_SOURCE_1",
            "code": "KNOWLEDGE_SOURCE_1",
            "id": "65d754785baec301dcce36db",
        },
    ]

    collection_1_documents_mocked: list[dict] = [
        {
            "content": "Content 1",
            "metadata": {"name": "Name 1"},
            "id": "65d6139128defdcf0816c101",
        },
        {
            "content": "Content 2",
            "metadata": {"name": "Name 2"},
            "id": "65d6139128defdcf0816c102",
        },
        {
            "content": "Content 3",
            "metadata": {"name": "Name 3"},
            "id": "65d6139128defdcf0816c103",
        },
    ]

    collections_exported = [
        {
            "name": "KNOWLEDGE_SOURCE_1",
            "code": "KNOWLEDGE_SOURCE_1",
            "chunks": [
                {"content": "Content 1", "metadata": {"name": "Name 1"}},
                {"content": "Content 2", "metadata": {"name": "Name 2"}},
                {"content": "Content 3", "metadata": {"name": "Name 3"}},
            ],
        },
    ]

    mock_collection_ai_apps = MagicMock()
    mock_collection_ai_apps.find.return_value = get_mongo_cursor_mock(ai_apps_mocked)

    mock_collection_rag_tools = MagicMock()
    mock_collection_rag_tools.find.return_value = get_mongo_cursor_mock(
        rag_tools_mocked
    )

    mock_collection_retrieval_tools = MagicMock()
    mock_collection_retrieval_tools.find.return_value = get_mongo_cursor_mock(
        retrieval_tools_mocked
    )

    mock_collection_prompt_templates = MagicMock()
    mock_collection_prompt_templates.find.return_value = get_mongo_cursor_mock(
        prompt_templates_mocked
    )

    mock_collection_models = MagicMock()
    mock_collection_models.find.return_value = get_mongo_cursor_mock(models_mocked)

    mock_db_client.get_collection.side_effect = create_side_effect(
        [
            {"args": ("ai_apps",), "return_value": mock_collection_ai_apps},
            {"args": ("rag_tools",), "return_value": mock_collection_rag_tools},
            {
                "args": ("retrieval_tools",),
                "return_value": mock_collection_retrieval_tools,
            },
            {
                "args": ("prompts",),
                "return_value": mock_collection_prompt_templates,
            },  # TODO - rename collection
            {
                "args": ("models",),
                "return_value": mock_collection_models,
            },  # TODO - rename collection
        ],
    )

    mock_db_store.list_collections.return_value = collections_mocked

    mock_db_store.list_documents.side_effect = create_side_effect(
        [
            {
                "kwargs": {"collection_id": "65d754785baec301dcce36db"},
                "return_value": collection_1_documents_mocked,
            },
        ],
    )

    data = {
        "ai_apps": ["AI_APP_1", "AI_APP_2", "AI_APP_3"],
        "rag_tools": ["RAG_TOOL_1", "RAG_TOOL_2"],
        "retrieval_tools": ["RETRIEVAL_TOOL_1", "RETRIEVAL_TOOL_2"],
        "prompt_templates": ["RETRIEVAL_TOOL_1", "RETRIEVAL_TOOL_2"],
        "knowledge_sources": ["KNOWLEDGE_SOURCE_1"],
        "models": ["MODEL_1", "MODEL_2"],
    }

    result = export_entities(data)

    expected_result = {
        "ai_apps": ai_apps_mocked,
        "rag_tools": rag_tools_mocked,
        "retrieval_tools": retrieval_tools_mocked,
        "prompt_templates": prompt_templates_mocked,
        "knowledge_sources": collections_exported,
        "models": models_mocked,
    }

    assert result == expected_result
