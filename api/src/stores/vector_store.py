from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class AddVector(BaseModel):
    id: str
    vector: list[float]  # Required
    payload: dict[str, Any] | None = None  # Optional metadata


class UpsertVector(BaseModel):
    id: str  # Required for upsert
    vector: list[float]  # Optional
    payload: dict[str, Any] | None = None  # Optional metadata


class UpdateMetadataVector(BaseModel):
    id: str  # Required for metadata update
    payload: dict[str, Any]  # Metadata to update


class VectorStore(ABC):
    @abstractmethod
    async def __init__(self, client: Any, prefix: str):
        """Initializes the store with a client and a prefix for collections."""

    # region Collection Management
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Creates a new collection for storing vectors with optional configuration."""

    @abstractmethod
    async def recreate_collection(
        self,
        collection_name: str,
        config: dict[str, Any] | None = None,
    ):
        """Clears the specified collection and recreates it."""

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection from the store."""

    # endregion

    # region Search
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        k: int | None = None,
    ) -> list[dict]:
        """Searches for the nearest vectors to the query in the specified collection, considering the limit."""

    @abstractmethod
    async def filter_and_search(
        self,
        collection_name: str,
        query_vector: list[float],
        metadata_filter: dict[str, Any],
        limit: int,
        k: int | None = None,
    ) -> list[dict]:
        """Filters by metadata, then performs vector search in the specified collection."""

    # endregion

    # region Vector Operations
    @abstractmethod
    async def get(self, collection_name: str, vector_id: str) -> dict:
        """Returns a vector and metadata by ID from the specified collection."""

    @abstractmethod
    async def add(self, collection_name: str, vectors: list[AddVector]):
        """Adds vectors with metadata and optional IDs to the specified collection."""

    @abstractmethod
    async def upsert(self, collection_name: str, vectors: list[UpsertVector]):
        """Creates or updates vectors with metadata and IDs in the specified collection."""

    @abstractmethod
    async def delete(self, collection_name: str, vector_id: str):
        """Deletes a vector by ID from the specified collection."""

    @abstractmethod
    async def delete_many(self, collection_name: str, vector_ids: list[str]):
        """Deletes multiple vectors by their IDs from the specified collection."""

    @abstractmethod
    async def update_metadata(
        self,
        collection_name: str,
        vectors: list[UpdateMetadataVector],
    ):
        """Updates only the metadata (payload) of vectors by ID in the specified collection."""

    # endregion

    # region Collection Information
    @abstractmethod
    async def collection_info(self, collection_name: str) -> dict:
        """Returns information about the collection."""

    # endregion
