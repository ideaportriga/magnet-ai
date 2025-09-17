from json import loads
from typing import Any

from bson import errors
from litestar import Controller, Router, delete, get, patch, post, put
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT

from data_sources.confluence.source import ConfluenceDataSource
from data_sources.confluence.utils import create_confluence_instance
from data_sources.file.source import UrlDataSource
from data_sources.fluid_topics.source import FluidTopicsDataSource
from data_sources.hubspot.source import HubspotDataSource
from data_sources.oracle_knowledge.source import OracleKnowledgeDataSource
from data_sources.oracle_knowledge.utils import create_oracle_knowledge_client
from data_sources.rightnow.source import RightNowDataSource
from data_sources.rightnow.utils import get_rightnow_basic_auth
from data_sources.salesforce.source import SalesforceDataSource
from data_sources.salesforce.utils import create_salesforce_instance
from data_sources.sharepoint.source_documents import SharePointDocumentsDataSource
from data_sources.sharepoint.source_pages import SharePointPagesDataSource
from data_sources.sharepoint.utils import create_sharepoint_client
from data_sync.processors.confluence_data_processor import ConfluenceDataProcessor
from data_sync.processors.file_data_processor import UrlDataProcessor
from data_sync.processors.fluidtopics_data_processor import FluidTopicsDataProcessor
from data_sync.processors.hubspot_data_processor import HubspotDataProcessor
from data_sync.processors.oracle_knowledge_processor import OracleKnowledgeDataProcessor
from data_sync.processors.rightnow_data_processor import RightNowDataProcessor
from data_sync.processors.salesforce_data_processor import SalesforceDataProcessor
from data_sync.processors.sharepoint.sharepoint_documents_data_processor import (
    SharepointDocumentsDataProcessor,
)
from data_sync.processors.sharepoint.sharepoint_pages_data_processor import (
    SharepointPagesDataProcessor,
)
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
from utils.common import CollectionSource
from utils.datetime_utils import utc_now

store = get_db_store()

DOCUMENT_COLLECTION_PREFIX = "documents_"


async def sync_collection_standalone(collection_id: str, **kwargs) -> None:
    """Standalone function to sync a collection without needing a controller instance.
    This allows the function to be called directly from other modules.

    Args:
        collection_id: The ID of the collection to sync

    """
    collection_config = await store.get_collection_metadata(collection_id)
    observability_context.update_current_trace(
        name=collection_config.get("name"), type=FeatureType.KNOWLEDGE_SOURCE.value
    )

    source = collection_config.get("source", {})
    source_type = source.get("source_type")

    match source_type:
        case CollectionSource.SHAREPOINT:
            sharepoint_site_url = source.get("sharepoint_site_url")

            if not sharepoint_site_url:
                raise ClientException("Missing `sharepoint_site_url` in metadata")

            client = create_sharepoint_client(sharepoint_site_url)

            folder: str | None = source.get("sharepoint_folder")
            recursive: bool = source.get("sharepoint_recursive", False)
            library: str | None = collection_config.get("sharepoint_library")
            folder: str | None = collection_config.get("sharepoint_folder")
            recursive: bool = collection_config.get("sharepoint_recursive", False)

            data_source = SharePointDocumentsDataSource(
                ctx=client,
                library=library,
                folder=folder,
                recursive=recursive,
            )

            await Synchronizer(
                SharepointDocumentsDataProcessor(data_source, collection_config),
                store,
            ).sync(collection_id)

            return

        case CollectionSource.SHAREPOINT_PAGES:
            sharepoint_site_url = source.get("sharepoint_site_url")

            if not sharepoint_site_url:
                raise ClientException("Missing `sharepoint_site_url` in metadata")

            client = create_sharepoint_client(sharepoint_site_url)

            page_name = source.get("sharepoint_pages_page_name")

            embed_title = source.get(
                "sharepoint_pages_embed_title",
                False,
            )

            data_source = SharePointPagesDataSource(client, page_name)

            await Synchronizer(
                SharepointPagesDataProcessor(
                    data_source, collection_config, embed_title
                ),
                store,
            ).sync(collection_id)

            return

        case CollectionSource.CONFLUENCE:
            confluence_url = source.get("confluence_url")
            confluence_space = source.get("confluence_space")

            if not confluence_url:
                raise ClientException("Missing `confluence_url` in metadata")
            if not confluence_space:
                raise ClientException("Missing `confluence_space` in metadata")

            data_source = ConfluenceDataSource(
                create_confluence_instance(confluence_url),
                confluence_space,
            )

            await Synchronizer(ConfluenceDataProcessor(data_source), store).sync(
                collection_id,
            )

        case CollectionSource.SALESFORCE:
            object_api_name = source.get("object_api_name")
            output_config_json = source.get("output_config")

            if not object_api_name:
                raise ClientException("Missing `object_api_name` in metadata")
            if not output_config_json:
                raise ClientException("Missing `output_config` in metadata")

            output_config = loads(output_config_json)
            salesforce = create_salesforce_instance()

            await Synchronizer(
                SalesforceDataProcessor(
                    SalesforceDataSource(salesforce, object_api_name, output_config),
                    output_config,
                ),
                store,
            ).sync(collection_id)

        case CollectionSource.RIGHTNOW:
            rightnow_url = source.get("rightnow_url")

            if not rightnow_url:
                raise ClientException("Missing `rightnow_url` in metadata")

            auth = get_rightnow_basic_auth()

            await Synchronizer(
                RightNowDataProcessor(RightNowDataSource(rightnow_url, auth)),
                store,
            ).sync(collection_id)

        case CollectionSource.ORACLEKNOWLEDGE:
            oracle_knowledge_url = source.get("oracle_knowledge_url")

            if not oracle_knowledge_url:
                raise ClientException("Missing `oracle_knowledge_url` in metadata")

            client = create_oracle_knowledge_client(oracle_knowledge_url)

            await Synchronizer(
                OracleKnowledgeDataProcessor(OracleKnowledgeDataSource(client)),
                store,
            ).sync(collection_id)

        case CollectionSource.FILE:
            file_url = source.get("file_url")
            if not file_url:
                raise ClientException("Missing `file_url` in metadata")
            data_source = UrlDataSource(file_url)
            await Synchronizer(
                UrlDataProcessor(data_source, collection_config), store
            ).sync(
                collection_id,
            )

        case CollectionSource.HUBSPOT:
            chunk_size = source.get("chunk_size")

            if chunk_size:
                data_source = HubspotDataSource(int(chunk_size))
            else:
                data_source = HubspotDataSource()

            await Synchronizer(HubspotDataProcessor(data_source), store).sync(
                collection_id
            )

        case CollectionSource.FLUID_TOPICS:
            filters = source.get("fluid_topics_search_filters")
            filters = loads(filters) if filters else []
            data_source = FluidTopicsDataSource(filters)
            await Synchronizer(
                FluidTopicsDataProcessor(data_source, collection_config),
                store,
            ).sync(collection_id)

        case _:
            raise ClientException("Sync is not supported for this collection")


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
