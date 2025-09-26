"""
Utility for migrating data from MongoDB to SQLAlchemy.

Supports:
- Configurable mapping between MongoDB collections and SQLAlchemy tables
- MongoDB connection via COSMOS_DB_CONNECTION_STRING
- Using e        # Special transformation for AIModel: rename model to ai_model
        if self.model_class.__name__ == 'AIModel':
            # Rename model to ai_model if it exists
            if 'model' in transformed and 'ai_model' not in transformed:
                transformed['ai_model'] = transformed.pop('model')
            
            # Ensure ai_model is not null
            if 'ai_model' not in transformed or transformed['ai_model'] is None:
                # Set a default value
                transformed['ai_model'] = 'unknown'
            
            # Ensure provider is not null
            if 'provider' not in transformed or transformed['provider'] is None:
                # Set a default value
                transformed['provider'] = 'unknown'
            
            # Convert price fields from float to string
            price_fields = ['price_input', 'price_output', 'price_cached']
            for field in price_fields:
                if field in transformed and isinstance(transformed[field], (int, float)):
                    transformed[field] = str(transformed[field])LAlchemy engine from the project
- Migration process logging
- Error handling and rollback when necessary
- MongoDB metadata processing (_metadata with dates)
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import uuid

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue without it
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add root directory to sys.path
root_path = Path(__file__).parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import inspect, select, delete
    
    # Project imports
    from src.core.config.base import get_settings, get_database_connection_settings
    
    # Imports of models from main package (those that are exported)
    from src.core.db.models import APIKey, Job, Metric, Trace, Evaluation
    
    # Imports of individual models that are not exported in __init__.py
    from src.core.db.models.agent import Agent
    from src.core.db.models.agent_conversation import AgentConversation
    from src.core.db.models.ai_app import AIApp
    from src.core.db.models.ai_model import AIModel
    from src.core.db.models.collection import Collection
    from src.core.db.models.api_server import APIServer
    from src.core.db.models.api_tool import APITool
    from src.core.db.models.mcp_server import MCPServer
    from src.core.db.models.rag_tool import RagTool
    from src.core.db.models.retrieval_tool import RetrievalTool
    from src.core.db.models.evaluation_set import EvaluationSet
    from src.core.db.models.prompt import Prompt
    
except ImportError as e:
    logger.error(f"Failed to import required dependencies: {e}")
    logger.info("Make sure to install: pip install motor sqlalchemy")
    sys.exit(1)


# Fixed namespace UUID for deterministic UUID generation from MongoDB ObjectId
MONGODB_OBJECTID_NAMESPACE = uuid.UUID('12345678-1234-5678-9012-123456789012')


@dataclass
class MigrationConfig:
    """Configuration for data migration."""
    
    mongodb_connection_string: str
    mongodb_database_name: str
    batch_size: int = 100
    dry_run: bool = False
    limit: Optional[int] = None  # Limit on the number of documents to migrate
    
    # Mapping of MongoDB collections to SQLAlchemy models
    collection_model_mapping: Dict[str, Type] = None
    
    def __post_init__(self):
        """Initialization after object creation."""
        if self.collection_model_mapping is None:
            self.collection_model_mapping = {
                # Core entities
                "agents": Agent,
                "agent_conversations": AgentConversation,
                "ai_apps": AIApp,
                "models": AIModel,
                "prompts": Prompt,
                "rag_tools": RagTool,

                "retrieval_tools": RetrievalTool,
                "collections": Collection,
                # Tools and servers
                "api_keys": APIKey,
                "api_servers": APIServer,
                "mcp_servers": MCPServer,
                
                # Evaluation and metrics
                "evaluations": Evaluation,
                "evaluation_sets": EvaluationSet,
                "metrics": Metric,
                "traces": Trace,
            
               
            }


class DocumentTransformer:
    """Class for transforming MongoDB documents into SQLAlchemy objects."""
    
    def __init__(self, model_class: Type):
        self.model_class = model_class
        self.inspector = inspect(model_class)
        self.column_names = {col.name for col in self.inspector.columns}
    
    def transform_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MongoDB document to SQLAlchemy-compatible format."""
        transformed = {}
        
        # Handle _metadata field for timestamps
        if '_metadata' in doc:
            metadata = doc['_metadata']
            if isinstance(metadata, dict):
                # Extract created_at and modified_at from _metadata
                if 'created_at' in metadata:
                    created_at = self._transform_date_value(metadata['created_at'])
                    if created_at is not None:
                        transformed['created_at'] = created_at
                if 'modified_at' in metadata:
                    updated_at = self._transform_date_value(metadata['modified_at'])
                    if updated_at is not None:
                        transformed['updated_at'] = updated_at
        
        # Handle direct created_at and updated_at fields
        if 'created_at' in doc and 'created_at' not in transformed:
            created_at = self._transform_date_value(doc['created_at'])
            if created_at is not None:
                transformed['created_at'] = created_at
        if 'updated_at' in doc and 'updated_at' not in transformed:
            updated_at = self._transform_date_value(doc['updated_at'])
            if updated_at is not None:
                transformed['updated_at'] = updated_at
        
        # Set default timestamps if missing
        current_time = datetime.now(timezone.utc)
        if 'created_at' not in transformed:
            transformed['created_at'] = current_time
        if 'updated_at' not in transformed:
            transformed['updated_at'] = current_time
        
        # Copy other fields, skipping _id, _metadata, and id
        for key, value in doc.items():
            if key in ('_id', '_metadata', 'id'):
                continue
            
            # Handle nested documents and arrays
            transformed_value = self._transform_value(value)
            transformed[key] = transformed_value
        
        # Special handling for MCPServer and APIServer: remove secrets_encrypted field
        if self.model_class.__name__ in ('MCPServer', 'APIServer'):
            if 'secrets_encrypted' in transformed:
                del transformed['secrets_encrypted']
        
        # Special transformation for retrieval_tools: move specific fields to variants
        if self.model_class.__name__ == 'RetrievalTool':
            variants = []
            variant_1 = {}
            
            # Move specific fields to variant_1
            for field in ['retrieve', 'ui_settings', 'language', 'sample_test_set']:
                variant_1['variant'] = 'variant_1'
                if field in transformed:
                    variant_1[field] = transformed.pop(field)
            
            if variant_1:
                variants.append(variant_1)
                transformed['variants'] = variants
                transformed['active_variant'] = 'variant_1'
        
        # Special transformation for collections: rename model to ai_model and collect source fields
        if self.model_class.__name__ == 'Collection':
            # Rename model to ai_model
            if 'model' in transformed:
                transformed['ai_model'] = transformed.pop('model')
            
            # Collect source fields
            source_fields = [
                'source_type', 'file_url', 'sharepoint_site_url', 'sharepoint_folder', 
                'sharepoint_pages_page_name', 'sharepoint_library', 'sharepoint_recursive', 
                'sharepoint_pages_embed_title', 'object_api_name', 'output_config', 
                'confluence_url', 'confluence_space', 'oracle_knowledge_url', 'fluid_topics_search_filters'
            ]
            source_dict = {}
            for field in source_fields:
                if field in transformed:
                    source_dict[field] = transformed.pop(field)
            
            if source_dict:
                transformed['source'] = source_dict
            
            # Generate system_name from name if missing
            if 'system_name' not in transformed or transformed['system_name'] is None:
                if 'name' in transformed and transformed['name']:
                    # Convert name to uppercase and replace spaces/special chars with underscores
                    system_name = str(transformed['name']).upper().replace(' ', '_').replace('-', '_').replace('/', '_')
                    # Remove multiple consecutive underscores
                    import re
                    system_name = re.sub(r'_+', '_', system_name).strip('_')
                    transformed['system_name'] = system_name
                else:
                    # Fallback: generate a unique system_name
                    import uuid
                    transformed['system_name'] = f"COLLECTION_{str(uuid.uuid4())[:8].upper()}"
        
        # Special transformation for AIModel: rename model to ai_model
        if self.model_class.__name__ == 'AIModel':
            # Rename model to ai_model if it exists
            if 'model' in transformed and 'ai_model' not in transformed:
                transformed['ai_model'] = transformed.pop('model')
            
            # Ensure ai_model is not null
            if 'ai_model' not in transformed or transformed['ai_model'] is None:
                # Set a default value or skip - for now, set default
                transformed['ai_model'] = 'unknown'
            
            # Ensure provider is not null
            if 'provider' not in transformed or transformed['provider'] is None:
                transformed['provider'] = 'unknown'
            
            # Ensure display_name is not null
            if 'display_name' not in transformed or transformed['display_name'] is None:
                # Set display_name to system_name or a default value
                if 'system_name' in transformed and transformed['system_name']:
                    transformed['display_name'] = transformed['system_name']
                else:
                    transformed['display_name'] = 'Unknown Model'
            
            # Ensure type is not null
            if 'type' not in transformed or transformed['type'] is None:
                transformed['type'] = 'prompts'
            
            # Convert price fields from float to string
            price_fields = ['price_input', 'price_output', 'price_cached']
            for field in price_fields:
                if field in transformed and isinstance(transformed[field], (int, float)):
                    transformed[field] = str(transformed[field])
            
            # Handle datetime fields with defaults
            now = datetime.now(timezone.utc)
            if 'created_at' not in transformed or transformed['created_at'] is None:
                transformed['created_at'] = now
            if 'updated_at' not in transformed or transformed['updated_at'] is None:
                transformed['updated_at'] = now
        if self.model_class.__name__ == 'Trace':
            # Set default type if null or missing
            if 'type' not in transformed or transformed['type'] is None:
                transformed['type'] = 'unknown'
            
            # Set default status if null or missing
            if 'status' not in transformed or transformed['status'] is None:
                transformed['status'] = 'unknown'
        
        # Generate new UUID for id instead of using MongoDB ObjectId
        # For metrics, use the existing _id field from MongoDB ObjectId
        if self.model_class.__name__ == 'Metric' or self.model_class.__name__ == 'Trace':
            # Use MongoDB ObjectId as string for metrics
            transformed['id'] = str(doc['_id'])
        else:
            import uuid
            transformed['id'] = str(uuid.uuid4())
        
        return transformed
    
    def _transform_date_value(self, value: Any) -> Optional[datetime]:
        """Transform MongoDB date value to datetime object."""
        if isinstance(value, dict) and '$date' in value:
            try:
                date_str = value['$date']
                if isinstance(date_str, str):
                    # Handle ISO format with Z suffix
                    if date_str.endswith('Z'):
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        return datetime.fromisoformat(date_str)
                else:
                    logger.debug(f"Unexpected date format: {value}")
                    return None
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse date {value}: {e}")
                return None
        elif isinstance(value, datetime):
            # Ensure datetime has timezone info for PostgreSQL
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        elif isinstance(value, str):
            try:
                # Try to parse as ISO format with timezone
                if '+' in value or value.endswith('Z'):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    # Assume UTC if no timezone
                    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
            except ValueError:
                logger.debug(f"Could not parse date string: {value}")
                return None
        else:
            logger.debug(f"Unexpected date type: {type(value)}")
            return None

    def _transform_value(self, value: Any) -> Any:
        """Transform a value recursively."""
        if isinstance(value, dict):
            # Handle MongoDB ObjectId references
            if '$oid' in value:
                return value['$oid']
            # Handle MongoDB dates
            elif '$date' in value:
                return self._transform_date_value(value)
            # Handle other MongoDB special types
            elif '$numberInt' in value:
                return int(value['$numberInt'])
            elif '$numberLong' in value:
                return int(value['$numberLong'])
            elif '$numberDouble' in value:
                return float(value['$numberDouble'])
            # Recursively transform nested objects
            else:
                return {k: self._transform_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._transform_value(item) for item in value]
        elif isinstance(value, str):
            # Try to transform string values that might be dates
            date_result = self._transform_date_value(value)
            if date_result is not None:
                return date_result
            return value
        elif isinstance(value, datetime):
            # Ensure datetime has timezone info for PostgreSQL
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        else:
            return value


class MongoToSQLAlchemyMigrator:
    """Main class for migrating data from MongoDB to SQLAlchemy."""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.mongodb_database: Optional[AsyncIOMotorDatabase] = None
        self.sqlalchemy_session: Optional[AsyncSession] = None
        
        # Get SQLAlchemy settings from the project
        self.settings = get_settings()
        self.db_settings = get_database_connection_settings()
        
        # Create SQLAlchemy session factory
        self.session_factory = sessionmaker(
            bind=self.settings.db.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Establishes connections to MongoDB and SQLAlchemy."""
        logger.warning("Connecting to databases")
        
        # MongoDB connection
        self.mongodb_client = AsyncIOMotorClient(self.config.mongodb_connection_string)
        self.mongodb_database = self.mongodb_client[self.config.mongodb_database_name]
        
        # Test MongoDB connection
        try:
            await self.mongodb_client.admin.command('ping')
            logger.warning("MongoDB connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Create SQLAlchemy session
        self.sqlalchemy_session = self.session_factory()
        
        logger.warning("Database connections established")
    
    async def disconnect(self):
        """Closes database connections."""
        if self.sqlalchemy_session:
            await self.sqlalchemy_session.close()
            logger.warning("SQLAlchemy session closed")
        
        if self.mongodb_client:
            self.mongodb_client.close()
            logger.warning("MongoDB connection closed")
    
    async def get_collection_names(self) -> List[str]:
        """Gets the list of all collections in MongoDB."""
        collection_names = await self.mongodb_database.list_collection_names()
        logger.info(f"Found collections in MongoDB: count={len(collection_names)}, names={collection_names}")
        return collection_names
    
    async def migrate_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Migrates one collection from MongoDB to SQLAlchemy.
        
        Args:
            collection_name: Name of the collection to migrate
            
        Returns:
            Migration statistics
        """
        logger.warning(f"Starting migration for collection: {collection_name}")
        
        if collection_name not in self.config.collection_model_mapping:
            logger.warning(f"No model mapping found for collection: {collection_name}")
            return {
                "collection_name": collection_name,
                "status": "skipped",
                "reason": "No model mapping configured",
                "total_documents": 0,
                "processed": 0,
                "errors": 0
            }
        
        model_class = self.config.collection_model_mapping[collection_name]
        transformer = DocumentTransformer(model_class)
        
        # Get MongoDB collection
        mongodb_collection = self.mongodb_database[collection_name]
        
        # Count total number of documents
        total_documents = await mongodb_collection.count_documents({})
        
        # Apply limit if specified
        if self.config.limit is not None:
            total_documents = min(total_documents, self.config.limit)
            logger.warning(f"Limited migration to {total_documents} documents (limit: {self.config.limit})")
        else:
            logger.warning(f"Found {total_documents} documents in collection {collection_name}")
        
        if total_documents == 0:
            logger.warning(f"Collection {collection_name} is empty, skipping")
            return {
                "collection_name": collection_name,
                "status": "completed",
                "reason": "Empty collection",
                "total_documents": 0,
                "processed": 0,
                "errors": 0
            }
        
        processed_count = 0
        error_count = 0
        
        try:
            # Process documents in batches, each batch in its own transaction
            async for batch in self._get_batches(mongodb_collection, self.config.batch_size):
                batch_results = await self._process_batch(batch, transformer, model_class)
                processed_count += batch_results["processed"]
                error_count += batch_results["errors"]
                
                if batch_results["errors"] > 0:
                    logger.warning(f"Batch had {batch_results['errors']} errors, but continuing with next batch")
            
            # All batches processed
            logger.warning(f"Migration completed for collection {collection_name}: processed {processed_count}, errors {error_count}")
            
            result = {
                "collection_name": collection_name,
                "status": "completed",
                "total_documents": total_documents,
                "processed": processed_count,
                "errors": error_count
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during migration of collection {collection_name}: {e}")
            
            return {
                "collection_name": collection_name,
                "status": "failed",
                "reason": str(e),
                "total_documents": total_documents,
                "processed": processed_count,
                "errors": error_count + 1
            }
    
    async def _get_batches(self, collection, batch_size: int):
        """Generator for getting documents in batches."""
        cursor = collection.find({})
        batch = []
        processed_total = 0
        
        async for doc in cursor:
            if self.config.limit is not None and processed_total >= self.config.limit:
                break
                
            batch.append(doc)
            processed_total += 1
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield the last incomplete batch
        if batch:
            yield batch
    
    async def _process_batch(self, batch: List[Dict], transformer: DocumentTransformer, model_class: Type) -> Dict[str, int]:
        """Processes one batch of documents."""
        processed = 0
        errors = 0
        
        if self.config.dry_run:
            # For dry-run just count documents
            for doc in batch:
                try:
                    transformed_doc = transformer.transform_document(doc)
                    logger.debug(f"DRY RUN: Would process document with id={transformed_doc.get('id')}")
                    processed += 1
                except Exception as e:
                    logger.error(f"Error transforming document {doc.get('_id', 'unknown')}: {e}")
                    errors += 1
            return {"processed": processed, "errors": errors}
        
        # Start transaction for this batch
        try:
            await self.sqlalchemy_session.begin()
            
            for doc in batch:
                try:
                    # Transform document
                    transformed_doc = transformer.transform_document(doc)
                    
                    # Handle uniqueness by deleting existing records
                    if model_class.__name__ == 'Metric':
                        # For metrics, check by id
                        existing = await self.sqlalchemy_session.execute(
                            select(model_class).where(model_class.id == transformed_doc['id'])
                        )
                        existing_record = existing.scalar_one_or_none()
                        if existing_record:
                            # Skip duplicate
                            logger.debug(f"Skipping duplicate metric with id: {transformed_doc['id']}")
                            processed += 1
                            continue
                    elif 'system_name' in transformed_doc:
                        system_name = transformed_doc['system_name']
                        
                        # Check if system_name already exists
                        existing = await self.sqlalchemy_session.execute(
                            select(model_class).where(model_class.system_name == system_name)
                        )
                        existing_record = existing.scalar_one_or_none()
                        if existing_record:
                            # Delete the existing record
                            await self.sqlalchemy_session.execute(
                                delete(model_class).where(model_class.system_name == system_name)
                            )
                            logger.debug(f"Deleted existing record with system_name: {system_name}")
                    
                    # Create new record
                    # Filter only fields that exist in the model
                    model_fields = {col.name for col in inspect(model_class).columns}
                    filtered_doc = {k: v for k, v in transformed_doc.items() if k in model_fields}
                    
                    new_record = model_class(**filtered_doc)
                    self.sqlalchemy_session.add(new_record)
                    logger.debug(f"Created new record: {transformed_doc['id']}")
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {doc.get('_id', 'unknown')}: {e}")
                    errors += 1
                    continue
            
            # Commit batch
            await self.sqlalchemy_session.commit()
            logger.debug(f"Committed batch with {processed} records")
            
        except Exception as e:
            # Rollback batch in case of error
            logger.error(f"Error in batch, rolling back: {e}")
            if self.sqlalchemy_session.in_transaction():
                await self.sqlalchemy_session.rollback()
            errors += len(batch) - processed  # All documents in batch are considered errors
        
        return {"processed": processed, "errors": errors}
    
    async def migrate_all_collections(self) -> Dict[str, Any]:
        """Migrates all configured collections."""
        logger.warning("Starting migration of all collections")
        
        results = []
        total_processed = 0
        total_errors = 0
        
        for collection_name in self.config.collection_model_mapping.keys():
            try:
                result = await self.migrate_collection(collection_name)
                results.append(result)
                total_processed += result.get("processed", 0)
                total_errors += result.get("errors", 0)
            except Exception as e:
                logger.error(f"Failed to migrate collection {collection_name}: {e}")
                results.append({
                    "collection_name": collection_name,
                    "status": "failed",
                    "reason": str(e),
                    "total_documents": 0,
                    "processed": 0,
                    "errors": 1
                })
                total_errors += 1
        
        summary = {
            "status": "completed",
            "collections": results,
            "summary": {
                "total_collections": len(results),
                "successful_collections": len([r for r in results if r["status"] == "completed"]),
                "total_processed": total_processed,
                "total_errors": total_errors
            }
        }
        
        logger.warning(f"Migration summary: {summary['summary']}")
        return summary


async def main():
    """Main function for running migration."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Migrate data from MongoDB to SQLAlchemy')
    parser.add_argument('--collection', type=str, help='Specific collection to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without actually inserting data')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing documents')
    parser.add_argument('--mongodb-db', type=str, default=None, help='MongoDB database name')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of documents to migrate (useful for testing)')
    
    args = parser.parse_args()
    
    # Get MongoDB connection string from environment variable
    mongodb_connection_string = os.getenv('COSMOS_DB_CONNECTION_STRING')
    if not mongodb_connection_string:
        logger.error("COSMOS_DB_CONNECTION_STRING environment variable is not set")
        return 1
    
    # Get MongoDB database name from environment variable
    mongodb_db_name = os.getenv('COSMOS_DB_DB_NAME', 'magnet')
    logger.warning(f"Using MongoDB database: {mongodb_db_name} (from COSMOS_DB_DB_NAME env var)")
    
    # Create migration configuration
    config = MigrationConfig(
        mongodb_connection_string=mongodb_connection_string,
        mongodb_database_name=args.mongodb_db if args.mongodb_db else mongodb_db_name,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        limit=args.limit
    )
    
    logger.warning(f"Starting migration with config: db={config.mongodb_database_name}, "
                f"batch_size={config.batch_size}, dry_run={config.dry_run}, limit={config.limit}")
    
    try:
        async with MongoToSQLAlchemyMigrator(config) as migrator:
            if args.collection:
                # Migrate one collection
                result = await migrator.migrate_collection(args.collection)
                print(json.dumps(result, indent=2, default=str))
            else:
                # Migrate all collections
                result = await migrator.migrate_all_collections()
                print(json.dumps(result, indent=2, default=str))
        
        logger.warning("Migration completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)