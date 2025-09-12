from decimal import Decimal

import pytest
from langchain.schema import Document

from models import ChunksByCollection, DocumentSearchResultItem
from stores.document_store import DocumentStore
from tools.rag.utils import (
    get_chat_completion_input_documents,
    get_extended_chunks_query,
)


@pytest.fixture
def mock_document_store(mocker):
    mocked_store = mocker.patch("tools.rag.utils.store", spec_set=DocumentStore)
    return mocked_store


def test_get_extended_chunks_query():
    collection_id_1 = "65d754785baec301dcce36da"
    collection_id_2 = "65d754785baec301dcce36db"
    collection_id_3_non_chunked = "65d754785baec301dcce36dc"

    context_window = 2

    search_result = [
        DocumentSearchResultItem(
            id="1_1",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 1},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="1_2",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 10},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="1_3",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 13},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="1_4",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_2", "chunkNumber": 5},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_1",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_1", "chunkNumber": 3},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_2",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 5},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_3",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 10},
            content="",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="3_1",
            collection_id=collection_id_3_non_chunked,
            metadata={"sourceId": "3_1"},
            content="",
            score=Decimal("0"),
        ),
    ]

    result = get_extended_chunks_query(
        search_result=search_result, context_window=context_window,
    )

    assert result == {
        collection_id_1: {
            "1_1": [1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15],
            "1_2": [3, 4, 5, 6, 7],
        },
        collection_id_2: {
            "2_1": [1, 2, 3, 4, 5],
            "2_2": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        },
    }


@pytest.mark.parametrize(
    "context_window",
    [
        (0),
        (-1),
    ],
)
def test_get_chat_completion_input_documents_no_context_window(
    mock_document_store, context_window,
):
    """It should not call store for extended context if there is no context window (it's less than 1).
    It should just convert retrieved chunks to input documents.
    """
    collection_id_1 = "collection_1"
    collection_id_2 = "collection_2"
    collection_id_3_non_chunked = "65d754785baec301dcce36dc"

    search_result = [
        DocumentSearchResultItem(
            id="1_1",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 1},
            content="Doc 1_1, Chunk 1.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="3_1",
            collection_id=collection_id_3_non_chunked,
            metadata={"sourceId": "3"},
            content="Doc 3.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_1",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 7},
            content="Doc 2_2, Chunk 7.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_2",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 5},
            content="Doc 2_2, Chunk 5.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="1_2",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 12},
            content="Doc 1_1, Chunk 12.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_3",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_1", "chunkNumber": 3},
            content="Doc 2_1, Chunk 3.",
            score=Decimal("0"),
        ),
    ]

    result = get_chat_completion_input_documents(
        search_result=search_result, context_window=context_window,
    )

    mock_document_store.document_collections_query_chunks_context.assert_not_called()

    assert result == [
        Document(
            page_content="Doc 1_1, Chunk 1.",
            metadata={"sourceId": "1_1", "chunkNumber": 1},
        ),
        Document(page_content="Doc 3.", metadata={"sourceId": "3"}),
        Document(
            page_content="Doc 2_2, Chunk 7.",
            metadata={"sourceId": "2_2", "chunkNumber": 7},
        ),
        Document(
            page_content="Doc 2_2, Chunk 5.",
            metadata={"sourceId": "2_2", "chunkNumber": 5},
        ),
        Document(
            page_content="Doc 1_1, Chunk 12.",
            metadata={"sourceId": "1_1", "chunkNumber": 12},
        ),
        Document(
            page_content="Doc 2_1, Chunk 3.",
            metadata={"sourceId": "2_1", "chunkNumber": 3},
        ),
    ]


def test_get_chat_completion_input_documents(mocker, mock_document_store):
    collection_id_1 = "collection_1"
    collection_id_2 = "collection_2"
    collection_id_3_non_chunked = "65d754785baec301dcce36dc"
    context_window = 2

    search_result = [
        DocumentSearchResultItem(
            id="1_1",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 1},
            content="Doc 1_1, Chunk 1.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="3_1",
            collection_id=collection_id_3_non_chunked,
            metadata={"sourceId": "3"},
            content="Doc 3.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_1",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 7},
            content="Doc 2_2, Chunk 7.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_2",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_2", "chunkNumber": 5},
            content="Doc 2_2, Chunk 5.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="1_2",
            collection_id=collection_id_1,
            metadata={"sourceId": "1_1", "chunkNumber": 12},
            content="Doc 1_1, Chunk 12.",
            score=Decimal("0"),
        ),
        DocumentSearchResultItem(
            id="2_3",
            collection_id=collection_id_2,
            metadata={"sourceId": "2_1", "chunkNumber": 3},
            content="Doc 2_1, Chunk 3.",
            score=Decimal("0"),
        ),
    ]

    extended_chunks_query = {
        collection_id_1: {"1_1": [1, 2, 3, 10, 11, 12, 13, 14]},
        collection_id_2: {"2_1": [1, 2, 3, 4, 5], "2_2": [3, 4, 5, 6, 7, 8, 9]},
    }

    mocker.patch(
        "tools.rag.utils.get_extended_chunks_query", return_value=extended_chunks_query,
    )

    mocked_chunks_by_collections: ChunksByCollection = {
        collection_id_1: [
            {
                "content": "Doc 1_1, Chunk 1.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 1, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 2.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 2, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 3.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 3, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 10.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 10, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 11.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 11, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 12.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 12, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 13.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 13, "chunksTotal": 15},
            },
            {
                "content": "Doc 1_1, Chunk 14.",
                "metadata": {"sourceId": "1_1", "chunkNumber": 14, "chunksTotal": 15},
            },
        ],
        collection_id_2: [
            {
                "content": "Doc 2_1, Chunk 1.",
                "metadata": {"sourceId": "2_1", "chunkNumber": 1, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_1, Chunk 2.",
                "metadata": {"sourceId": "2_1", "chunkNumber": 2, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_1, Chunk 3.",
                "metadata": {"sourceId": "2_1", "chunkNumber": 3, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_1, Chunk 4.",
                "metadata": {"sourceId": "2_1", "chunkNumber": 4, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_1, Chunk 5.",
                "metadata": {"sourceId": "2_1", "chunkNumber": 5, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 3.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 3, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 4.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 4, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 5.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 5, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 6.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 6, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 7.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 7, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 8.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 8, "chunksTotal": 10},
            },
            {
                "content": "Doc 2_2, Chunk 9.",
                "metadata": {"sourceId": "2_2", "chunkNumber": 9, "chunksTotal": 10},
            },
        ],
    }

    mock_document_store.document_collections_query_chunks_context.return_value = (
        mocked_chunks_by_collections
    )

    result = get_chat_completion_input_documents(
        search_result=search_result, context_window=context_window,
    )

    mock_document_store.document_collections_query_chunks_context.assert_called_once_with(
        query=extended_chunks_query,
    )

    assert result == [
        Document(
            page_content="Doc 1_1, Chunk 1.",
            metadata={"sourceId": "1_1", "chunkNumber": 1, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 2.",
            metadata={"sourceId": "1_1", "chunkNumber": 2, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 3.",
            metadata={"sourceId": "1_1", "chunkNumber": 3, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 10.",
            metadata={"sourceId": "1_1", "chunkNumber": 10, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 11.",
            metadata={"sourceId": "1_1", "chunkNumber": 11, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 12.",
            metadata={"sourceId": "1_1", "chunkNumber": 12, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 13.",
            metadata={"sourceId": "1_1", "chunkNumber": 13, "chunksTotal": 15},
        ),
        Document(
            page_content="Doc 1_1, Chunk 14.",
            metadata={"sourceId": "1_1", "chunkNumber": 14, "chunksTotal": 15},
        ),
        Document(page_content="Doc 3.", metadata={"sourceId": "3"}),
        Document(
            page_content="Doc 2_2, Chunk 3.",
            metadata={"sourceId": "2_2", "chunkNumber": 3, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 4.",
            metadata={"sourceId": "2_2", "chunkNumber": 4, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 5.",
            metadata={"sourceId": "2_2", "chunkNumber": 5, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 6.",
            metadata={"sourceId": "2_2", "chunkNumber": 6, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 7.",
            metadata={"sourceId": "2_2", "chunkNumber": 7, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 8.",
            metadata={"sourceId": "2_2", "chunkNumber": 8, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_2, Chunk 9.",
            metadata={"sourceId": "2_2", "chunkNumber": 9, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_1, Chunk 1.",
            metadata={"sourceId": "2_1", "chunkNumber": 1, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_1, Chunk 2.",
            metadata={"sourceId": "2_1", "chunkNumber": 2, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_1, Chunk 3.",
            metadata={"sourceId": "2_1", "chunkNumber": 3, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_1, Chunk 4.",
            metadata={"sourceId": "2_1", "chunkNumber": 4, "chunksTotal": 10},
        ),
        Document(
            page_content="Doc 2_1, Chunk 5.",
            metadata={"sourceId": "2_1", "chunkNumber": 5, "chunksTotal": 10},
        ),
    ]

    # TODO - rethink chunk group order based on search result order.
    # assert result == [
    #     Document(page_content="Doc 1_1, Chunk 1. Doc 1_1, Chunk 2. Doc 1_1, Chunk 3."),
    #     Document(page_content="Doc 3."),
    #     Document(
    #         page_content="Doc 2_2, Chunk 3. Doc 2_2, Chunk 4. Doc 2_2, Chunk 5. Doc 2_2, Chunk 6. Doc 2_2, Chunk 7. Doc 2_2, Chunk 8. Doc 2_2, Chunk 9."
    #     ),
    #     Document(page_content="Doc 1_1, Chunk 10. Doc 1_1, Chunk 11. Doc 1_1, Chunk 12. Doc 1_1, Chunk 13. Doc 1_1, Chunk 14."),
    #     Document(page_content="Doc 2_1, Chunk 1. Doc 2_1, Chunk 2. Doc 2_1, Chunk 3. Doc 2_1, Chunk 4. Doc 2_1, Chunk 5."),
    # ]
