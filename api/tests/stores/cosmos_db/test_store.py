from collections.abc import Callable
from unittest.mock import MagicMock, call

import pytest
from bson import ObjectId
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult
from pytest_mock import MockerFixture

from models import ChunksByCollection
from stores.cosmos_db.store import CosmosDbStore


@pytest.fixture
def mock_cosmos_db_client_database():
    return MagicMock()


@pytest.fixture
def mock_cosmos_db_client(mock_cosmos_db_client_database):
    mock = MagicMock()
    mock.database.return_value = mock_cosmos_db_client_database

    return mock


@pytest.fixture
def cosmos_db_store(mock_cosmos_db_client, mocker: MockerFixture) -> CosmosDbStore:

    return CosmosDbStore(client=mock_cosmos_db_client)


def get_mongo_cursor_mock(mock_cursor_data):
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter(mock_cursor_data)

    return mock_cursor


def get_collection_side_effect(data: dict) -> Callable:
    def side_effect(*args):
        return_value = data.get(args[0])

        if not return_value:
            raise ValueError("Invalid input")

        return return_value

    return side_effect


def test_list_collections(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collections_data = [{"_id": "1"}, {"_id": "2"}]

    mock_collection = MagicMock()
    mock_cosmos_db_client.get_collection.return_value = mock_collection
    mock_collection.find.return_value = get_mongo_cursor_mock(collections_data)

    result = cosmos_db_store.list_collections()

    assert result == collections_data

    mock_cosmos_db_client.get_collection.assert_called_once_with("collections")


def test_create_collection(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    mock_collection_collections = MagicMock()
    mock_collection_collections.insert_one.return_value = InsertOneResult(inserted_id="1", acknowledged=True)
    mock_cosmos_db_client.get_collection.return_value = mock_collection_collections

    result = cosmos_db_store.create_collection({"name": "Collection #1"})

    assert result == "1"

    mock_collection_collections.insert_one.assert_called_once()
    mock_cosmos_db_client.database.create_collection.assert_called_once_with("documents_1")
    mock_cosmos_db_client.database.command.assert_called_once_with(
        {
            "createIndexes": "documents_1",
            "indexes": [
                {
                    "name": "VectorSearchIndex",
                    "key": {"embedding": "cosmosSearch"},
                    "cosmosSearchOptions": {"kind": "vector-ivf", "numLists": 1, "similarity": "COS", "dimensions": 1536},
                },
            ],
        },
    )


def test_get_collection_metadata(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    collection_object_id = ObjectId(collection_id)
    collection_metadata = {"_id": collection_object_id, "name": "Collection #1"}
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = collection_metadata
    mock_cosmos_db_client.get_collection.return_value = mock_collection

    result = cosmos_db_store.get_collection_metadata(collection_id)

    assert result == {"id": collection_id, "name": "Collection #1"}

    mock_collection.find_one.assert_called_once_with({"_id": collection_object_id})


def test_get_collection_metadata_not_existent(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_cosmos_db_client.get_collection.return_value = mock_collection

    with pytest.raises(LookupError, match="Collection does not exist"):
        cosmos_db_store.get_collection_metadata(collection_id)

    mock_collection.find_one.assert_called_once_with({"_id": ObjectId(collection_id)})


def test_update_collection_metadata(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    collection_object_id = ObjectId(collection_id)
    mock_collection = MagicMock()
    mock_collection.update_one.return_value = UpdateResult(raw_result={"n": 1}, acknowledged=True)
    mock_cosmos_db_client.get_collection.return_value = mock_collection

    result = cosmos_db_store.update_collection_metadata(collection_id, {"name": "Updated name"})

    assert result is None

    mock_collection.update_one.assert_called_once_with({"_id": collection_object_id}, {"$set": {"name": "Updated name"}})


def test_update_collection_metadata_not_existent(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    collection_object_id = ObjectId(collection_id)
    mock_collection = MagicMock()
    mock_collection.update_one.return_value = UpdateResult(raw_result={"n": 0}, acknowledged=True)
    mock_cosmos_db_client.get_collection.return_value = mock_collection

    with pytest.raises(LookupError, match="Nothing was updated"):
        cosmos_db_store.update_collection_metadata(collection_id, {"name": "Updated name"})

    mock_collection.update_one.assert_called_once_with({"_id": collection_object_id}, {"$set": {"name": "Updated name"}})


def test_delete_collection(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    collection_object_id = ObjectId(collection_id)
    mock_collection_collections = MagicMock()
    mock_collection_documents = MagicMock()

    mock_collection_collections.delete_one.return_value = DeleteResult(raw_result={"n": 1}, acknowledged=True)
    mock_cosmos_db_client.get_collection.side_effect = get_collection_side_effect(
        {
            "collections": mock_collection_collections,
            "documents_65d754785baec301dcce36db": mock_collection_documents,
        },
    )

    result = cosmos_db_store.delete_collection(collection_id)

    assert result is None

    mock_collection_collections.delete_one.assert_called_once_with({"_id": collection_object_id})
    mock_collection_documents.drop.assert_called_once()


def test_document_collection_similarity_search_collection_non_existent(cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
    collection_id = "65d754785baec301dcce36db"
    query = "Hi"
    num_results = 3
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    mock_cosmos_db_client.get_collection.return_value = mock_collection

    with pytest.raises(LookupError, match="Collection does not exist"):
        cosmos_db_store.document_collection_similarity_search(
            collection_id=collection_id,
            query=query,
            num_results=num_results,
        )

    mock_collection.aggregate.assert_not_called()


# Takes long because @observe could be mocked. Implementations need refactoring.
# def test_document_collection_similarity_search(mocker: MockerFixture, cosmos_db_store: CosmosDbStore, mock_cosmos_db_client):
#     collection_id = "65d754785baec301dcce36db"
#     collection_object_id = ObjectId(collection_id)
#     query = "Hi"
#     num_results = 3

#     collection_metadata = {"_id": collection_object_id, "name": "Collection #1", "todo_MODELs": "1"}
#     mock_collection_collections = MagicMock()
#     mock_collection_collections.find_one.return_value = collection_metadata

#     mock_collection_documents = MagicMock()
#     mock_collection_documents.aggregate.return_value = get_mongo_cursor_mock(
#         [
#             {"_id": ObjectId("65d6139128defdcf0816c101"), "content": "Content 1", "metadata": {"name": "Name 1"}, "similarityScore": "0.83"},
#             {"_id": ObjectId("65d6139128defdcf0816c102"), "content": "Content 2", "metadata": {"name": "Name 2"}, "similarityScore": "0.82"},
#             {"_id": ObjectId("65d6139128defdcf0816c103"), "content": "Content 3", "metadata": {"name": "Name 3"}, "similarityScore": "0.81"},
#         ]
#     )

#     mock_cosmos_db_client.get_collection.side_effect = get_collection_side_effect(
#         {
#             "collections": mock_collection_collections,
#             "documents_65d754785baec301dcce36db": mock_collection_documents,
#         }
#     )
#     mocker.patch("stores.cosmos_db.store.observability_context")

#     mocker.patch(
#         "stores.cosmos_db.store.get_embeddings",
#         return_value=[1.0, 2.0, 3.0],
#     )

#     result = cosmos_db_store.document_collection_similarity_search(
#         collection_id=collection_id,
#         query=query,
#         num_results=num_results,
#     )

#     mock_collection_documents.aggregate.assert_called_once_with(
#         [
#             {
#                 "$search": {
#                     "cosmosSearch": {
#                         "vector": [1.0, 2.0, 3.0],
#                         "path": "embedding",
#                         "k": num_results,
#                     },
#                     "returnStoredSource": True,
#                 }
#             },
#             {
#                 "$project": {
#                     "similarityScore": {"$toString": {"$meta": "searchScore"}},
#                     "content": "$$ROOT.content",
#                     "metadata": "$$ROOT.metadata",
#                 }
#             },
#         ]
#     )

#     assert len(result) == 3

#     assert result[0] == DocumentSearchResultItem(content="Content 1", metadata={"name": "Name 1"}, score=Decimal("0.83"), collection_id=collection_id)
#     assert result[1] == DocumentSearchResultItem(content="Content 2", metadata={"name": "Name 2"}, score=Decimal("0.82"), collection_id=collection_id)
#     assert result[2] == DocumentSearchResultItem(content="Content 3", metadata={"name": "Name 3"}, score=Decimal("0.81"), collection_id=collection_id)


def test_document_collections_query_chunks_context(mocker: MockerFixture, cosmos_db_store: CosmosDbStore):
    collection_id_1 = "65d754785baec301dcce36db"
    collection_id_2 = "65d754785baec301dcce36dc"
    chunks_by_collection_id_by_source_id = {
        collection_id_1: {
            "doc_1": [1, 2, 3, 4, 5, 6],
            "doc_2": [9, 10, 11],
        },
        collection_id_2: {
            "doc_3": [4, 5, 6],
        },
    }

    mocker.patch.object(
        cosmos_db_store,
        "list_documents",
        side_effect=[
            [
                {"id": "1_1"},
                {"id": "1_2"},
                {"id": "1_3"},
                {"id": "1_4"},
                {"id": "1_5"},
                {"id": "1_6"},
                {"id": "2_9"},
                {"id": "2_10"},
                {"id": "2_11"},
            ],
            [
                {"id": "3_4"},
                {"id": "3_5"},
                {"id": "3_6"},
            ],
        ],
    )

    result = cosmos_db_store.document_collections_query_chunks_context(chunks_by_collection_id_by_source_id)

    list_documents_expected_calls = [
        call(
            collection_id=collection_id_1,
            query={
                "$or": [
                    {"metadata.sourceId": "doc_1", "metadata.chunkNumber": {"$in": [1, 2, 3, 4, 5, 6]}},
                    {"metadata.sourceId": "doc_2", "metadata.chunkNumber": {"$in": [9, 10, 11]}},
                ],
            },
        ),
        call(
            collection_id=collection_id_2,
            query={
                "$or": [
                    {"metadata.sourceId": "doc_3", "metadata.chunkNumber": {"$in": [4, 5, 6]}},
                ],
            },
        ),
    ]

    assert cosmos_db_store.list_documents.call_count == len(list_documents_expected_calls)
    cosmos_db_store.list_documents.assert_has_calls(list_documents_expected_calls)

    expected_result: ChunksByCollection = {
        collection_id_1: [
            {"id": "1_1"},
            {"id": "1_2"},
            {"id": "1_3"},
            {"id": "1_4"},
            {"id": "1_5"},
            {"id": "1_6"},
            {"id": "2_9"},
            {"id": "2_10"},
            {"id": "2_11"},
        ],
        collection_id_2: [
            {"id": "3_4"},
            {"id": "3_5"},
            {"id": "3_6"},
        ],
    }

    assert result == expected_result
