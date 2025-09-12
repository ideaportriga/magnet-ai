import array
import json
from decimal import ROUND_HALF_UP, Decimal
from logging import getLogger
from typing import Any

import oracledb
import regex
import yake

from models import (
    ChunksByCollection,
    DocumentData,
    DocumentSearchResult,
    DocumentSearchResultItem,
    QueryChunksByCollectionBySource,
)
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType
from stores.document_store import DocumentStore
from stores.oracle.client import OracleDbClient
from type_defs.pagination import OffsetPaginationRequest
from utils.pagination_utils import paginate_collection
from utils.search_utils import reciprocal_rank_fusion
from utils.serializer import OracleDbSerializer

logger = getLogger(__name__)
logger.setLevel("DEBUG")


class OracleDbStore(DocumentStore):
    COLLECTIONS_DV = "collections_dv"
    DOCUMENTS_DV = "documents_dv"
    DOCUMENTS_TABLE = "documents"

    def __init__(self, client: OracleDbClient):
        self.client = client

    async def list_collections(self, query: dict | None = None) -> list[dict]:
        logger.debug(f"Listing collections with query {query}.")
        query = query or {}
        collection = self.client.get_collection(self.COLLECTIONS_DV.upper())

        result = []
        cursor = collection.find(query)
        async for row in cursor:
            row.pop("_metadata", None)
            row["id"] = row.pop("_id", "")
            result.append(row)
        logger.debug(f"Total collections retrieved: {len(result)}")
        return result

    async def create_collection(self, metadata: dict) -> str:
        logger.debug(f"Creating collection with metadata: {metadata}")

        if metadata.get("chunk_size") == "":
            metadata["chunk_size"] = None

        def convert_datetime(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return obj

        json_data = json.dumps(metadata, default=convert_datetime)
        sql = f"INSERT INTO {self.COLLECTIONS_DV} (DATA) VALUES (:json_data) RETURNING JSON_VALUE(DATA, '$._id') INTO :id_out"

        async with await self.client._pool.acquire() as connection:
            async with connection.cursor() as cursor:
                id_out = cursor.var(oracledb.STRING)
                bindvars = {"json_data": json_data, "id_out": id_out}
                await cursor.execute(sql, bindvars)
                await connection.commit()
                _id = id_out.getvalue()
        logger.info(f"Collection created with id: {_id}")
        return _id[0]

    async def get_collection_metadata(self, collection_id: str) -> dict:
        logger.debug(f"Fetching metadata for collection_id: {collection_id}")
        sql = f'SELECT JSON_SERIALIZE(DATA) FROM {self.COLLECTIONS_DV} D WHERE D.DATA."_id" = :id'
        async with self.client.execute(sql, {"id": collection_id}) as cursor:
            row = await cursor.fetchone()
            if not row:
                logger.error("Collection does not exist.")
                raise LookupError("Collection does not exist")

            try:
                metadata = json.loads(row[0])
                metadata["id"] = str(metadata.pop("_id", ""))
                logger.debug(
                    f"Metadata was successfully retrieved for collection_id: {collection_id}",
                )
                return metadata
            except json.JSONDecodeError:
                logger.error(
                    f"Failed to parse metadata for collection_id: {collection_id}"
                )
                logger.error(f"Row: {row}")
                raise ValueError("Invalid metadata format")

    async def update_collection_metadata(self, collection_id: str, metadata: dict):
        logger.debug(
            f"Updating metadata for collection_id: {collection_id} with data: {metadata}",
        )
        if metadata.get("chunk_size") is None:
            metadata.pop("chunk_size", None)
        metadata_json = json.dumps(metadata)
        sql = f"""
            UPDATE {self.COLLECTIONS_DV} D
            SET DATA = JSON_MERGEPATCH(D.DATA, :metadata)
            WHERE D.DATA."_id" = :id
            """
        params = {"metadata": metadata_json, "id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            cursor.connection.commit()
            logger.info(f"Updated metadata for collection '{collection_id}'")

    async def replace_collection_metadata(self, collection_id: str, metadata: dict):
        logger.debug(
            f"Replacing metadata for collection_id: {collection_id} with data: {metadata}",
        )
        if metadata.get("chunk_size") == "":
            metadata["chunk_size"] = None
        metadata["_id"] = collection_id
        metadata_json = json.dumps(metadata)
        sql = f'UPDATE {self.COLLECTIONS_DV} D SET DATA = :metadata WHERE D.DATA."_id" = :id'
        params = {"metadata": metadata_json, "id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            cursor.connection.commit()
            logger.info(f"Replaced metadata for collection '{collection_id}'")

    async def delete_collection(self, collection_id: str):
        logger.debug(f"Deleting collection with id: {collection_id}")
        sql_delete_collection = (
            f'DELETE FROM {self.COLLECTIONS_DV} D WHERE D.DATA."_id" = :id'
        )
        params = {"id": collection_id}
        async with self.client.execute(sql_delete_collection, params) as cursor:
            cursor.connection.commit()
            logger.info(f"Deleted collection '{collection_id}' and its documents")

    async def list_documents(
        self,
        collection_id: str,
        query: dict | None = None,
    ) -> list[dict]:
        logger.debug(
            f">>>>Listing documents in collection_id: {collection_id} with query: {query}",
        )
        query = query or {}
        query_with_collection = {"collection_id": collection_id}

        if query:
            query_with_collection.update(query)
        query["collection_id"] = collection_id
        logger.debug(f"Modified query {query}")
        collection = self.client.get_collection(self.DOCUMENTS_DV.upper())

        result = []
        cursor = collection.find(query)
        async for row in cursor:
            row.pop("_metadata", None)
            row["id"] = row.pop("_id", "")
            result.append(row)
        logger.debug(f"Total documents retrieved: {len(result)}")
        return result

    async def list_document_with_offset(
        self,
        collection_id: str,
        data: OffsetPaginationRequest,
    ) -> dict[str, Any]:
        return await paginate_collection(
            collection_name=self.DOCUMENTS_DV.upper(),
            data=data,
            additional_filters={"collection_id": collection_id},
            client=self.client,
        )

    async def __get_embedding_by_model(
        self,
        model_system_name: str,
        text: str,
        **kwargs,
    ) -> list[float]:
        return await get_embeddings(
            text=text, model_system_name=model_system_name, **kwargs
        )

    async def create_document(self, document: DocumentData, collection_id: str) -> str:
        logger.debug(
            f">>>Creating document in collection_id: {collection_id} with data: {document}",
        )
        if not document:
            logger.info(f"No document to create for collection '{collection_id}'")
            return ""

        collection_config = await self.get_collection_metadata(collection_id)
        embedding_model = collection_config.get("model")

        if not embedding_model:
            raise ValueError("Embedding model is not set for collection")

        embedding = await get_embeddings(document.content, embedding_model)
        vector_data_64 = array.array("d", embedding)

        sql = f"INSERT INTO {self.DOCUMENTS_TABLE} (collection_id, content, metadata, embedding) VALUES (:collection_id, :content, :metadata, :embedding) RETURNING id INTO :id_out"

        async with await self.client._pool.acquire() as connection:
            async with connection.cursor() as cursor:
                id_out = cursor.var(oracledb.STRING)
                bind_vars = {
                    "collection_id": collection_id,
                    "content": document.content,
                    "metadata": document.metadata,
                    "embedding": vector_data_64,
                    "id_out": id_out,
                }
                cursor.setinputsizes(
                    collection_id=oracledb.STRING,
                    content=oracledb.CLOB,
                    metadata=oracledb.DB_TYPE_JSON,
                    embedding=oracledb.DB_TYPE_BINARY_DOUBLE,
                    id_out=oracledb.STRING,
                )
                await cursor.execute(sql, bind_vars)
                cursor.connection.commit()
                document_id = id_out.getvalue()
        logger.info(
            f"Created document with id: {document_id} in collection '{collection_id}'",
        )
        return document_id[0]

    async def create_documents(
        self,
        documents: list[DocumentData],
        collection_id: str,
    ) -> list[str]:
        logger.debug(f"Creating multiple documents in collection_id: {collection_id}")

        if not documents:
            logger.info(f"No documents to create for collection '{collection_id}'")
            return []

        collection_config = await self.get_collection_metadata(collection_id)
        semantic_search_supported = collection_config.get("indexing", {}).get(
            "semantic_search_supported",
        ) or not collection_config.get("indexing")
        embedding_model = collection_config.get("model")

        if not embedding_model:
            raise ValueError("Embedding model is not set for collection")

        document_ids = []

        sql = f"INSERT INTO {self.DOCUMENTS_TABLE} (collection_id, content, metadata, embedding) VALUES (:collection_id, :content, :metadata, :embedding) RETURNING id INTO :id_out"
        async with await self.client._pool.acquire() as connection:
            for document in documents:
                logger.debug(
                    f"Processing document: {document.metadata.get('sourceId')}"
                )

                if semantic_search_supported:
                    embeddings = await get_embeddings(document.content, embedding_model)
                    semantic_dense_vector = array.array("d", embeddings)
                else:
                    semantic_dense_vector = None

                async with connection.cursor() as cursor:
                    id_out = cursor.var(oracledb.STRING)
                    bind_vars = {
                        "collection_id": collection_id,
                        "content": document.content,
                        "metadata": document.metadata,
                        "embedding": semantic_dense_vector,
                        "id_out": id_out,
                    }
                    cursor.setinputsizes(
                        collection_id=oracledb.STRING,
                        content=oracledb.CLOB,
                        metadata=oracledb.DB_TYPE_JSON,
                        embedding=oracledb.DB_TYPE_BINARY_DOUBLE,
                        id_out=oracledb.STRING,
                    )
                    await cursor.execute(sql, bind_vars)
                    document_id = id_out.getvalue()
                    document_ids.append(document_id)
            await connection.commit()

        logger.info(
            f"Created {len(document_ids)} documents in collection '{collection_id}'",
        )
        logger.info(document_ids)
        return document_ids

    async def get_document(self, document_id, collection_id) -> dict:
        logger.debug(
            f"Fetching document with id: {document_id} from collection '{collection_id}'",
        )
        sql = f"""
            SELECT DATA FROM {self.DOCUMENTS_DV} D
            WHERE D.DATA.\"_id\" = :id AND D.DATA.\"collection_id\" = :collection_id
        """
        params = {"id": document_id, "collection_id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            row = await cursor.fetchone()
            if not row:
                logger.error("Document not found.")
                raise LookupError("Not found")
            document = row[0]
            document.pop("collection_id", "")
            document.pop("_metadata", "")
            document["id"] = document.pop("_id", "")
            logger.debug(f"Retrieved document: {document}")
            return document

    async def update_document(self, document_id: str, data: dict, collection_id: str):
        logger.debug(
            f"Updating document with id: {document_id} in collection '{collection_id}' with data: {data}",
        )
        if "content" not in data and "metadata" not in data:
            logger.info(
                f"No update needed for document {document_id} in collection '{collection_id}'",
            )
            return

        existing_document = await self.get_document(document_id, collection_id)
        existing_metadata = existing_document.get("metadata", {})
        bind_vars: dict[str, Any] = {
            "id": document_id,
        }
        set_clauses = []
        input_sizes = {
            "id": oracledb.STRING,
        }

        collection_config = await self.get_collection_metadata(collection_id)
        embedding_model = collection_config.get("model")

        if not embedding_model:
            raise ValueError("Embedding model is not set for collection")

        if "metadata" in data:
            existing_metadata.update(data["metadata"])
            bind_vars["metadata"] = json.dumps(existing_metadata)
            set_clauses.append("metadata = :metadata")
            input_sizes["metadata"] = oracledb.DB_TYPE_JSON
        if "content" in data:
            bind_vars["content"] = data["content"]
            set_clauses.append("content = :content")
            input_sizes["content"] = oracledb.CLOB
            embedding = await get_embeddings(data["content"], embedding_model)
            vector_data_64 = array.array("d", embedding)
            bind_vars["embedding"] = vector_data_64
            set_clauses.append("embedding = :embedding")
            input_sizes["embedding"] = oracledb.DB_TYPE_BINARY_DOUBLE

        set_clause = ", ".join(set_clauses)
        sql = f"UPDATE {self.DOCUMENTS_TABLE} D SET {set_clause} WHERE D.id = :id"
        async with await self.client._pool.acquire() as connection:
            async with connection.cursor() as cursor:
                cursor.setinputsizes(**input_sizes)
                async with self.client.execute(sql, bind_vars) as cursor:
                    cursor.connection.commit()
        logger.info(f"Updated document {document_id} in collection '{collection_id}'")

    async def replace_document(
        self,
        document_id: str,
        data: DocumentData,
        collection_id: str,
    ):
        logger.debug(
            f"Replacing document with id: {document_id} in collection '{collection_id}' with data: {data}",
        )

        collection_config = await self.get_collection_metadata(collection_id)
        embedding_model = collection_config.get("model")

        if not embedding_model:
            raise ValueError("Embedding model is not set for collection")

        embedding = await get_embeddings(data.content, embedding_model)
        vector_data_64 = array.array("d", embedding)
        bind_vars = {
            "id": document_id,
            "content": data.content,
            "metadata": json.dumps(data.metadata),
            "embedding": vector_data_64,
        }

        async with await self.client._pool.acquire() as connection:
            async with connection.cursor() as cursor:
                cursor.setinputsizes(
                    id=oracledb.STRING,
                    content=oracledb.CLOB,
                    metadata=oracledb.DB_TYPE_JSON,
                    embedding=oracledb.DB_TYPE_BINARY_DOUBLE,
                )
                sql = f"UPDATE {self.DOCUMENTS_TABLE} D SET content = :content, metadata = :metadata, embedding = :embedding WHERE D.id = :id"
                async with self.client.execute(sql, bind_vars) as cursor:
                    cursor.connection.commit()
        logger.info(f"Replaced document {document_id} in collection '{collection_id}'")

    async def delete_document(self, document_id: str, collection_id: str):
        logger.debug(
            f"Deleting document with id: {document_id} from collection '{collection_id}'",
        )
        sql = f"""
            DELETE FROM {self.DOCUMENTS_TABLE} D
            WHERE D.id = :id AND D.collection_id = :collection_id
        """
        params = {"id": document_id, "collection_id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            if cursor.rowcount == 0:
                error_message = f"Document with id {document_id} not found in collection '{collection_id}'"
                logger.error(error_message)
                raise ValueError(error_message)
            cursor.connection.commit()
            logger.info(
                f"Deleted document {document_id} from collection '{collection_id}'"
            )

    async def delete_documents(
        self,
        collection_id: str,
        document_ids: list[str] | None = None,
    ):
        logger.debug(
            f"Deleting documents from collection_id: {collection_id}, document_ids: {document_ids}",
        )
        if document_ids:
            ids_str = ", ".join(f"'{doc_id.upper()}'" for doc_id in document_ids)
            sql = f"""
                DELETE FROM {self.DOCUMENTS_TABLE} D
                WHERE D.collection_id = :collection_id AND D.id IN ({ids_str})
            """
            params = {"collection_id": collection_id}
        else:
            sql = f"DELETE FROM {self.DOCUMENTS_TABLE} D WHERE D.collection_id = :collection_id"
            params = {"collection_id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            cursor.connection.commit()
            logger.info(f"Deleted documents from collection '{collection_id}'")

    async def delete_all_documents(self, collection_id: str):
        logger.debug(f"Deleting all documents from collection_id: {collection_id}")
        sql = f"DELETE FROM {self.DOCUMENTS_TABLE} D WHERE D.collection_id = :collection_id"
        params = {"collection_id": collection_id}
        async with self.client.execute(sql, params) as cursor:
            cursor.connection.commit()
            deleted_count = cursor.rowcount
            logger.info(
                f"Deleted {deleted_count} documents from collection '{collection_id}'",
            )

        await self.update_collection_metadata(collection_id, {"last_synced": None})

        return deleted_count

    async def __assert_collection_exist(self, collection_id: str) -> None:
        logger.debug(f"Asserting existence of collection_id: {collection_id}")
        await self.get_collection_metadata(collection_id)

    @observe(
        name="Vector search",
        type=SpanType.SEARCH,
        capture_input=True,
        capture_output=True,
    )
    async def __vector_search(
        self,
        collection_id: str,
        query: str,
        vector: list[float],
        num_results: int,
    ) -> DocumentSearchResult:
        logger.debug(
            f"Performing vector search in collection_id: {collection_id} with num_results: {num_results}",
        )
        await self.__assert_collection_exist(collection_id)

        observability_context.update_current_span(
            description=f"Performing vector search in Oracle Autonomous Database and taking only {num_results} first results.",
            extra_data={
                "table_name": self.DOCUMENTS_TABLE,
                "store": "oracle",
            },
        )

        vector_data_64 = array.array("d", vector)
        sql = f"SELECT id, content, metadata, VECTOR_DISTANCE(D.embedding, :query_embedding) AS V FROM {self.DOCUMENTS_TABLE} D WHERE D.collection_id = :collection_id ORDER BY V FETCH NEXT {num_results} ROWS ONLY"

        params = {
            "query_embedding": vector_data_64,
            "collection_id": collection_id,
        }
        logger.debug(f"Executing similarity search SQL: {sql}")

        async with self.client.execute(sql, params) as cursor:
            result = []
            async for row in cursor:
                id = row[0]
                content = await row[1].read()  # to convert it to a string
                metadata = json.loads(json.dumps(row[2], cls=OracleDbSerializer))
                vector_similarity_score = (1 - Decimal(row[3])).quantize(
                    Decimal("0.0000"),
                    rounding=ROUND_HALF_UP,
                )
                result.append(
                    DocumentSearchResultItem(
                        id=id,
                        score=vector_similarity_score,
                        content=content,
                        collection_id=collection_id,
                        metadata=metadata,
                    ),
                )
            logger.debug(f"Similarity search results count: {len(result)}")
            return result

    @observe(
        name="Full text search",
        type=SpanType.SEARCH,
        capture_input=True,
        capture_output=True,
    )
    async def __full_text_search(
        self,
        collection_id: str,
        query: str,
        num_results: int,
    ) -> DocumentSearchResult:
        logger.debug(
            f"Performing full text search on collection_id: {collection_id} with query: {query}",
        )

        def extract_keywords(query: str, num_results: int):
            max_ngram_size = 2
            windowSize = 1

            kw_extractor = yake.KeywordExtractor(
                n=max_ngram_size,
                windowsSize=windowSize,
                top=num_results,
                features=None,
            )
            keywords = kw_extractor.extract_keywords(query.strip().lower())
            return sorted(keywords, key=lambda kw: kw[1])

        keywords = extract_keywords(query, 4)

        sql = f"SELECT id, content, metadata, SCORE(1) AS V FROM {self.DOCUMENTS_TABLE} D WHERE D.collection_id = :collection_id AND CONTAINS(D.content, :query_keywords, 1) > 0 ORDER BY V DESC FETCH NEXT {num_results} ROWS ONLY"

        stemmed_keywords = []
        splitter = regex.compile(r"[^\p{L}\p{N}_\+\-/]")
        for keyword in keywords:
            stemmed_keyword = ""
            for single_word in splitter.split(keyword[0]):
                stemmed_keyword += "$" + single_word + " "
            stemmed_keywords.append(stemmed_keyword.strip())
        params = {
            "collection_id": collection_id,
            "query_keywords": ",".join(stemmed_keywords),
        }
        async with self.client.execute(sql, params) as cursor:
            result = []
            async for row in cursor:
                id = row[0]
                content = await row[1].read()  # to convert it to a string
                metadata = json.loads(json.dumps(row[2], cls=OracleDbSerializer))
                score = Decimal(row[3]).quantize(
                    Decimal("0.0000"), rounding=ROUND_HALF_UP
                )
                result.append(
                    DocumentSearchResultItem(
                        id=id,
                        score=score,
                        content=content,
                        collection_id=collection_id,
                        metadata=metadata,
                    ),
                )
            logger.debug(f"Full text search results count: {len(result)}")
            return result

    async def document_collection_similarity_search(
        self,
        collection_id: str,
        query: str,
        num_results: int,
    ) -> DocumentSearchResult:
        logger.debug(
            f"Performing similarity search on collection_id: {collection_id} with query: {query}",
        )

        collection_config = await self.get_collection_metadata(collection_id)
        embedding_model = collection_config.get("model")

        if not embedding_model:
            raise ValueError("Embedding model is not set for collection")

        vector = await get_embeddings(query, embedding_model)
        return await self.__vector_search(collection_id, query, vector, num_results)

    async def document_collections_similarity_search(
        self,
        collection_ids: list[str],
        query: str,
        num_results: int,
    ) -> list:
        if not collection_ids:
            logger.warning("No collections provided for similarity search.")
            return []

        if not query:
            logger.warning("No query provided for similarity search.")
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

        import asyncio

        embedding_results = await asyncio.gather(
            *[_get_embedding(model) for model in unique_models]
        )
        for model_name, embedding in embedding_results:
            embedding_cache[model_name] = embedding

        async def _search_in_collection(cid: str):
            try:
                collection_config = await self.get_collection_metadata(cid)
                semantic_search_supported = collection_config.get("indexing", {}).get(
                    "semantic_search_supported",
                ) or not collection_config.get("indexing")
                full_text_search_supported = collection_config.get("indexing", {}).get(
                    "fulltext_search_supported",
                )

                semantic_search_result = []
                full_text_search_result = []

                if semantic_search_supported:
                    model_name = collection_model_map[cid]
                    vector_for_collection = embedding_cache.get(model_name)

                    if vector_for_collection:
                        semantic_search_result = await self.__vector_search(
                            collection_id=cid,
                            query=query,
                            vector=vector_for_collection,
                            num_results=num_results,
                        )
                    else:
                        logger.warning(
                            "Skipping collection %s due to missing embedding for model %s",
                            cid,
                            model_name,
                        )

                if full_text_search_supported:
                    full_text_search_result = await self.__full_text_search(
                        collection_id=cid,
                        query=query,
                        num_results=num_results,
                    )

                if semantic_search_supported and full_text_search_supported:
                    return reciprocal_rank_fusion(
                        semantic_search_result,
                        full_text_search_result,
                        num_results,
                    )
                if semantic_search_supported:
                    return semantic_search_result
                if full_text_search_supported:
                    return full_text_search_result
                return []
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
            *[_search_in_collection(cid) for cid in collection_ids]
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
        logger.debug(f"Querying chunks context with query: {query}")
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

        import asyncio

        list_documents_results = await asyncio.gather(
            *[self.list_documents(**input) for input in list_inputs]
        )

        result = {}
        for list_input, list_result in zip(
            list_inputs, list_documents_results, strict=False
        ):
            collection_id = list_input.get("collection_id")
            result[collection_id] = list_result

        return result
