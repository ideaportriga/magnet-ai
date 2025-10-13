"""PostgreSQL store with pgvector support for document storage and search."""

import asyncio
import json
import logging
from decimal import Decimal
from typing import Any, override

from models import (
    ChunksByCollection,
    DocumentData,
    DocumentSearchResult,
    DocumentSearchResultItem,
    QueryChunksByCollectionBySource,
)
from open_ai.utils_new import get_embeddings
from openai_model.utils import get_model_by_system_name
from services.observability import observability_context, observe
from services.observability.models import SpanType
from stores.document_store import DocumentStore
from stores.pgvector_db.client import PgVectorClient
from stores.pgvector_db.metadata_filter_builder import PgVectorMetadataFilterBuilder
from type_defs.pagination import FilterObject, OffsetPaginationRequest
from validation.rag_tools import RetrieveConfig

logger = logging.getLogger(__name__)


class PgVectorStore(DocumentStore):
    """Document store implementation using PostgreSQL with pgvector extension."""

    COLLECTIONS_TABLE = "collections"
    DOCUMENTS_TABLE_PREFIX = "documents_"
    METADATA_FILTER_BUILDER = PgVectorMetadataFilterBuilder()

    def __init__(self, client: PgVectorClient):
        """Initialize the PgVector store.

        Args:
            client: PgVectorClient instance
        """
        self.client = client

    async def _ensure_tables_exist(self) -> None:
        """Ensure required tables exist - This assumes migrations have been run."""
        # Check if collections table exists with correct schema
        # If migrations are being used, this should not create the table
        # Only used for backward compatibility
        table_exists = await self.client.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """,
            self.COLLECTIONS_TABLE,
        )

        if not table_exists:
            # If table doesn't exist, assume migrations need to be run
            logger.warning(
                f"Table {self.COLLECTIONS_TABLE} does not exist. "
                "Please run database migrations first."
            )
            raise RuntimeError(
                f"Table {self.COLLECTIONS_TABLE} does not exist. "
                "Run migrations using: python manage_migrations.py upgrade"
            )

    def _get_documents_table_name(self, collection_id: str) -> str:
        """Get the documents table name for a collection."""
        return f"{self.DOCUMENTS_TABLE_PREFIX}{collection_id.replace('-', '_')}"

    async def _get_vector_size_from_model(self, model_system_name: str) -> int:
        """Get vector size from model configuration.
        
        Args:
            model_system_name: System name of the AI model
            
        Returns:
            Vector size (dimensions), defaults to 1536 if not configured
        """
        try:
            model_config = await get_model_by_system_name(model_system_name)
            configs = model_config.get("configs", {})
            if configs and isinstance(configs, dict):
                vector_size = configs.get("vector_size")
                if vector_size and isinstance(vector_size, int):
                    return vector_size
        except Exception as e:
            logger.warning(
                "Failed to get vector size from model %s: %s, using default 1536",
                model_system_name,
                e,
            )
        return 1536  # Default size for OpenAI ada-002

    async def _create_documents_table(self, collection_id: str, vector_size: int = 1536) -> None:
        """Create documents table for a collection.
        
        Args:
            collection_id: Collection ID
            vector_size: Size of the embedding vector (default 1536)
        """
        table_name = self._get_documents_table_name(collection_id)

        await self.client.execute_command(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                metadata JSONB,
                embedding vector({vector_size}),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create vector index for similarity search
        if vector_size <= 2000:
            # Use HNSW for vectors up to 2000 dimensions
            await self.client.execute_command(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding_cosine
                ON {table_name} USING hnsw (embedding vector_cosine_ops) 
                WITH (m = 16, ef_construction = 64)
            """)
        else:
            # Use IVFFlat for vectors > 2000 dimensions
            await self.client.execute_command(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding_ivfflat
                ON {table_name} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            logger.info(
                "Created IVFFlat index for collection %s with %d dimensions",
                collection_id,
                vector_size,
            )

        # Create GIN index for metadata
        await self.client.execute_command(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_metadata_gin
            ON {table_name} USING GIN (metadata)
        """)

        logger.info("Created documents table %s with indexes", table_name)

    async def _ensure_documents_table_exists(self, collection_id: str) -> None:
        """Ensure documents table exists for a collection."""
        table_name = self._get_documents_table_name(collection_id)

        # Check if table exists
        table_exists = await self.client.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """,
            table_name,
        )

        if not table_exists:
            logger.info("Documents table %s does not exist, creating it", table_name)
            # Get vector size from collection's model
            try:
                collection_metadata = await self.get_collection_metadata(collection_id)
                model_name = collection_metadata.get("ai_model")
                if model_name:
                    vector_size = await self._get_vector_size_from_model(model_name)
                else:
                    vector_size = 1536  # Default
            except Exception as e:
                logger.warning(
                    "Could not get model info for collection %s: %s, using default vector size",
                    collection_id,
                    e,
                )
                vector_size = 1536
            await self._create_documents_table(collection_id, vector_size)

    async def _drop_documents_table(self, collection_id: str) -> None:
        """Drop documents table for a collection."""
        table_name = self._get_documents_table_name(collection_id)
        await self.client.execute_command(f"DROP TABLE IF EXISTS {table_name}")
        logger.info("Dropped documents table %s", table_name)

    async def list_collections(self, query: dict | None = None) -> list[dict]:
        """List all collections."""
        await self._ensure_tables_exist()

        where_clause = ""
        params = []

        if query:
            # For the new schema, we need to search in the individual JSON fields
            conditions = []
            param_count = 0
            for key, value in query.items():
                if key in ["source", "chunking", "indexing"]:
                    param_count += 1
                    conditions.append(f"{key} @> ${param_count}")
                    params.append(
                        json.dumps(
                            {key: value}
                            if isinstance(value, (str, int, bool))
                            else value
                        )
                    )
                else:
                    param_count += 1
                    conditions.append(f"{key} = ${param_count}")
                    params.append(value)

            if conditions:
                where_clause = f"WHERE {' AND '.join(conditions)}"

        sql = f"""
            SELECT 
                id::text,
                name,
                description,
                system_name,
                category,
                type,
                ai_model,
                source,
                chunking,
                indexing,
                last_synced,
                created_at,
                updated_at,
                created_by,
                updated_by
            FROM {self.COLLECTIONS_TABLE} 
            {where_clause}
            ORDER BY created_at DESC
        """

        rows = await self.client.execute_query(sql, *params)

        result = []
        for row in rows:
            collection_metadata = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "system_name": row["system_name"],
                "category": row["category"],
                "type": row["type"],
                "ai_model": row["ai_model"],
                "source": row["source"] or {},
                "chunking": row["chunking"] or {},
                "indexing": row["indexing"] or {},
                "last_synced": row["last_synced"].isoformat()
                if row["last_synced"]
                else None,
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
                "updated_at": row["updated_at"].isoformat()
                if row["updated_at"]
                else None,
                "created_by": row["created_by"],
                "updated_by": row["updated_by"],
            }
            result.append(collection_metadata)

        return result

    async def create_collection(self, metadata: dict) -> str:
        """Create a new collection."""
        logger.info("Creating collection")

        if metadata.get("indexing", {}).get("fulltext_search_supported"):
            logger.warning(
                "Fulltext search support noted but not implemented in pgvector"
            )

        await self._ensure_tables_exist()

        # Insert collection metadata using the new schema
        from datetime import datetime, timezone

        collection_id = await self.client.fetchval(
            f"""
            INSERT INTO {self.COLLECTIONS_TABLE} (
                name,
                description,
                system_name,
                category,
                type,
                ai_model,
                source,
                chunking,
                indexing,
                last_synced,
                created_at,
                updated_at,
                created_by,
                updated_by
            ) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) 
            RETURNING id::text
        """,
            metadata.get("name", ""),
            metadata.get("description"),
            metadata.get("system_name", ""),
            metadata.get("category"),
            metadata.get("type"),
            metadata.get("ai_model"),
            json.dumps(metadata.get("source", {})) if metadata.get("source") else None,
            json.dumps(metadata.get("chunking", {}))
            if metadata.get("chunking")
            else None,
            json.dumps(metadata.get("indexing", {}))
            if metadata.get("indexing")
            else None,
            (
                datetime.fromisoformat(metadata["last_synced"].replace("Z", "+00:00"))
                if metadata.get("last_synced")
                and isinstance(metadata.get("last_synced"), str)
                else None
            ),
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
            metadata.get("created_by"),
            metadata.get("updated_by"),
        )

        logger.info("Collection metadata inserted, id: %s", collection_id)

        # Create documents table for this collection
        await self._create_documents_table(collection_id)

        logger.info("Collection created completely, id: '%s'", collection_id)
        return collection_id

    async def get_collection_metadata(self, collection_id: str) -> dict:
        """Get collection metadata."""
        row = await self.client.fetchrow(
            f"""
            SELECT 
                id::text,
                name,
                description,
                system_name,
                category,
                type,
                ai_model,
                source,
                chunking,
                indexing,
                last_synced,
                created_at,
                updated_at,
                created_by,
                updated_by
            FROM {self.COLLECTIONS_TABLE} 
            WHERE id = $1
        """,
            collection_id,
        )

        if not row:
            raise LookupError("Collection does not exist")

        # Convert row to metadata dictionary
        metadata = {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "system_name": row["system_name"],
            "category": row["category"],
            "type": row["type"],
            "ai_model": row["ai_model"],
            "source": row["source"] or {},
            "chunking": row["chunking"] or {},
            "indexing": row["indexing"] or {},
            "last_synced": row["last_synced"].isoformat()
            if row["last_synced"]
            else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "created_by": row["created_by"],
            "updated_by": row["updated_by"],
        }
        metadata["id"] = collection_id
        return metadata

    async def update_collection_metadata(self, collection_id: str, metadata: dict):
        """Update collection metadata."""
        # Build dynamic update query based on provided metadata fields
        update_fields = []
        params = []
        param_idx = 1

        # Handle individual fields
        for field, value in metadata.items():
            if field in [
                "name",
                "description",
                "system_name",
                "category",
                "type",
                "ai_model",
                "created_by",
                "updated_by",
            ]:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(value)
                param_idx += 1
            elif field in ["source", "chunking", "indexing"]:
                update_fields.append(f"{field} = ${param_idx}")
                params.append(json.dumps(value) if value else None)
                param_idx += 1
            elif field == "last_synced":
                update_fields.append(f"last_synced = ${param_idx}")
                if value:
                    if isinstance(value, str):
                        from datetime import datetime

                        params.append(
                            datetime.fromisoformat(value.replace("Z", "+00:00"))
                        )
                    else:
                        params.append(value)
                else:
                    params.append(None)
                param_idx += 1

        # Always update the updated_at field
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        if not update_fields:
            logger.warning("No valid fields to update in collection metadata")
            return

        params.append(collection_id)

        result = await self.client.execute_command(
            f"""
            UPDATE {self.COLLECTIONS_TABLE} 
            SET {", ".join(update_fields)}
            WHERE id = ${param_idx}
        """,
            *params,
        )

        if result == "UPDATE 0":
            raise LookupError("Nothing was updated")

        logger.info("Updated metadata for collection '%s'", collection_id)

    async def replace_collection_metadata(self, collection_id: str, metadata: dict):
        """Replace collection metadata."""
        from datetime import datetime

        result = await self.client.execute_command(
            f"""
            UPDATE {self.COLLECTIONS_TABLE} 
            SET 
                name = $1,
                description = $2,
                system_name = $3,
                category = $4,
                type = $5,
                ai_model = $6,
                source = $7,
                chunking = $8,
                indexing = $9,
                last_synced = $10,
                updated_at = CURRENT_TIMESTAMP,
                created_by = $11,
                updated_by = $12
            WHERE id = $13
        """,
            metadata.get("name", ""),
            metadata.get("description"),
            metadata.get("system_name", ""),
            metadata.get("category"),
            metadata.get("type"),
            metadata.get("ai_model"),
            json.dumps(metadata.get("source", {})) if metadata.get("source") else None,
            json.dumps(metadata.get("chunking", {}))
            if metadata.get("chunking")
            else None,
            json.dumps(metadata.get("indexing", {}))
            if metadata.get("indexing")
            else None,
            (
                datetime.fromisoformat(metadata["last_synced"].replace("Z", "+00:00"))
                if metadata.get("last_synced")
                and isinstance(metadata.get("last_synced"), str)
                else None
            ),
            metadata.get("created_by"),
            metadata.get("updated_by"),
            collection_id,
        )

        if result == "UPDATE 0":
            raise LookupError("Nothing was replaced")

        logger.info("Replaced metadata for collection '%s'", collection_id)

    async def delete_collection(self, collection_id: str):
        """Delete a collection and all its documents."""
        # Delete collection metadata
        result = await self.client.execute_command(
            f"""
            DELETE FROM {self.COLLECTIONS_TABLE} WHERE id = $1
        """,
            collection_id,
        )

        if result == "DELETE 0":
            raise LookupError("Nothing was deleted")

        logger.info("Collection '%s' metadata deleted", collection_id)

        # Drop documents table
        await self._drop_documents_table(collection_id)

        logger.info("Collection '%s' deleted with all documents", collection_id)

    async def list_documents(
        self,
        collection_id: str,
        query: dict | None = None,
    ) -> list[dict]:
        """List documents in a collection."""
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before querying
        await self._ensure_documents_table_exists(collection_id)

        where_clause = ""
        params = []

        if query:
            where_clause = "WHERE metadata @> $1"
            params.append(json.dumps(query))

        sql = f"""
            SELECT id::text, content, metadata, created_at, updated_at
            FROM {table_name} 
            {where_clause}
            ORDER BY created_at DESC
        """

        rows = await self.client.execute_query(sql, *params)

        result = []
        for row in rows:
            document = {
                "id": row["id"],
                "content": row["content"],
                "metadata": row["metadata"] if row["metadata"] else {},
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
                "updated_at": row["updated_at"].isoformat()
                if row["updated_at"]
                else None,
            }
            result.append(document)

        return result

    async def list_document_with_offset(
        self,
        collection_id: str,
        data: OffsetPaginationRequest,
    ) -> dict[str, Any]:
        """List documents with offset pagination."""
        logger.info(
            "Listing documents with offset pagination for collection '%s'",
            collection_id,
        )

        if not collection_id:
            return {"documents": [], "pagination": {}}

        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before querying
        await self._ensure_documents_table_exists(collection_id)

        # Count total documents
        total_count = await self.client.fetchval(f"""
            SELECT COUNT(*) FROM {table_name}
        """)

        # Get paginated documents
        offset = data.offset or 0
        limit = data.limit or 10

        rows = await self.client.execute_query(
            f"""
            SELECT id::text, content, metadata, created_at, updated_at
            FROM {table_name}
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """,
            limit,
            offset,
        )

        documents = []
        for row in rows:
            document = {
                "id": row["id"],
                "content": row["content"],
                "metadata": row["metadata"] if row["metadata"] else {},
                "created_at": row["created_at"].isoformat()
                if row["created_at"]
                else None,
                "updated_at": row["updated_at"].isoformat()
                if row["updated_at"]
                else None,
            }
            documents.append(document)

        return {
            "items": documents,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }

    async def _get_embedding(
        self,
        collection_id: str,
        text: str,
        **kwargs,
    ):
        """Get embedding for text using the collection's model."""
        collection_metadata = await self.get_collection_metadata(collection_id)
        model_name = collection_metadata.get("ai_model")
        if not model_name:
            raise ValueError(f"No model specified for collection {collection_id}")
        embeddings = await get_embeddings(
            text=text,
            model_system_name=model_name,
            **kwargs,
        )
        return embeddings

    async def _get_embedding_by_model(
        self,
        model_system_name: str,
        text: str,
        **kwargs,
    ):
        """Get embedding for text using a specific model."""
        embeddings = await get_embeddings(
            text=text,
            model_system_name=model_system_name,
            **kwargs,
        )
        return embeddings

    async def create_document(self, document: DocumentData, collection_id: str) -> str:
        """Create a single document."""
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before creating a document
        await self._ensure_documents_table_exists(collection_id)

        # Get embedding for the content
        embedding = await self._get_embedding(collection_id, document.content)

        # Insert document
        document_id = await self.client.fetchval(
            f"""
            INSERT INTO {table_name} (content, metadata, embedding)
            VALUES ($1, $2, $3)
            RETURNING id::text
        """,
            document.content,
            document.metadata,
            embedding,
        )

        logger.info("Created document in collection '%s'", collection_id)
        return document_id

    async def create_documents(
        self,
        documents: list[DocumentData],
        collection_id: str,
    ) -> list[str]:
        """Create multiple documents."""
        if not documents:
            logger.info("No documents to create for collection '%s'", collection_id)
            return []

        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before creating documents
        await self._ensure_documents_table_exists(collection_id)

        # Pre-fetch collection metadata once to avoid multiple DB calls
        collection_metadata = await self.get_collection_metadata(collection_id)
        model_name = collection_metadata.get("ai_model")
        if not model_name:
            raise ValueError(f"No model specified for collection {collection_id}")

        # Get embeddings for all documents with reduced concurrency
        # Process in smaller batches to avoid overwhelming the connection pool
        batch_size = 10  # Process 10 embeddings at a time
        embeddings = []

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_tasks = [
                self._get_embedding_by_model(model_name, doc.content)
                for doc in batch_docs
            ]
            batch_embeddings = await asyncio.gather(*batch_tasks)
            embeddings.extend(batch_embeddings)

        # Use executemany approach by inserting documents one by one in a transaction
        # This avoids the asyncpg parameter type confusion with bulk operations
        inserted_ids = []

        # Ensure pool is initialized
        await self.client._ensure_pool_initialized()
        if not self.client.pool:
            raise RuntimeError("Connection pool is not initialized")

        # Use a transaction to ensure all inserts succeed or all fail
        async with self.client.pool.acquire() as connection:
            async with connection.transaction():
                for doc, embedding in zip(documents, embeddings):
                    document_id = await connection.fetchval(
                        f"""
                        INSERT INTO {table_name} (content, metadata, embedding)
                        VALUES ($1, $2, $3)
                        RETURNING id::text
                    """,
                        doc.content,
                        doc.metadata,
                        embedding,
                    )
                    inserted_ids.append(document_id)

        logger.info(
            "Created %s documents in collection '%s'",
            len(inserted_ids),
            collection_id,
        )

        return inserted_ids

    async def get_document(self, document_id: str, collection_id: str) -> dict:
        """Get a single document."""
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before querying
        await self._ensure_documents_table_exists(collection_id)

        row = await self.client.fetchrow(
            f"""
            SELECT id::text, content, metadata, created_at, updated_at
            FROM {table_name}
            WHERE id = $1
        """,
            document_id,
        )

        if not row:
            raise LookupError("Not found")

        return {
            "id": row["id"],
            "content": row["content"],
            "metadata": row["metadata"] if row["metadata"] else {},
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }

    async def update_document(self, document_id: str, data: dict, collection_id: str):
        """Update a document."""
        logger.info(
            "Updating document %s in collection '%s'",
            document_id,
            collection_id,
        )

        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before updating a document
        await self._ensure_documents_table_exists(collection_id)

        data.pop("collection_id", "")

        update_fields = []
        params = []
        param_idx = 1

        if "content" in data:
            update_fields.append(f"content = ${param_idx}")
            params.append(data["content"])
            param_idx += 1

            # Update embedding if content changed
            embedding = await self._get_embedding(collection_id, data["content"])
            update_fields.append(f"embedding = ${param_idx}")
            params.append(embedding)
            param_idx += 1

            logger.info("Re-creating embedding for document %s update", document_id)

        if "metadata" in data:
            update_fields.append(f"metadata = ${param_idx}")
            params.append(json.dumps(data["metadata"]))
            param_idx += 1

        if not update_fields:
            logger.warning("No valid fields to update")
            return

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(document_id)

        sql = f"""
            UPDATE {table_name} 
            SET {", ".join(update_fields)}
            WHERE id = ${param_idx}
        """

        result = await self.client.execute_command(sql, *params)

        if result == "UPDATE 0":
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
        """Replace a document completely."""
        logger.info(
            "Replacing document %s in collection '%s'",
            document_id,
            collection_id,
        )

        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before replacing a document
        await self._ensure_documents_table_exists(collection_id)

        # Get embedding for new content
        embedding = await self._get_embedding(collection_id, data.content)

        result = await self.client.execute_command(
            f"""
            UPDATE {table_name}
            SET content = $1, metadata = $2, embedding = $3, updated_at = CURRENT_TIMESTAMP
            WHERE id = $4
        """,
            data.content,
            data.metadata,
            embedding,
            document_id,
        )

        if result == "UPDATE 0":
            raise LookupError("Nothing was replaced")

        logger.info(
            "Replaced document %s in collection '%s'",
            document_id,
            collection_id,
        )

    async def delete_document(self, document_id: str, collection_id: str):
        """Delete a single document."""
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before deleting a document
        await self._ensure_documents_table_exists(collection_id)

        result = await self.client.execute_command(
            f"""
            DELETE FROM {table_name} WHERE id = $1
        """,
            document_id,
        )

        if result == "DELETE 0":
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
        """Delete multiple documents or all documents if no IDs provided."""
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before deleting documents
        await self._ensure_documents_table_exists(collection_id)

        if document_ids:
            # Delete specific documents
            result = await self.client.execute_command(
                f"""
                DELETE FROM {table_name} WHERE id = ANY($1)
            """,
                document_ids,
            )

            deleted_count = (
                int(result.split()[-1]) if result.startswith("DELETE") else 0
            )

            if deleted_count < len(document_ids):
                logger.warning(
                    "Deleted %s documents in collection '%s', requested to delete: %s",
                    deleted_count,
                    collection_id,
                    len(document_ids),
                )
        else:
            # Delete all documents
            result = await self.client.execute_command(f"""
                DELETE FROM {table_name}
            """)

            deleted_count = (
                int(result.split()[-1]) if result.startswith("DELETE") else 0
            )

        logger.info(
            "Deleted documents in collection '%s': %s",
            collection_id,
            deleted_count,
        )

    async def delete_all_documents(self, collection_id: str):
        """Delete all documents in a collection."""
        logger.info("Deleting all documents in collection '%s'", collection_id)
        await self.delete_documents(collection_id)

        # Update collection metadata
        await self.update_collection_metadata(collection_id, {"last_synced": None})

    async def document_collections_query_chunks_context(
        self,
        query: QueryChunksByCollectionBySource,
    ) -> ChunksByCollection:
        """Query chunks from multiple collections by source and chunk numbers."""

        async def query_collection(
            collection_id: str, source_query: dict
        ) -> list[dict]:
            table_name = self._get_documents_table_name(collection_id)

            # Ensure the documents table exists before querying
            await self._ensure_documents_table_exists(collection_id)

            # Build WHERE clause for OR conditions
            or_conditions = []
            params = []
            param_idx = 1

            for source_id, chunk_numbers in source_query.items():
                or_conditions.append(f"""
                    (metadata->>'sourceId' = ${param_idx} 
                     AND (metadata->>'chunkNumber')::int = ANY(${param_idx + 1}))
                """)
                params.extend([source_id, chunk_numbers])
                param_idx += 2

            if not or_conditions:
                return []

            sql = f"""
                SELECT id::text, content, metadata
                FROM {table_name}
                WHERE {" OR ".join(or_conditions)}
            """

            rows = await self.client.execute_query(sql, *params)

            result = []
            for row in rows:
                document = {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": row["metadata"] if row["metadata"] else {},
                }
                result.append(document)

            return result

        # Execute queries for all collections in parallel
        tasks = []
        collection_ids = []

        for collection_id, chunk_numbers_by_source_id in query.items():
            tasks.append(query_collection(collection_id, chunk_numbers_by_source_id))
            collection_ids.append(collection_id)

        results = await asyncio.gather(*tasks)

        # Build result dictionary
        result = {}
        for collection_id, collection_result in zip(collection_ids, results):
            result[collection_id] = collection_result

        return result

    async def _assert_collection_exist(self, collection_id: str) -> None:
        """Assert that a collection exists."""
        await self.get_collection_metadata(collection_id)

    @observe(
        name="Vector search",
        type=SpanType.SEARCH,
        capture_input=True,
        capture_output=True,
    )
    async def _vector_search(
        self,
        *,
        collection_id: str,
        query: str,
        vector: list[float],
        num_results: int,
        filter: FilterObject | None = None,
    ) -> DocumentSearchResult:
        """Perform vector similarity search."""
        logger.debug(
            f"Performing vector search in collection_id: {collection_id} with num_results: {num_results}",
        )

        await self._assert_collection_exist(collection_id)
        table_name = self._get_documents_table_name(collection_id)

        # Ensure the documents table exists before querying
        await self._ensure_documents_table_exists(collection_id)

        # Get collection metadata for filter building
        collection_metadata = await self.get_collection_metadata(collection_id)

        observability_context.update_current_span(
            description=f"Performing vector search in PostgreSQL with pgvector and taking only {num_results} first results.",
            extra_data={
                "table_name": table_name,
                "store": "pgvector",
            },
            input={
                "collection_id": collection_id,
                "collection_name": collection_metadata.get("name"),
                "query": query,
                "filter": filter.model_dump(exclude_none=True, by_alias=True)
                if filter
                else None,
                "num_results": num_results,
            },
        )

        # Build metadata filter condition
        metadata_filter = self.METADATA_FILTER_BUILDER.build(
            collection_metadata, filter
        )
        logger.debug(f"Metadata filter: {metadata_filter}")

        where_clause = "WHERE embedding IS NOT NULL"
        if metadata_filter:
            where_clause += f" AND ({metadata_filter})"

        # Perform cosine similarity search
        rows = await self.client.execute_query(
            f"""
            SELECT 
                id::text,
                content,
                metadata,
                1 - (embedding <=> $1) as similarity_score
            FROM {table_name}
            {where_clause}
            ORDER BY similarity_score DESC
            LIMIT $2
        """,
            vector,
            num_results,
        )

        result: DocumentSearchResult = []
        for row in rows:
            score = Decimal(str(row["similarity_score"]))
            content = row["content"]
            metadata = row["metadata"] if row["metadata"] else {}

            result.append(
                DocumentSearchResultItem(
                    id=row["id"],
                    score=score,
                    content=content,
                    collection_id=collection_id,
                    metadata=metadata,
                ),
            )
        logger.debug(
            f"Vector search found {len(result)} results in collection '{collection_id}'",
        )
        logger.debug(f"Vector search results: {result}")

        return result

    async def document_collection_similarity_search(
        self,
        collection_id: str,
        query: str,
        num_results: int,
        filter: FilterObject | None = None,
    ) -> DocumentSearchResult:
        """Perform similarity search on a single collection."""
        logger.debug(
            f"Performing similarity search on collection_id: {collection_id} with query: {query}",
        )

        vector = await self._get_embedding(collection_id, query)
        return await self._vector_search(
            collection_id=collection_id,
            query=query,
            vector=vector,
            num_results=num_results,
            filter=filter,
        )

    @override
    async def document_collections_similarity_search(
        self,
        collection_ids: list[str],
        retrieve_config: RetrieveConfig,
        query: str,
        num_results: int,
        filter: FilterObject | None = None,
    ) -> list:
        """Perform similarity search across multiple collections."""
        if not collection_ids:
            logger.warning("No collections provided for similarity search.")
            return []

        logger.debug(
            f"Performing similarity search on multiple collections: {collection_ids} with query: {query}",
        )

        # Get model for each collection
        collection_model_map = {}
        for cid in collection_ids:
            try:
                metadata = await self.get_collection_metadata(cid)
                collection_model_map[cid] = metadata.get("ai_model")
            except LookupError:
                logger.warning("Collection %s not found, skipping", cid)
                continue

        # Get unique models and create embedding cache
        unique_models = {
            model for model in collection_model_map.values() if model is not None
        }
        embedding_cache = {}

        async def _get_embedding(model_name: str):
            try:
                embedding = await self._get_embedding_by_model(model_name, query)
                return model_name, embedding
            except Exception as e:
                logger.error(
                    "Failed to get embedding for model %s: %s",
                    model_name,
                    e,
                    exc_info=True,
                )
                return model_name, None

        # Get embeddings for all unique models
        embedding_tasks = [_get_embedding(model) for model in unique_models]
        embedding_results = await asyncio.gather(*embedding_tasks)

        for model_name, embedding in embedding_results:
            embedding_cache[model_name] = embedding

        metadata_filtering_allowed = retrieve_config.allow_metadata_filter
        use_keyword_search = retrieve_config.use_keyword_search

        # Search in each collection
        async def _search_in_collection(cid: str):
            try:
                collection_config = await self.get_collection_metadata(cid)
                indexing = collection_config.get("indexing", {})
                semantic_search_needed = True
                keyword_search_needed = use_keyword_search and indexing.get(
                    "fulltext_search_supported"
                )

                semantic_search_task = asyncio.sleep(0)
                if semantic_search_needed:
                    model_name = collection_model_map[cid]
                    vector_for_collection = embedding_cache.get(model_name)

                    if vector_for_collection:
                        semantic_search_task = self._vector_search(
                            collection_id=cid,
                            query=query,
                            vector=vector_for_collection,
                            num_results=num_results,
                            filter=filter if metadata_filtering_allowed else None,
                        )
                    else:
                        logger.error(
                            f"Skipping collection {cid} due to missing embedding for model {model_name}"
                        )

                # Note: PgVector doesn't support full-text search like Oracle
                # For now, we only implement semantic search
                # If keyword search is needed, it would require additional implementation
                keyword_search_task = asyncio.sleep(0)
                if keyword_search_needed:
                    logger.warning(
                        f"Full-text search requested for collection {cid} but not implemented in PgVector store"
                    )

                semantic_search_result, keyword_search_result = await asyncio.gather(
                    semantic_search_task, keyword_search_task
                )

                if semantic_search_needed and keyword_search_needed:
                    # For now, just return semantic search results since keyword search isn't implemented
                    return semantic_search_result or []
                if semantic_search_needed:
                    return semantic_search_result or []
                if keyword_search_needed:
                    return keyword_search_result or []

                return []
            except Exception as e:
                logger.error(
                    "Exception in _search_in_collection for collection %s: %s",
                    cid,
                    e,
                    exc_info=True,
                )
                return []

        # Execute searches in parallel
        search_tasks = [_search_in_collection(cid) for cid in collection_ids]
        all_results_nested = await asyncio.gather(*search_tasks)

        # Flatten results
        all_results = []
        for result in all_results_nested:
            if result:
                all_results.extend(result)

        # Sort by similarity score (descending)
        search_result_sorted = sorted(
            all_results,
            key=lambda x: getattr(x, "score", 0),
            reverse=True,
        )

        return search_result_sorted
