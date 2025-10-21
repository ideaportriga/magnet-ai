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
from services.knowledge_sources.factory import get_provider_config
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
    
    If collection has provider_system_name, retrieves provider configuration
    and merges it with source config.

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
    provider_system_name = collection_config.get("provider_system_name")

    # Get provider configuration if provider is linked
    provider_config = {}
    if provider_system_name:
        try:
            provider_config = await get_provider_config(provider_system_name)
        except ValueError as e:
            raise ClientException(f"Failed to load provider configuration: {e}")
    
    # Merge provider config with source config
    # Source config takes precedence over provider config
    # Plugins now use 'endpoint' field directly, no transformation needed
    merged_source_config = {**provider_config, **source}

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

    # Create processor using the plugin with merged configuration
    processor = await plugin.create_processor(merged_source_config, collection_config, store)

    # Sync using the processor
    await Synchronizer(processor, store).sync(collection_id)


# TODO - complete naming change (Collection -> Knowledge Source, Document - Chunk(?))
class KnowledgeSourcesController(Controller):
    @get()
    async def list_collections(self) -> list[dict[str, Any]]:
        """List all collections"""
        return await store.list_collections()
    
    @get("/plugins")
    async def list_plugins(self) -> dict[str, Any]:
        """Get available knowledge source plugins with their configuration schemas
        
        Returns:
            Dictionary with plugin information including:
            - name: Plugin display name
            - source_type: Unique identifier for the plugin
            - description: Plugin description
            - provider_fields: Fields that should be configured in the provider
            - source_fields: Fields that can be configured in the knowledge source
        """
        # Get all knowledge source plugins
        plugins = PluginRegistry.get_all(PluginType.KNOWLEDGE_SOURCE)
        
        # Provider-level credential fields that should not appear in collection form
        provider_credential_fields = {
            'client_id', 'client_secret', 'tenant', 'thumbprint', 'private_key',
            'username', 'password', 'token', 'security_token', 'api_token',
            'api_key', 'search_api_url', 'pdf_api_url', 'base_slug'
        }
        
        # Provider-level endpoint field (standardized as 'endpoint')
        # Plugins now use 'endpoint' directly in their config_schema
        provider_endpoint_field = 'endpoint'
        
        # All provider fields combined
        all_provider_fields = provider_credential_fields | {provider_endpoint_field}
        
        def determine_component(field_name: str, field_type: str) -> str:
            """Determine the Vue component type based on field characteristics"""
            if field_type == "boolean":
                return "km-toggle"
            elif field_type == "array":
                return "km-input-list-add"
            elif field_type == "object" or "config" in field_name or "filter" in field_name:
                return "km-codemirror"
            else:
                return "km-input"
        
        def format_label(field_name: str) -> str:
            """Convert field_name to human-readable label"""
            # Remove common prefixes
            label = field_name
            for prefix in ['sharepoint_', 'confluence_', 'oracle_', 'rightnow_', 'fluid_topics_', 'sharepoint_pages_']:
                if label.startswith(prefix):
                    label = label[len(prefix):]
                    break
            
            # Convert snake_case to Title Case
            words = label.split('_')
            return ' '.join(word.capitalize() for word in words)
        
        def transform_field(field_name: str, field_schema: dict, required: bool, is_provider_field: bool = False) -> dict:
            """Transform schema field to frontend format"""
            field_type = field_schema.get("type", "string")
            
            # Map JSON schema types to frontend types
            type_mapping = {
                "string": "String",
                "integer": "Number",
                "number": "Number",
                "boolean": "Boolean",
                "array": "Array",
                "object": "Object"
            }
            
            field_info = {
                "name": field_name,
                "label": format_label(field_name),
                "field": field_name,
                "component": determine_component(field_name, field_type),
                "type": type_mapping.get(field_type, "String"),
            }
            
            # Add description if available
            if field_schema.get("description"):
                field_info["description"] = field_schema["description"]
            
            # Add default value if present
            if "default" in field_schema:
                field_info["default"] = field_schema["default"]
            
            # Provider fields should not have readonly logic based on last_synced
            # Collection fields should be readonly after sync to prevent data inconsistency
            if is_provider_field:
                field_info["readonly"] = False
            else:
                field_info["readonly_after_sync"] = True
            
            # Mark if field is required
            field_info["required"] = required
            
            return field_info
        
        result = []
        for plugin_id, plugin in plugins.items():
            if not isinstance(plugin, KnowledgeSourcePlugin):
                continue
                
            metadata = plugin.metadata
            config_schema = metadata.config_schema or {}
            
            # Extract properties from schema
            properties = config_schema.get("properties", {})
            required_fields = config_schema.get("required", [])
            
            # Split fields into provider and source fields
            provider_fields = []
            source_fields = []
            
            for field_name, field_schema in properties.items():
                is_provider_field = field_name in all_provider_fields
                
                field_info = transform_field(
                    field_name, 
                    field_schema, 
                    field_name in required_fields,
                    is_provider_field
                )
                
                if is_provider_field:
                    provider_fields.append(field_info)
                else:
                    source_fields.append(field_info)
            
            plugin_info = {
                "name": metadata.name,
                "source_type": plugin.source_type,
                "description": metadata.description,
                "version": metadata.version,
                "author": metadata.author,
                "provider_fields": provider_fields,
                "source_fields": source_fields,
            }
            result.append(plugin_info)
        
        return {"plugins": result}

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
