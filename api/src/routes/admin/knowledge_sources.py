from typing import Any

from bson import errors
from litestar import Controller, Router, delete, get, patch, post, put
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT

from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from core.plugins.registry import PluginRegistry
from data_sync.synchronizer import Synchronizer
from models import DocumentData
from services.knowledge_sources.models import (
    MetadataAutomapRequest,
    MetadataAutomapResponse,
)
from services.knowledge_sources.services import automap_metadata
from services.observability import observability_context, observe
from services.observability.models import FeatureType
from services.utils.get_ids_by_system_names import get_ids_by_system_names
from stores import get_db_store
from stores.utils import validate_id
from type_defs.pagination import (
    OffsetPaginationRequest,
)
from utils.datetime_utils import utc_now

store = get_db_store()

DOCUMENT_COLLECTION_PREFIX = "documents_"

# Load all knowledge source plugins on module import
PluginRegistry.auto_load()


async def sync_collection_standalone(collection_id: str, **kwargs) -> None:
    """Standalone function to sync a collection using the plugin system.

    This function uses the plugin registry to dynamically load and execute
    the appropriate knowledge source plugin based on the collection's source type.

    Args:
        collection_id: The ID of the collection to sync

    Raises:
        ClientException: If source type is unknown or plugin not found
    """
    collection_config = await store.get_collection_metadata(collection_id)
    observability_context.update_current_trace(
        name=collection_config.get("name"), type=FeatureType.KNOWLEDGE_SOURCE.value
    )

    source = collection_config.get("source", {})
    source_type = source.get("source_type")

    # Get plugin from registry
    plugin = PluginRegistry.get(PluginType.KNOWLEDGE_SOURCE, source_type)

    if not plugin:
        # Provide helpful error message with available plugins
        available = PluginRegistry.list_available(PluginType.KNOWLEDGE_SOURCE)
        available_sources = available.get(PluginType.KNOWLEDGE_SOURCE.value, [])
        raise ClientException(
            f"Unknown knowledge source type: '{source_type}'. "
            f"Available plugins: {', '.join(available_sources)}"
        )

    # Ensure it's a KnowledgeSourcePlugin
    if not isinstance(plugin, KnowledgeSourcePlugin):
        raise ClientException(
            f"Plugin '{source_type}' is not a valid KnowledgeSourcePlugin"
        )

    # Create processor using the plugin
    processor = await plugin.create_processor(source, collection_config, store)

    # Sync using the processor
    await Synchronizer(processor, store).sync(collection_id)


# TODO - complete naming change (Collection -> Knowledge Source, Document - Chunk(?))
class KnowledgeSourcesController(Controller):
    @get()
    async def list_collections(self) -> list[dict[str, Any]]:
        """List all collections"""
        return await store.list_collections()

    @post()
    async def create_collection(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new collection"""
        data["created"] = utc_now()
        inserted_id = await store.create_collection(data)

        return {"inserted_id": inserted_id}

    @get("/{collection_id:str}")
    async def get_collection(self, collection_id: str) -> dict[str, Any]:
        """Get collection metadata"""
        try:
            return await store.get_collection_metadata(collection_id)
        except LookupError:
            raise NotFoundException("Collection doesn't exist")

    @patch("/{collection_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def update_collection(self, collection_id: str, data: dict[str, Any]) -> None:
        """Update collection metadata"""
        await store.update_collection_metadata(
            collection_id=collection_id, metadata=data
        )

    @put("/{collection_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def replace_collection(
        self, collection_id: str, data: dict[str, Any]
    ) -> None:
        """Replace collection metadata"""
        await store.replace_collection_metadata(
            collection_id=collection_id, metadata=data
        )

    @delete("/{collection_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def delete_collection(self, collection_id: str) -> None:
        """Delete a collection"""
        await store.delete_collection(collection_id)

    @post("/{collection_id:str}/sync", status_code=HTTP_204_NO_CONTENT)
    @observe(name="Syncing knowledge source", channel="production")
    async def sync_collection(self, collection_id: str) -> None:
        """Sync collection from source"""
        await sync_collection_standalone(collection_id)


class KnowledgeSourceMetadataController(Controller):
    path = "/{collection_id:str}/metadata"

    @post("/automap")
    async def automap(
        self, collection_id: str, data: MetadataAutomapRequest
    ) -> MetadataAutomapResponse:
        return MetadataAutomapResponse(
            root=await automap_metadata(collection_id, data.exclude_fields)
        )


class KnowledgeSourceChunksController(Controller):
    path = "/{collection_id:str}/documents"

    @get()
    async def list_documents(self, collection_id: str) -> list[dict[str, Any]]:
        """List documents in collection"""
        collection_id = await self._validate_collection_id(collection_id)

        return await store.list_documents(collection_id)

    @post(
        "/paginate/offset",
        status_code=HTTP_200_OK,
    )
    async def offset_pagination(
        self,
        collection_id: str,
        data: OffsetPaginationRequest,
    ) -> dict[str, Any]:
        return await store.list_document_with_offset(
            collection_id=collection_id, data=data
        )

    @post()
    async def create_document(
        self, collection_id: str, data: DocumentData
    ) -> dict[str, str]:
        """Create a document in collection"""
        collection_id = await self._validate_collection_id(collection_id)
        created_id = await store.create_document(data, collection_id)

        return {"created_id": created_id}

    @post("/bulk")
    async def create_documents_bulk(
        self,
        collection_id: str,
        data: list[DocumentData],
    ) -> dict[str, list[str]]:
        """Create multiple documents in collection"""
        collection_id = await self._validate_collection_id(collection_id)
        created_ids = await store.create_documents(data, collection_id)

        return {"created_ids": created_ids}

    @get("/{document_id:str}")
    async def get_document(
        self, collection_id: str, document_id: str
    ) -> dict[str, Any]:
        """Get a document from collection"""
        collection_id = await self._validate_collection_id(collection_id)
        try:
            return await store.get_document(
                document_id=document_id,
                collection_id=collection_id,
            )
        except LookupError:
            raise NotFoundException("Document doesn't exist")

    @patch("/{document_id:str}")
    async def update_document(
        self,
        collection_id: str,
        document_id: str,
        data: dict[str, Any],
    ) -> None:
        """Update a document in collection"""
        collection_id = await self._validate_collection_id(collection_id)
        await store.update_document(
            document_id=document_id,
            data=data,
            collection_id=collection_id,
        )

    @put("/{document_id:str}")
    async def replace_document(
        self,
        collection_id: str,
        document_id: str,
        data: dict[str, Any],
    ) -> None:
        """Replace a document in collection"""
        collection_id = await self._validate_collection_id(collection_id)
        document = DocumentData(**data)
        await store.replace_document(
            document_id=document_id,
            data=document,
            collection_id=collection_id,
        )

    @delete("/{document_id:str}")
    async def delete_document(self, collection_id: str, document_id: str) -> None:
        """Delete a document from collection"""
        collection_id = await self._validate_collection_id(collection_id)
        await store.delete_document(
            document_id=document_id, collection_id=collection_id
        )

    @delete("/all")
    async def delete_all_documents(self, collection_id: str) -> None:
        """Delete all documents from collection"""
        collection_id = await self._validate_collection_id(collection_id)
        await store.delete_all_documents(collection_id=collection_id)

    async def _validate_collection_id(self, collection_id: str) -> str:
        """Validate collection ID and return normalized ID"""
        try:
            validate_id(collection_id)
        except (errors.InvalidId, TypeError):
            collection_id = await get_ids_by_system_names(collection_id, "collections")  # type: ignore TODO - REFACTOR

            if not collection_id:
                raise ClientException("Collection doesn't exist after alternate lookup")

        try:
            await store.get_collection_metadata(collection_id)
        except LookupError:
            raise ClientException("Collection doesn't exist")

        return collection_id


knowledge_sources_router = Router(
    path="/collections",
    tags=["knowledge_sources_deprecated"],
    route_handlers=[
        KnowledgeSourcesController,
        KnowledgeSourceMetadataController,
        KnowledgeSourceChunksController,
    ],
)


knowledge_sources_router_deprecated = Router(
    path="/knowledge_sources",
    tags=["knowledge_sources"],
    route_handlers=[
        KnowledgeSourcesController,
        KnowledgeSourceMetadataController,
        KnowledgeSourceChunksController,
    ],
)
