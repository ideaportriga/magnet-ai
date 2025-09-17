import asyncio
import uuid
from decimal import Decimal
from logging import getLogger
from typing import Any, override

from bson import ObjectId

# Use Motor for async MongoDB
from motor.motor_asyncio import AsyncIOMotorCollection

from models import (
    ChunksByCollection,
    DocumentData,
    DocumentSearchResult,
    DocumentSearchResultItem,
    QueryChunksByCollectionBySource,
)

# Assume get_embeddings is now async
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType
from stores.document_store import DocumentStore
from stores.mongo_db.client import MongoDBClient
from stores.qdrant_db.store import QdrantVectorStore
from stores.vector_store import AddVector, UpsertVector
from type_defs.pagination import FilterObject, OffsetPaginationRequest
from utils.pagination_utils import paginate_collection
from validation.rag_tools import RetrieveConfig

logger = getLogger(__name__)


class MongoDbStore(DocumentStore):
    # region Initialization
    COLLECTION_NAME_COLLECTIONS = "collections"
    DOCUMENT_COLLECTION_PREFIX = "documents_"

    def __init__(self, client: MongoDBClient, vector_store: QdrantVectorStore):
        logger.info("Initializing MongoDbStore")
        self.client = client
        self.vector_store = vector_store

    # endregion

    # region Collection Management
    async def list_collections(self, query: dict | None = None) -> list[dict]:
        query = query or {}
        collection = self.client.get_collection(self.COLLECTION_NAME_COLLECTIONS)
        cursor = collection.find(query)
        result = []
        async for collection_metadata in cursor:
            collection_metadata["id"] = str(collection_metadata.pop("_id", ""))
            result.append(collection_metadata)
        return result

    async def create_collection(self, metadata: dict) -> str:
        logger.info("Creating collection")
        collection = self.client.get_collection(self.COLLECTION_NAME_COLLECTIONS)
        result = await collection.insert_one(metadata)
        collection_id = result.inserted_id
        documents_collection_name = self.__get_documents_collection_name(collection_id)
        await self.client.database.create_collection(documents_collection_name)
        await self.__create_vector_search_index(documents_collection_name)
        return str(collection_id)

    async def get_collection_metadata(self, collection_id: str) -> dict:
        logger.info("Calling get_collection_metadata")
        collection = self.client.get_collection(self.COLLECTION_NAME_COLLECTIONS)
        metadata = await collection.find_one({"_id": ObjectId(collection_id)})
        if not metadata:
            raise LookupError("Collection does not exist")
        metadata["id"] = str(metadata.pop("_id", ""))
        return metadata

    async def update_collection_metadata(self, collection_id: str, metadata: dict):
        logger.info("Calling update_collection_metadata")
        collection = self.client.get_collection(self.COLLECTION_NAME_COLLECTIONS)
        result = await collection.update_one(
            {"_id": ObjectId(collection_id)},
            {"$set": metadata},
        )
        if result.matched_count == 0:
            raise LookupError("Nothing was updated")
        logger.info("Updated metadata for collection '%s'", collection_id)

    async def replace_collection_metadata(self, collection_id: str, metadata: dict):
        logger.info("Calling replace_collection_metadata")
        collection = self.client.get_collection(self.COLLECTION_NAME_COLLECTIONS)
        result = await collection.replace_one(
            {"_id": ObjectId(collection_id)},
            metadata,
        )
        if result.matched_count == 0:
            raise LookupError("Nothing was replaced")
        logger.info("Replaced metadata for collection '%s'", collection_id)

    async def delete_collection(self, collection_id: str):
        logger.info("Calling delete_collection")
        collection_object_id = ObjectId(collection_id)
        collection_collections = self.client.get_collection(
            self.COLLECTION_NAME_COLLECTIONS,
        )
        collection_delete_result = await collection_collections.delete_one(
            {"_id": collection_object_id},
        )
        if collection_delete_result.deleted_count == 0:
            raise LookupError("Nothing was deleted")
        logger.info("Collection '%s' metadata deleted", collection_id)
        collection_documents = await self.__get_documents_collection(collection_id)
        await collection_documents.drop()
        await self.vector_store.delete_collection(
            collection_name=self.__get_documents_collection_name(collection_id),
        )
        logger.info("Collection '%s' deleted with all documents", collection_id)

    # endregion

    # region Document Management
    async def list_documents(
        self,
        collection_id: str,
        query: dict | None = None,
    ) -> list[dict]:
        logger.info("Calling list_documents")
        query = query or {}
        collection = await self.__get_documents_collection(collection_id)
        cursor = collection.find(query, {"embedding": 0})
        result = []
        async for document in cursor:
            document["id"] = str(document.pop("_id", ""))
            result.append(document)
        return result

    async def list_document_with_offset(
        self,
        collection_id: str,
        data: OffsetPaginationRequest,
    ) -> dict[str, Any]:
        logger.info("Calling list_document_with_offset")
        if not collection_id:
            return {"documents": [], "pagination": {}}
        # paginate_collection must be async
        return await paginate_collection(
            collection_name=self.__get_documents_collection_name(collection_id),
            data=data,
            client=self.client,
        )

    async def create_document(self, document: DocumentData, collection_id: str) -> str:
        collection = await self.__get_documents_collection(collection_id)
        persisted_document = await self.__create_persisted_document(
            document,
            collection_id,
        )
        result = await collection.insert_one(persisted_document)
        await self.vector_store.upsert(
            collection_name=self.__get_documents_collection_name(collection_id),
            vectors=[
                UpsertVector(
                    id=persisted_document["vector_id"],
                    vector=persisted_document["embedding"],
                    payload={
                        **persisted_document.get("metadata", {}),
                        "document_id": str(result.inserted_id),
                    },
                ),
            ],
        )
        logger.info("Created document in collection '%s'", collection_id)
        return str(result.inserted_id)

    async def create_documents(
        self,
        documents: list[DocumentData],
        collection_id: str,
    ) -> list[str]:
        logger.info("Calling create_documents")
        logger.info("Creating documents in collection '%s'", collection_id)
        if not documents:
            logger.info("No documents to create for collection '%s'", collection_id)
            return []
        persisted_documents = [
            await self.__create_persisted_document(document, collection_id)
            for document in documents
        ]
        collection_name = self.__get_documents_collection_name(collection_id)
        collection = await self.__get_documents_collection(collection_id)
        result = await collection.insert_many(persisted_documents)
        inserted_ids = [str(_id) for _id in result.inserted_ids]
        await self.vector_store.add(
            collection_name=collection_name,
            vectors=[
                AddVector(
                    id=document.get("vector_id"),
                    vector=document.get("embedding", []),
                    payload={
                        **document.get("metadata", {}),
                        "document_id": inserted_id,
                    },
                )
                for document, inserted_id in zip(
                    persisted_documents,
                    inserted_ids,
                    strict=False,
                )
            ],
        )
        return inserted_ids

    async def get_document(self, document_id, collection_id) -> dict:
        logger.info("Calling get_document")
        collection = await self.__get_documents_collection(collection_id)
        query = {"_id": ObjectId(document_id)}
        projection = {"embedding": 0}
        document = await collection.find_one(query, projection)
        if not document:
            raise LookupError("Not found")
        document["id"] = str(document.pop("_id", ""))
        return document

    async def update_document(self, document_id: str, data: dict, collection_id: str):
        logger.info("Calling update_document")
        collection = await self.__get_documents_collection(collection_id)
        data.pop("collection_id", "")
        update_data = {
            key: value for key, value in data.items() if key in ("content", "metadata")
        }
        if "content" in update_data:
            update_data["embedding"] = await self.__get_embedding(
                collection_id,
                update_data.get("content", ""),
            )
            logger.info("Re-creating embedding for document %s update", document_id)
        result = await collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data},
        )
        if "embedding" in update_data:
            await self.vector_store.upsert(
                collection_name=self.__get_documents_collection_name(collection_id),
                vectors=[
                    UpsertVector(
                        id=update_data.get("vector_id"),
                        vector=update_data["embedding"],
                        payload=update_data.get("metadata", {}),
                    ),
                ],
            )
        if result.matched_count == 0:
            raise LookupError("Nothing was updated")
        logger.info(
            "Updated document %s in collection '%s'",
            document_id,
            collection_id,
        )

    async def replace_document(
        self,
        document_id: str,
        data: DocumentData,
        collection_id: str,
    ):
        logger.info("Calling replace_document")
        logger.info(
            "Replacing document %s in collection '%s'",
            document_id,
            collection_id,
        )
        collection = await self.__get_documents_collection(collection_id)
        persisted_document = await self.__create_persisted_document(data, collection_id)
        result = await collection.replace_one(
            {"_id": ObjectId(document_id)},
            persisted_document,
        )
        await self.vector_store.upsert(
            collection_name=self.__get_documents_collection_name(collection_id),
            vectors=[
                UpsertVector(
                    id=persisted_document.get("vector_id"),
                    vector=persisted_document["embedding"],
                    payload=persisted_document.get("metadata", {}),
                ),
            ],
        )
        if result.matched_count == 0:
            raise LookupError("Nothing was replaced")
        logger.info(
            "Replaced document %s in collection '%s'",
            document_id,
            collection_id,
        )

    async def delete_document(self, document_id: str, collection_id: str):
        logger.info("Calling delete_document")
        collection = await self.__get_documents_collection(collection_id)
        doc = await collection.find_one({"_id": ObjectId(document_id)})
        if doc:
            vector_id = doc.get("vector_id")
            await self.vector_store.delete(
                collection_name=self.__get_documents_collection_name(collection_id),
                vector_id=vector_id,
            )
        result = await collection.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 0:
            raise LookupError("Nothing was deleted")
        logger.info(
            "Deleted document %s in collection '%s'",
            document_id,
            collection_id,
        )

    async def delete_documents(
        self,
        collection_id: str,
        document_ids: list[str] | None = None,
    ):
        logger.info("Calling delete_documents")
        collection = await self.__get_documents_collection(collection_id)
        query = {}
        if document_ids:
            document_object_ids = [
                ObjectId(document_id) for document_id in document_ids
            ]
            query = {"_id": {"$in": document_object_ids}}
        if document_ids:
            vector_ids = [
                doc.get("vector_id")
                async for doc in collection.find({"_id": {"$in": document_object_ids}})
            ]
            await self.vector_store.delete_many(
                collection_name=self.__get_documents_collection_name(collection_id),
                vector_ids=vector_ids,
            )
        result = await collection.delete_many(query)
        if document_ids and result.deleted_count < len(document_ids):
            logger.warning(
                "Deleted %s documents in collection '%s', requested to delete: %s",
                result.deleted_count,
                collection_id,
                len(document_ids),
            )
        logger.info(
            "Deleted documents in collection '%s': %s",
            collection_id,
            result.deleted_count,
        )

    async def delete_all_documents(self, collection_id: str):
        logger.info("Calling delete_all_documents")
        await self.delete_documents(collection_id)
        await self.update_collection_metadata(collection_id, {"last_synced": None})

    # region Helper Methods
    def __get_documents_collection_name(self, collection_id: str) -> str:
        logger.info("Calling __get_documents_collection_name")
        return f"{self.DOCUMENT_COLLECTION_PREFIX}{collection_id}"

    async def __get_documents_collection(
        self,
        collection_id: str,
    ) -> AsyncIOMotorCollection:
        logger.info("Calling __get_documents_collection")
        collection_name = self.__get_documents_collection_name(collection_id)
        collection = self.client.get_collection(collection_name)
        return collection

    async def __create_vector_search_index(self, collection_name: str) -> None:
        logger.info("Calling __create_vector_search_index")
        await self.vector_store.create_collection(collection_name)

    async def __create_persisted_document(
        self,
        document: DocumentData,
        collection_id: str,
    ) -> dict:
        logger.info("Calling __create_persisted_document")
        content = document.content
        metadata = document.metadata
        embedding = await self.__get_embedding(collection_id, content)
        persisted_document = {
            "vector_id": str(uuid.uuid4()),
            "content": content,
            "metadata": metadata,
            "embedding": embedding,
        }
        return persisted_document

    async def __get_embedding(
        self,
        collection_id: str,
        text: str,
        **kwargs,
    ) -> list[float]:
        logger.info("Calling __get_embedding")
        collection_metadata = await self.get_collection_metadata(collection_id)
        return await get_embeddings(
            text=text,
            model_system_name=collection_metadata.get("model"),
            **kwargs,
        )

    async def __get_embedding_by_model(
        self,
        model_system_name: str,
        text: str,
        **kwargs,
    ) -> list[float]:
        logger.info("Calling __get_embedding_by_model")
        return await get_embeddings(
            text=text,
            model_system_name=model_system_name,
            **kwargs,
        )

    async def __get_content_by_id(self, document_id: str, collection_id: str) -> str:
        logger.info("Calling __get_content_by_id")
        collection = await self.__get_documents_collection(collection_id)
        document = await collection.find_one({"_id": ObjectId(document_id)})
        if not document:
            return ""
        return document.get("content")

    # endregion

    # region Vector Search Methods
    @observe(
        name="Semantic search",
        description="Performing semantic (vector) search in knowledge source.",
        type=SpanType.SEARCH,
        capture_output=True,
    )
    async def __vector_search(
        self, *, collection_id: str, query: str, vector: list[float], num_results: int
    ) -> DocumentSearchResult:
        logger.debug(
            f"Performing vector search in collection_id: {collection_id} with num_results: {num_results}",
        )
        collection_config = await self.get_collection_metadata(collection_id)

        observability_context.update_current_span(
            input={
                "collection_id": collection_id,
                "collection_name": collection_config.get("name"),
                "query": query,
                "num_results": num_results,
            }
        )

        vector_search_result = await self.vector_store.search(
            collection_name=self.__get_documents_collection_name(collection_id),
            query_vector=vector,
            limit=num_results,
        )
        formatted_result = DocumentSearchResult(
            [
                DocumentSearchResultItem(
                    id=item["Id"],
                    score=Decimal(item["distance"]),
                    content=await self.__get_content_by_id(
                        document_id=item.get("metadata", {}).get("document_id", None),
                        collection_id=collection_id,
                    ),
                    collection_id=collection_id,
                    metadata=item["metadata"],
                )
                for item in vector_search_result
            ],
        )
        return formatted_result

    @override
    async def document_collections_similarity_search(
        self,
        collection_ids: list[str],
        query: str,
        retrieve_config: RetrieveConfig,
        num_results: int,
        filter: FilterObject | None = None,
    ) -> list:
        logger.info("Calling document_collections_similarity_search")
        if not collection_ids:
            logger.warning("No collections provided for similarity search.")
            return []
        logger.debug(
            f"Performing similarity search on multiple collections: {collection_ids} with query: {query}",
        )
        collection_model_map = {
            cid: (await self.get_collection_metadata(cid)).get("model")
            for cid in collection_ids
        }
        unique_models = {
            model for model in collection_model_map.values() if model is not None
        }
        embedding_cache = {}

        async def _get_embedding(model_name: str):
            try:
                embedding = await self.__get_embedding_by_model(model_name, query)
                return model_name, embedding
            except Exception as e:
                logger.error(
                    "Failed to get embedding for model %s: %s",
                    model_name,
                    e,
                    exc_info=True,
                )
                return model_name, None

        # Gather embeddings in parallel
        embedding_results = await asyncio.gather(
            *[_get_embedding(model) for model in unique_models],
        )
        for model_name, embedding in embedding_results:
            embedding_cache[model_name] = embedding

        async def _search_in_collection(cid: str):
            try:
                model_name = collection_model_map[cid]
                vector_for_collection = embedding_cache.get(model_name)
                if vector_for_collection is None:
                    logger.warning(
                        "Skipping collection %s due to missing embedding for model %s",
                        cid,
                        model_name,
                    )
                    return []
                result = await self.__vector_search(
                    collection_id=cid,
                    query=query,
                    vector=vector_for_collection,
                    num_results=num_results,
                )
                return result
            except Exception as e:
                logger.error(
                    "Exception in _search_in_collection for collection %s: %s",
                    cid,
                    e,
                    exc_info=True,
                )
                return []

        all_results = []
        search_results = await asyncio.gather(
            *[_search_in_collection(cid) for cid in collection_ids],
        )
        for result in search_results:
            if result:
                all_results.extend(result)
        search_result_sorted = sorted(
            all_results,
            key=lambda x: getattr(x, "score", 0),
            reverse=True,
        )
        return search_result_sorted

    async def document_collections_query_chunks_context(
        self,
        query: QueryChunksByCollectionBySource,
    ) -> ChunksByCollection:
        logger.info("Calling document_collections_query_chunks_context")
        list_inputs = []
        for collection_id, chunk_numbers_by_source_id in query.items():
            query_items = []
            for source_id, chunk_numbers in chunk_numbers_by_source_id.items():
                query_items.append(
                    {
                        "metadata.sourceId": source_id,
                        "metadata.chunkNumber": {"$in": chunk_numbers},
                    },
                )
            query_collection = {"$or": query_items}
            list_inputs.append(
                {"collection_id": collection_id, "query": query_collection},
            )
        # Run list_documents in parallel
        list_documents_results = await asyncio.gather(
            *[self.list_documents(**input) for input in list_inputs],
        )
        result = {}
        for list_input, list_result in zip(
            list_inputs,
            list_documents_results,
            strict=False,
        ):
            collection_id = list_input.get("collection_id")
            result[collection_id] = list_result
        return result

    # endregion
