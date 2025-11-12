import asyncio
from typing import Any
from venv import logger

# Assume an async-compatible Qdrant client is available as AsyncQdrantClient
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from stores.vector_store import (
    AddVector,
    UpdateMetadataVector,
    UpsertVector,
    VectorStore,
)


class QdrantVectorStore(VectorStore):
    # region Initialization
    def __init__(self, client: AsyncQdrantClient, prefix: str):
        """Initialize the store with an async Qdrant client and prefix."""
        self.client = client
        self.prefix = prefix

    # endregion

    def _get_full_name(self, collection_name: str) -> str:
        """Helper method to build the full collection name."""
        return f"{self.prefix}_{collection_name}"

    # region Collection Management
    async def create_collection(
        self,
        collection_name: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection in Qdrant."""
        full_name = self._get_full_name(collection_name)
        if config is None:
            config = {}

        dimension = config.get("dimension", 1536)  # Default is 1536 if not specified
        distance = config.get("distance", "Cosine").upper()  # Default is Cosine

        try:
            await self.client.create_collection(
                collection_name=full_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance[distance],
                ),
            )
        except Exception as e:
            logger.error(f"Failed to create collection {full_name}: {e}")
            raise

    async def recreate_collection(
        self,
        collection_name: str,
        config: dict[str, Any] | None = None,
    ):
        """Clear the specified collection."""
        full_name = self._get_full_name(collection_name)
        try:
            await self.client.delete_collection(collection_name=full_name)
            await self.create_collection(
                collection_name,
                config=config,
            )  # Recreate an empty collection
        except Exception as e:
            logger.error(f"Failed to recreate collection {full_name}: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        full_name = self._get_full_name(collection_name)
        try:
            return await self.client.delete_collection(full_name)
        except Exception as e:
            logger.error(f"Failed to delete collection {full_name}: {e}")
            raise

    # endregion

    # region Search
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        k: int | None = None,
    ) -> list[dict]:
        """Search for the nearest vectors to the query vector in the specified collection."""
        full_name = self._get_full_name(collection_name)
        try:
            results = await self.client.search(
                collection_name=full_name,
                query_vector=query_vector,
                limit=limit,
            )
            return [
                {
                    "id": str(result.id),
                    "distance": result.score,
                    "metadata": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Search failed in collection {full_name}: {e}")
            raise

    async def filter_and_search(
        self,
        collection_name: str,
        query_vector: list[float],
        metadata_filter: dict[str, Any],
        limit: int,
        k: int | None = None,
    ) -> list[dict]:
        """Filter by metadata and perform a vector search in the specified collection."""
        full_name = self._get_full_name(collection_name)
        filter = models.Filter(
            must=[
                models.FieldCondition(key=key, match=models.MatchValue(value=value))
                for key, value in metadata_filter.items()
            ],
        )
        try:
            results = await self.client.search(
                collection_name=full_name,
                query_vector=query_vector,
                query_filter=filter,
                limit=limit,
            )
            return [
                {
                    "id": str(result.id),
                    "distance": result.score,
                    "metadata": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Filter and search failed in collection {full_name}: {e}")
            raise

    # endregion

    # region Vector Operations
    async def get(self, collection_name: str, vector_id: str) -> dict:
        """Retrieve a vector and its metadata by ID from the specified collection."""
        full_name = self._get_full_name(collection_name)
        try:
            result = await self.client.retrieve(
                collection_name=full_name,
                ids=[vector_id],
            )
            if result:
                point = result[0]
                return {
                    "id": str(point.id),
                    "vector": point.vector,
                    "metadata": point.payload,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id} from {full_name}: {e}")
            raise

    async def add(self, collection_name: str, vectors: list[AddVector]):
        """Add vectors to the specified collection (without updating existing ones)."""
        logger.info("Adding vectors to collection")
        full_name = self._get_full_name(collection_name)
        points = [
            models.PointStruct(
                id=vector.id,
                vector=vector.vector,
                payload=vector.payload if hasattr(vector, "payload") else {},
            )
            for vector in vectors
        ]
        try:
            await self.client.upsert(collection_name=full_name, points=points)
        except Exception as e:
            logger.error(f"Failed to add vectors to {full_name}: {e}")
            raise

    async def upsert(self, collection_name: str, vectors: list[UpsertVector]):
        """Create or update vectors in the specified collection."""
        logger.info("Upserting vectors in collection")
        full_name = self._get_full_name(collection_name)
        points = [
            models.PointStruct(
                id=vector.id,
                vector=vector.vector,
                payload=vector.payload if hasattr(vector, "payload") else {},
            )
            for vector in vectors
        ]
        try:
            await self.client.upsert(collection_name=full_name, points=points)
        except Exception as e:
            logger.error(f"Failed to upsert vectors in {full_name}: {e}")
            raise

    async def delete(self, collection_name: str, vector_id: str):
        """Delete a vector by ID from the specified collection."""
        full_name = self._get_full_name(collection_name)
        try:
            await self.client.delete(
                collection_name=full_name,
                points_selector=models.PointIdsList(points=[vector_id]),
            )
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_id} from {full_name}: {e}")
            raise

    async def delete_many(self, collection_name: str, vector_ids: list[str]):
        """Delete multiple vectors by their IDs from the specified collection."""
        full_name = self._get_full_name(collection_name)
        try:
            await self.client.delete(
                collection_name=full_name,
                points_selector=models.PointIdsList(points=vector_ids),
            )
        except Exception as e:
            logger.error(f"Failed to delete vectors from {full_name}: {e}")
            raise

    async def update_metadata(
        self,
        collection_name: str,
        vectors: list[UpdateMetadataVector],
    ):
        """Update only the metadata (payload) of vectors by ID in the specified collection."""
        full_name = f"{self.prefix}_{collection_name}"

        try:
            await asyncio.gather(
                *[
                    self.client.batch_update_points(
                        collection_name=full_name,
                        update_operations=[
                            models.OverwritePayloadOperation(
                                overwrite_payload=models.SetPayload(
                                    payload=vector.payload
                                    if hasattr(vector, "payload")
                                    else {},
                                    points=[vector.id],
                                ),
                            )
                            for vector in vectors
                        ],
                    ),
                ],
            )
        except Exception as e:
            logger.error(f"Failed to update metadata in {full_name}: {e}")
            raise

    # endregion

    # region Collection Information

    async def collection_info(self, collection_name: str) -> dict:
        """Return information about the collection."""
        full_name = self._get_full_name(collection_name)
        try:
            info = await self.client.get_collection(full_name)
            return info.model_dump()
        except Exception as e:
            logger.error(f"Failed to get collection info for {full_name}: {e}")
            raise

    # endregion
