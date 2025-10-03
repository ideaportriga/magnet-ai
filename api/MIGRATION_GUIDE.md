# MongoDB to SQLAlchemy Data Migration Utility

This utility is designed for migrating data from MongoDB to PostgreSQL using SQLAlchemy ORM.

## Features

- **Configurable mapping**: Configurable correspondence between MongoDB collections and SQLAlchemy tables
- **Batch processing**: Processing large volumes of data in batches for performance optimization
- **Testing mode**: Dry-run mode for checking migration without making changes
- **Error handling**: Reliable error handling with transaction rollback
- **Detailed logging**: Detailed logs of the migration process
- **Skip existing records**: Ability to skip already existing records

## Prerequisites

### Installing dependencies

```bash
# Core dependencies for migration
pip install motor pymongo sqlalchemy

# If using PostgreSQL
pip install asyncpg

# For full project work
cd api
poetry install
```

### Environment variables setup

Make sure the following variables are configured in the `.env` file:

```bash
# MongoDB (Cosmos DB)
COSMOS_DB_CONNECTION_STRING=mongodb+srv://username:password@cluster.cosmos.azure.com/
COSMOS_DB_DB_NAME=magnet-test

# PostgreSQL (SQLAlchemy)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://user:password@host:port/database
```

## Usage

### Basic usage

```bash
# Run from api directory
cd api
python mongo_to_sqlalchemy_migration.py

# Or with Python environment path specified
poetry run python mongo_to_sqlalchemy_migration.py
```

### Command line parameters

```bash
# Test run without making changes
python mongo_to_sqlalchemy_migration.py --dry-run

# Migrate specific collection
python mongo_to_sqlalchemy_migration.py --collection agents

# Configure batch size
python mongo_to_sqlalchemy_migration.py --batch-size 500

# Disable skipping existing records
python mongo_to_sqlalchemy_migration.py --no-skip-existing

# Combine parameters
python mongo_to_sqlalchemy_migration.py --dry-run --collection collections --batch-size 100
```

## Collection mapping

The utility supports the following MongoDB collections and their correspondence to SQLAlchemy tables:

| MongoDB collection | SQLAlchemy model | Description |
|------------------|-------------------|----------|
| `agents` | `Agent` | AI agents |
| `ai_apps` | `AIApp` | AI applications |
| `collections` | `Collection` | Document collections |
| `jobs` | `Job` | Tasks and jobs |
| `api_keys` | `APIKey` | API keys |
| `api_servers` | `APIServer` | API servers |
| `api_tools` | `APITool` | API tools |
| `mcp_servers` | `MCPServer` | MCP servers |
| `rag_tools` | `RAGTool` | RAG tools |
| `retrieval_tools` | `RetrievalTool` | Search tools |
| `evaluations` | `Evaluation` | Evaluations |
| `evaluation_sets` | `EvaluationSet` | Evaluation sets |
| `metrics` | `Metric` | Metrics |
| `traces` | `Trace` | Traces |
| `prompts` | `Prompt` | Prompts |

## Usage examples

### 1. Test run before migration

```bash
python mongo_to_sqlalchemy_migration.py --dry-run
```

This mode will show:
- Which collections will be processed
- Number of documents in each collection
- Expected migration results
- Potential issues

### 2. Migrate specific collection

```bash
python mongo_to_sqlalchemy_migration.py --collection agents --dry-run
```

Useful for:
- Testing migration on a small dataset
- Debugging issues with specific collection
- Step-by-step migration

### 3. Full migration

```bash
python mongo_to_sqlalchemy_migration.py
```

### 4. Migration with performance tuning

```bash
python mongo_to_sqlalchemy_migration.py --batch-size 2000
```

## Migration process structure

1. **Database connections**: Connection established to MongoDB and PostgreSQL
2. **Collection list retrieval**: Available collections scanned in MongoDB
3. **Collection filtering**: Only collections with configured mapping are processed
4. **Batch processing**: Documents processed in batches for memory optimization
5. **Data transformation**: MongoDB documents converted to SQLAlchemy objects
6. **Saving to PostgreSQL**: Data saved with error handling

## Data transformation

### Transformation features:

- **ID fields**: `_id` from MongoDB is ignored, auto-generated `id` is used in PostgreSQL
- **Dates**: String date representations automatically converted to datetime objects
- **JSON fields**: Complex objects and arrays saved in PostgreSQL JSONB fields
- **Unknown fields**: Fields without correspondence in SQLAlchemy model logged as warnings

### Transformation examples:

```python
# MongoDB document
{
    "_id": "507f1f77bcf86cd799439011",
    "name": "Test Agent",
    "system_name": "test_agent",
    "created_at": "2023-01-15T10:30:00Z",
    "variants": [{"name": "v1", "config": {}}]
}

# SQLAlchemy object
Agent(
    name="Test Agent",
    system_name="test_agent", 
    created_at=datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    variants=[{"name": "v1", "config": {}}]
)
```

## Monitoring and logging

The utility provides detailed information about the process:

```
2023-01-15 10:30:00 - INFO - Starting migration of all collections
2023-01-15 10:30:01 - INFO - Found collections in MongoDB: count=15, names=['agents', 'collections', ...]
2023-01-15 10:30:01 - INFO - Collections to migrate: total_collections=12, supported_collections=8
2023-01-15 10:30:02 - INFO - Starting migration for collection: agents
2023-01-15 10:30:02 - INFO - Collection statistics: total_documents=150
2023-01-15 10:30:03 - INFO - Batch processed: processed=100, total=150, progress_percent=66.67
2023-01-15 10:30:04 - INFO - Collection migration completed: status=completed, processed=150, errors=0
```

## Error handling

### Error types:

1. **Connection errors**: Connection issues to MongoDB or PostgreSQL
2. **Transformation errors**: Data conversion problems
3. **Insertion errors**: Problems saving to PostgreSQL
4. **Validation errors**: Data not matching SQLAlchemy schema

### Recovery strategy:

- **Transaction rollback**: On batch error, entire transaction is rolled back
- **Continue processing**: Error in one batch doesn't stop processing of others
- **Detailed reporting**: All errors logged with contextual information

## Performance

### Configuration recommendations:

- **Batch size**: 1000-5000 documents (default 1000)
- **Connections**: SQLAlchemy connection pools are used
- **Memory**: Batch processing minimizes memory consumption

### Expected performance:

- **Simple documents**: ~1000-2000 documents/sec
- **Complex documents with JSON**: ~500-1000 documents/sec
- **Large collections**: Linear scaling

## Security

- **Transactions**: All changes within transactions with rollback capability
- **Dry-run mode**: Safe testing without data modification
- **Skip existing**: Avoid data duplication
- **Logging**: Sensitive data is not logged

## Extension

### Adding new models:

1. Add model import at the beginning of the file
2. Add mapping in `collection_model_mapping`
3. Configure special transformation if needed in `DocumentTransformer`

### Custom transformation:

```python
def transform_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
    transformed = super().transform_document(document)
    
    # Custom logic for specific model
    if self.model_class.__name__ == 'Agent':
        # Special processing for agents
        pass
    
    return transformed
```

## Troubleshooting

### Common issues:

1. **ImportError**: Make sure all dependencies are installed
2. **Connection timeout**: Check database connection strings
3. **Schema mismatch**: Ensure SQLAlchemy models are synchronized with MongoDB structure
4. **Memory issues**: Reduce batch size

### Debugging:

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python mongo_to_sqlalchemy_migration.py --dry-run

# Test on small sample
python mongo_to_sqlalchemy_migration.py --collection agents --batch-size 10 --dry-run
```

## Support

When problems occur:

1. Check execution logs
2. Run in `--dry-run` mode for diagnostics
3. Ensure connection settings are correct
4. Check dependency version compatibility