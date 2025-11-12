# Async compatibility check: True
from abc import ABC, abstractmethod
from typing import Any

from models import (
    ChunksByCollection,
    DocumentData,
    DocumentSearchResult,
    QueryChunksByCollectionBySource,
)
from type_defs.pagination import FilterObject, OffsetPaginationRequest
from validation.rag_tools import RetrieveConfig


class DocumentStore(ABC):
    @abstractmethod
    async def list_collections(self, query: dict | None = None) -> list[dict]: ...

    @abstractmethod
    async def create_collection(self, metadata: dict) -> str: ...

    @abstractmethod
    async def get_collection_metadata(self, collection_id: str) -> dict: ...

    @abstractmethod
    async def update_collection_metadata(self, collection_id: str, metadata: dict): ...

    @abstractmethod
    async def replace_collection_metadata(self, collection_id: str, metadata: dict): ...

    @abstractmethod
    async def delete_collection(self, collection_id: str): ...

    @abstractmethod
    async def list_documents(
        self,
        collection_id,
        query: dict | None = None,
    ) -> list[dict]: ...

    @abstractmethod
    async def create_document(
        self,
        document: DocumentData,
        collection_id: str,
    ) -> str: ...

    @abstractmethod
    async def create_documents(
        self,
        documents: list[DocumentData],
        collection_id: str,
    ) -> list[str]: ...

    @abstractmethod
    async def get_document(self, document_id, collection_id) -> dict: ...

    @abstractmethod
    async def update_document(
        self,
        document_id: str,
        data: dict,
        collection_id: str,
    ): ...

    @abstractmethod
    async def replace_document(
        self,
        document_id: str,
        data: DocumentData,
        collection_id: str,
    ): ...

    @abstractmethod
    async def delete_document(self, document_id: str, collection_id: str): ...

    @abstractmethod
    async def delete_documents(self, document_ids: list[str], collection_id: str): ...

    @abstractmethod
    async def delete_all_documents(self, collection_id: str): ...

    @abstractmethod
    async def document_collections_query_chunks_context(
        self,
        query: QueryChunksByCollectionBySource,
    ) -> ChunksByCollection: ...

    @abstractmethod
    async def document_collections_similarity_search(
        self,
        collection_ids: list[str],
        retrieve_config: RetrieveConfig,
        query: str,
        num_results: int,
        filter: FilterObject | None = None,
    ) -> DocumentSearchResult: ...

    @abstractmethod
    async def list_document_with_offset(
        self,
        collection_id: str,
        data: OffsetPaginationRequest,
    ) -> dict[str, Any]: ...
