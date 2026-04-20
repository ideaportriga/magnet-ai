from __future__ import annotations

import os
from typing import Any

import aiofiles
import aiofiles.os
from bson import errors
from litestar import Controller, Router, delete, get, patch, post, put
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
import structlog

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
from services.knowledge_sources.security import PROVIDER_ONLY_FIELDS
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
from services.file_cleanup import KS_UPLOAD_DIR

from sqlalchemy.ext.asyncio import AsyncSession

from storage import FileLimits, StorageService

store = get_db_store()

DOCUMENT_COLLECTION_PREFIX = "documents_"


async def _preserve_file_ids(
    collection_id: str, data: dict[str, Any]
) -> dict[str, Any]:
    """Merge file_id/storage_path from existing metadata into incoming data.

    The frontend sends ``uploaded_files`` with only ``filename`` keys.  This
    helper re-attaches ``file_id`` or ``storage_path`` from the current DB
    state so they are not lost on save.
    """
    incoming_source = data.get("source")
    if not isinstance(incoming_source, dict):
        return data

    incoming_files = incoming_source.get("uploaded_files")
    if not incoming_files:
        return data

    try:
        existing = await store.get_collection_metadata(collection_id)
    except LookupError:
        return data

    existing_source = existing.get("source", {})
    if not isinstance(existing_source, dict):
        return data

    existing_files = existing_source.get("uploaded_files", [])
    lookup = {f["filename"]: f for f in existing_files if "filename" in f}

    merged = []
    for f in incoming_files:
        name = f.get("filename", "")
        existing_entry = lookup.get(name, {})
        entry = {**existing_entry, **f}
        merged.append(entry)

    incoming_source["uploaded_files"] = merged
    data["source"] = incoming_source
    return data


def _inject_storage_into_store(store_obj: Any) -> None:
    """Attach StorageService and a shared db_session to the DocumentStore so plugins can use it."""
    if getattr(store_obj, "storage_service", None) is not None:
        return
    try:
        from storage import StorageService

        store_obj.storage_service = StorageService()
    except Exception:
        pass

    if getattr(store_obj, "storage_db_session", None) is None:
        try:
            from core.config.base import get_settings
            from sqlalchemy.ext.asyncio import AsyncSession as _AS

            settings = get_settings()
            store_obj.storage_db_session = _AS(
                settings.db.get_engine(), expire_on_commit=False
            )
        except Exception:
            pass


async def _claim_temp_files(
    collection_id: str,
    data: dict[str, Any],
    storage_service: StorageService,
    db_session: AsyncSession,
) -> None:
    """Reassign temp-uploaded files (entity_type='ks_source_temp') to this collection.

    When a file is uploaded before the KS exists, it is stored with
    entity_type='ks_source_temp'.  Once the KS is created we update the
    entity_type to 'ks_source' and set entity_id to the new collection UUID so
    the file is properly managed (quota, enrichment, cleanup).
    """
    from uuid import UUID as _UUID

    uploaded_files = data.get("source", {}).get("uploaded_files", [])
    file_ids = [uf["file_id"] for uf in uploaded_files if "file_id" in uf]
    if not file_ids:
        return

    try:
        entity_id = _UUID(str(collection_id))
    except ValueError:
        return

    for fid in file_ids:
        try:
            stored = await storage_service.get(db_session, _UUID(fid))
            if stored and stored.entity_type == "ks_source_temp":
                stored.entity_type = "ks_source"
                stored.entity_id = entity_id
                db_session.add(stored)
        except Exception:
            pass

    await db_session.flush()


async def _enrich_uploaded_files(
    collection_id: str,
    source_config: dict[str, Any],
    db_session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Enrich uploaded_files in source_config from stored_files DB table.

    The stored_files table is the source of truth for files managed by
    StorageService.  Metadata ``uploaded_files`` may be stale (frontend can
    overwrite it), so we rebuild the list from the DB.
    """
    try:
        from sqlalchemy import select
        from storage.models import StoredFile
        from uuid import UUID as _UUID

        try:
            entity_id = _UUID(collection_id)
        except ValueError:
            return source_config

        # Use provided session or create a temporary one
        if db_session:
            session_to_use = db_session
            stmt = select(StoredFile).where(
                StoredFile.entity_type == "ks_source",
                StoredFile.entity_id == entity_id,
                StoredFile.deleted_at.is_(None),
            )
            result = await session_to_use.execute(stmt)
            stored = list(result.scalars().all())
        else:
            from core.config.base import get_settings
            from sqlalchemy.ext.asyncio import AsyncSession as _AS

            settings = get_settings()
            engine = settings.db.get_engine()
            async with _AS(engine, expire_on_commit=False) as tmp_session:
                stmt = select(StoredFile).where(
                    StoredFile.entity_type == "ks_source",
                    StoredFile.entity_id == entity_id,
                    StoredFile.deleted_at.is_(None),
                )
                result = await tmp_session.execute(stmt)
                stored = list(result.scalars().all())

        if not stored:
            return source_config

        db_files = [{"filename": sf.filename, "file_id": str(sf.id)} for sf in stored]

        existing = source_config.get("uploaded_files", [])
        legacy = [f for f in existing if "storage_path" in f]

        source_config["uploaded_files"] = db_files + legacy

        logger.info(
            "Enriched uploaded_files from stored_files table",
            collection_id=collection_id,
            db_files=len(db_files),
            legacy_files=len(legacy),
        )
    except Exception:
        logger.exception(
            "Failed to enrich uploaded_files from DB",
            collection_id=collection_id,
        )

    return source_config


# Load all knowledge source plugins on module import
PluginRegistry.auto_load()

logger = structlog.get_logger(__name__)


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

    logger.info(
        "Starting collection sync",
        collection_id=collection_id,
        collection_name=collection_config.get("name"),
        source_type=source_type,
        provider_system_name=provider_system_name,
        has_provider=bool(provider_system_name),
    )

    # Get provider configuration if provider is linked
    provider_config = {}
    if provider_system_name:
        try:
            provider_config = await get_provider_config(provider_system_name)
            logger.info(
                "Retrieved provider configuration",
                collection_id=collection_id,
                provider_system_name=provider_system_name,
                has_endpoint=bool(provider_config.get("endpoint")),
                endpoint_value=provider_config.get("endpoint", "None"),
            )
        except ValueError as e:
            logger.error(
                "Failed to load provider configuration",
                collection_id=collection_id,
                provider_system_name=provider_system_name,
                error=str(e),
            )
            raise ClientException(f"Failed to load provider configuration: {e}")
    else:
        logger.warning(
            "No provider linked to collection",
            collection_id=collection_id,
            message="Collection has no provider_system_name set. Endpoint and credentials must be in source config.",
        )

    # Merge provider config with source config
    # Provider config values for security-critical fields are NEVER overridden
    # Other source config values can override provider values if they are truthy
    merged_source_config = {**provider_config}
    for key, value in source.items():
        # Skip security-critical fields - they must only come from provider
        if key in PROVIDER_ONLY_FIELDS:
            logger.warning(
                "Ignoring security-critical field from source config",
                collection_id=collection_id,
                field=key,
                reason="Security-critical fields can only be set via provider configuration",
            )
            continue

        # For non-security fields, only override if value is truthy or key doesn't exist in provider
        if value or key not in provider_config:
            merged_source_config[key] = value

    logger.debug(
        "Merged configuration",
        collection_id=collection_id,
        source_type=source_type,
        has_endpoint=bool(merged_source_config.get("endpoint")),
        endpoint_from_provider=bool(provider_config.get("endpoint")),
        endpoint_in_source=bool(source.get("endpoint")),
    )

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

    # Inject StorageService + shared db_session into store so plugins can access it
    _inject_storage_into_store(store)

    # Enrich uploaded_files from stored_files table (source of truth).
    # Frontend may lose file_id from metadata, but the DB always has it.
    merged_source_config = await _enrich_uploaded_files(
        collection_id,
        merged_source_config,
        db_session=getattr(store, "storage_db_session", None),
    )

    # Create processor using the plugin with merged configuration
    processor = await plugin.create_processor(
        merged_source_config, collection_config, store
    )

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

        # Additional provider-level fields (beyond PROVIDER_ONLY_FIELDS) that are provider-specific
        # and should not appear in knowledge source form
        additional_provider_fields = {
            "search_api_url",  # Service-specific URLs
            "pdf_api_url",  # Service-specific URLs
            "base_slug",  # Service-specific configuration
        }

        # All provider fields combined (security-critical + provider-specific)
        all_provider_fields = PROVIDER_ONLY_FIELDS | additional_provider_fields

        def determine_component(
            field_name: str, field_type: str, field_schema: dict | None = None
        ) -> str:
            """Determine the Vue component type based on field characteristics"""
            # Allow plugins to specify a custom component via x-component
            if field_schema and field_schema.get("x-component"):
                return field_schema["x-component"]
            if field_type == "boolean":
                return "km-toggle"
            elif field_type == "array":
                return "km-input-list-add"
            elif (
                field_type == "object"
                or "config" in field_name
                or "filter" in field_name
            ):
                return "km-codemirror"
            else:
                return "km-input"

        def format_label(field_name: str) -> str:
            """Convert field_name to human-readable label"""
            # Remove common prefixes
            label = field_name
            for prefix in [
                "sharepoint_",
                "confluence_",
                "oracle_",
                "rightnow_",
                "fluid_topics_",
                "sharepoint_pages_",
            ]:
                if label.startswith(prefix):
                    label = label[len(prefix) :]
                    break

            # Convert snake_case to Title Case
            words = label.split("_")
            return " ".join(word.capitalize() for word in words)

        def transform_field(
            field_name: str,
            field_schema: dict,
            required: bool,
            is_provider_field: bool = False,
        ) -> dict:
            """Transform schema field to frontend format"""
            field_type = field_schema.get("type", "string")

            # Map JSON schema types to frontend types
            type_mapping = {
                "string": "String",
                "integer": "Number",
                "number": "Number",
                "boolean": "Boolean",
                "array": "Array",
                "object": "Object",
            }

            field_info = {
                "name": field_name,
                "label": format_label(field_name),
                "field": field_name,
                "component": determine_component(field_name, field_type, field_schema),
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
                # Skip fields marked as hidden (managed internally by other components)
                if field_schema.get("x-hidden"):
                    continue

                is_provider_field = field_name in all_provider_fields

                field_info = transform_field(
                    field_name,
                    field_schema,
                    field_name in required_fields,
                    is_provider_field,
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

        return result

    @post()
    async def create_collection(
        self,
        data: dict[str, Any],
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Create a new collection"""
        data["created"] = utc_now()
        inserted_id = await store.create_collection(data)

        # Reassign any temp-uploaded files to this collection
        if storage_service and db_session:
            await _claim_temp_files(inserted_id, data, storage_service, db_session)

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
        data = await _preserve_file_ids(collection_id, data)
        await store.update_collection_metadata(
            collection_id=collection_id, metadata=data
        )

    @put("/{collection_id:str}", status_code=HTTP_204_NO_CONTENT)
    async def replace_collection(
        self, collection_id: str, data: dict[str, Any]
    ) -> None:
        """Replace collection metadata"""
        data = await _preserve_file_ids(collection_id, data)
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


class KnowledgeSourceFileUploadController(Controller):
    """Handles file upload/delete for File-type knowledge sources."""

    path = "/{collection_id:str}/files"

    MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_FILE_SIZE_MB", "50"))

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
        ".epub",
        ".csv",
        ".html",
        ".htm",
        ".xml",
        ".txt",
        ".md",
        ".json",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
        ".eml",
        ".msg",
    }

    async def _get_collection_config(self, collection_id: str) -> dict[str, Any]:
        collection_id = await self._validate_collection_id(collection_id)
        return await store.get_collection_metadata(collection_id)

    async def _validate_collection_id(self, collection_id: str) -> str:
        try:
            validate_id(collection_id)
        except (errors.InvalidId, TypeError):
            collection_id = await get_ids_by_system_names(collection_id, "collections")  # type: ignore
            if not collection_id:
                raise ClientException("Collection doesn't exist after alternate lookup")
        try:
            await store.get_collection_metadata(collection_id)
        except LookupError:
            raise ClientException("Collection doesn't exist")
        return collection_id

    @post(status_code=HTTP_200_OK)
    async def upload_file(
        self,
        collection_id: str,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        storage_service: StorageService | None = None,
        file_limits: FileLimits | None = None,
        db_session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Upload a file for a File-type knowledge source."""
        collection_id = await self._validate_collection_id(collection_id)
        config = await store.get_collection_metadata(collection_id)

        filename = data.filename or "upload"
        file_bytes = await data.read()

        if not file_bytes:
            raise ClientException("Empty file")

        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(filename)

        # Validate file extension
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ClientException(
                f"Unsupported file extension '{ext}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # Validate file size
        if file_limits:
            file_limits.check_file_size(len(file_bytes), "ks_source")
        else:
            max_bytes = self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if len(file_bytes) > max_bytes:
                raise ClientException(
                    f"File exceeds maximum size of {self.MAX_UPLOAD_SIZE_MB} MB"
                )

        # Validate MIME type via magic bytes + extension/content match (§C.1)
        from kreuzberg import detect_mime_type

        from storage.mime_validation import validate_upload_mime

        detected_mime = detect_mime_type(file_bytes)
        if detected_mime == "application/octet-stream":
            logger.warning(
                "Could not detect MIME type from file content",
                filename=safe_filename,
                extension=ext,
            )
        validate_upload_mime(safe_filename, detected_mime)

        # Update source config with uploaded file reference
        source = config.get("source", {})
        if not isinstance(source, dict):
            source = {"source_type": source} if source else {}
        uploaded_files = source.get("uploaded_files", [])

        # Remove duplicate if same filename already exists
        uploaded_files = [
            uf for uf in uploaded_files if uf["filename"] != safe_filename
        ]

        # Store file via StorageService (primary) or legacy /tmp fallback
        if storage_service and db_session:
            if file_limits:
                from uuid import UUID as _UUID

                try:
                    entity_id = _UUID(collection_id)
                except ValueError:
                    from uuid_utils import uuid7

                    entity_id = uuid7()

                await file_limits.check_quota(
                    db_session,
                    storage_service,
                    "ks_source",
                    entity_id,
                    len(file_bytes),
                )
                stored_file = await storage_service.save_file(
                    db_session,
                    content=file_bytes,
                    filename=safe_filename,
                    content_type=detected_mime or "application/octet-stream",
                    entity_type="ks_source",
                    entity_id=entity_id,
                    backend_key=file_limits.backend_key_for("ks_source"),
                    sub_path=f"ks/{collection_id}",
                )
            else:
                from uuid_utils import uuid7

                stored_file = await storage_service.save_file(
                    db_session,
                    content=file_bytes,
                    filename=safe_filename,
                    content_type=detected_mime or "application/octet-stream",
                    entity_type="ks_source",
                    entity_id=uuid7(),
                    sub_path=f"ks/{collection_id}",
                )

            uploaded_files.append(
                {
                    "filename": safe_filename,
                    "file_id": str(stored_file.id),
                }
            )
        else:
            # Legacy fallback: write to /tmp
            collection_dir = os.path.join(KS_UPLOAD_DIR, collection_id)
            await aiofiles.os.makedirs(collection_dir, exist_ok=True)
            storage_path = os.path.join(collection_dir, safe_filename)

            async with aiofiles.open(storage_path, "wb") as f:
                await f.write(file_bytes)

            uploaded_files.append(
                {
                    "filename": safe_filename,
                    "storage_path": storage_path,
                }
            )

        source["uploaded_files"] = uploaded_files
        config["source"] = source
        await store.update_collection_metadata(
            collection_id=collection_id, metadata=config
        )

        logger.info(
            "File uploaded to knowledge source",
            collection_id=collection_id,
            filename=safe_filename,
            size=len(file_bytes),
        )

        return {
            "filename": safe_filename,
            "size": len(file_bytes),
        }

    @get(status_code=HTTP_200_OK)
    async def list_uploaded_files(self, collection_id: str) -> list[dict[str, str]]:
        """List uploaded files for a knowledge source."""
        collection_id = await self._validate_collection_id(collection_id)
        config = await store.get_collection_metadata(collection_id)
        source = config.get("source", {})
        if not isinstance(source, dict):
            return []
        return source.get("uploaded_files", [])

    @delete("/{filename:str}", status_code=HTTP_204_NO_CONTENT)
    async def delete_uploaded_file(
        self,
        collection_id: str,
        filename: str,
        storage_service: StorageService | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        """Delete an uploaded file from a knowledge source."""
        collection_id = await self._validate_collection_id(collection_id)
        config = await store.get_collection_metadata(collection_id)

        source = config.get("source", {})
        if not isinstance(source, dict):
            source = {"source_type": source} if source else {}
        uploaded_files = source.get("uploaded_files", [])

        # Sanitize filename
        safe_filename = os.path.basename(filename)

        target = next(
            (uf for uf in uploaded_files if uf["filename"] == safe_filename), None
        )
        if not target:
            raise NotFoundException(f"File '{safe_filename}' not found")

        # Delete file — StorageService (soft-delete) or legacy disk removal
        if "file_id" in target and storage_service and db_session:
            from uuid import UUID as _UUID

            stored_file = await storage_service.get(
                db_session, _UUID(target["file_id"])
            )
            if stored_file:
                await storage_service.delete_file(db_session, stored_file)
        elif "storage_path" in target:
            try:
                await aiofiles.os.remove(target["storage_path"])
            except FileNotFoundError:
                pass

        # Update config
        uploaded_files = [
            uf for uf in uploaded_files if uf["filename"] != safe_filename
        ]
        source["uploaded_files"] = uploaded_files
        config["source"] = source
        await store.update_collection_metadata(
            collection_id=collection_id, metadata=config
        )

        logger.info(
            "File deleted from knowledge source",
            collection_id=collection_id,
            filename=safe_filename,
        )


knowledge_sources_router = Router(
    path="/collections",
    tags=["[Deprecated] Knowledge Sources"],
    route_handlers=[
        KnowledgeSourcesController,
        KnowledgeSourceMetadataController,
        KnowledgeSourceChunksController,
        KnowledgeSourceFileUploadController,
    ],
)


knowledge_sources_router_deprecated = Router(
    path="/knowledge_sources",
    tags=["Admin / Knowledge Sources"],
    route_handlers=[
        KnowledgeSourcesController,
        KnowledgeSourceMetadataController,
        KnowledgeSourceChunksController,
        KnowledgeSourceFileUploadController,
    ],
)
