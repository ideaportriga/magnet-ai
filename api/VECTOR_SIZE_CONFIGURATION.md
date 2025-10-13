# Vector Size Configuration for Embedding Models

## Overview

This document explains how to configure vector dimensions for embedding models in the Magnet AI system.

## Problem Solved

Previously, the system hardcoded vector dimensions to 1536 (the default for OpenAI's text-embedding-ada-002). This caused errors when using models with different vector dimensions, such as:
- `text-embedding-3-small` (1536 dimensions)
- `text-embedding-3-large` (3072 dimensions, or configurable 256-3072)
- Other embedding models with custom dimensions (e.g., 1024, 768, etc.)

## Solution

A new `configs` JSON field has been added to the AI Models table to store additional model configurations, including vector dimensions for embedding models.

## Database Schema

### AI Models Table

A new column has been added:
- `configs`: JSONB field for storing model-specific configurations

Example configuration:
```json
{
  "vector_size": 1024
}
```

## Migration

Run the migration to add the `configs` field:

```bash
cd api
python manage_migrations.py upgrade
```

## Usage

### 1. Configure an Embedding Model with Vector Size

When creating or updating an embedding model, include the `configs` field with `vector_size`:

**Example API Request:**
```json
{
  "system_name": "openai-embedding-3-small",
  "provider_name": "openai",
  "provider_system_name": "openai",
  "ai_model": "text-embedding-3-small",
  "display_name": "OpenAI Embedding 3 Small",
  "type": "embeddings",
  "is_default": false,
  "configs": {
    "vector_size": 1024
  }
}
```

**Another Example (default 1536):**
```json
{
  "system_name": "openai-embedding-ada-002",
  "provider_name": "openai",
  "provider_system_name": "openai",
  "ai_model": "text-embedding-ada-002",
  "display_name": "OpenAI Ada 002",
  "type": "embeddings",
  "is_default": true,
  "configs": {
    "vector_size": 1536
  }
}
```

### 2. How It Works

When a collection is created with an embedding model:

1. The system retrieves the model configuration including the `configs` field
2. Extracts the `vector_size` from `configs` (defaults to 1536 if not specified)
3. Creates the pgvector table with the correct vector dimension:
   ```sql
   embedding vector(1024)  -- or whatever size is configured
   ```

### 3. Automatic Vector Size Detection

The `PgVectorStore` class now includes:

- `_get_vector_size_from_model(model_system_name)`: Retrieves vector size from model config
- `_create_documents_table(collection_id, vector_size)`: Creates table with specified vector size
- `_ensure_documents_table_exists(collection_id)`: Automatically determines vector size when creating tables

### 4. Supported Vector Sizes

Common embedding model vector sizes:

| Model | Default Vector Size | Configurable Range |
|-------|--------------------|--------------------|
| text-embedding-ada-002 | 1536 | Fixed |
| text-embedding-3-small | 1536 | 512-1536 |
| text-embedding-3-large | 3072 | 256-3072 |
| Cohere embed-v3 | 1024 | Fixed |
| Custom models | Varies | Model-dependent |

## Examples

### Create a Collection with 1024-dimension Embeddings

1. First, create/update the embedding model:
```python
# Using the API or admin panel
{
  "system_name": "custom-embedding-1024",
  "provider_system_name": "openai",
  "ai_model": "text-embedding-3-small",
  "type": "embeddings",
  "configs": {
    "vector_size": 1024
  }
}
```

2. Create a collection using this model:
```python
{
  "name": "My Collection",
  "ai_model": "custom-embedding-1024",
  ...
}
```

3. The system will automatically create the documents table with `vector(1024)` instead of `vector(1536)`

## Backward Compatibility

- If `configs` is not specified or `vector_size` is not in configs, the system defaults to 1536
- Existing collections and models continue to work without modification
- No breaking changes to existing APIs

## Technical Details

### Modified Files

1. **Database Model**: `api/src/core/db/models/ai_model/ai_model.py`
   - Added `configs` field using `JsonB` type

2. **Pydantic Schema**: `api/src/core/domain/ai_models/schemas.py`
   - Added `configs: Optional[dict]` to schema classes

3. **PgVector Store**: `api/src/stores/pgvector_db/store.py`
   - Added `_get_vector_size_from_model()` method
   - Updated `_create_documents_table()` to accept `vector_size` parameter
   - Updated `_ensure_documents_table_exists()` to determine vector size from model

4. **Migration**: `api/src/core/db/migrations/versions/2025-10-13_add_configs_field_to_ai_models_a1b2c3d4e5f6.py`
   - Adds `configs` column to `ai_models` table

## Troubleshooting

### Error: "expected 1536 dimensions, not 1024"

**Cause**: The model is configured for 1024 dimensions but the table was created with 1536.

**Solution**:
1. Drop and recreate the collection, OR
2. Manually alter the table (advanced):
   ```sql
   -- This requires recreating the column
   ALTER TABLE documents_<collection_id> 
   ALTER COLUMN embedding TYPE vector(1024);
   ```

### How to Check Current Vector Size

```sql
SELECT 
    table_name,
    column_name,
    udt_name,
    character_maximum_length
FROM information_schema.columns
WHERE table_name LIKE 'documents_%'
  AND column_name = 'embedding';
```

## Best Practices

1. **Always specify `vector_size`** for embedding models in `configs`
2. **Use consistent vector sizes** across related collections
3. **Document the vector size** in the model's `display_name` or `resources` field
4. **Test with sample data** before deploying to production
5. **Plan storage requirements**: Larger vectors require more disk space and memory

## Future Enhancements

Potential future improvements:
- Automatic vector size detection from provider APIs
- Vector dimension validation on model creation
- Migration tool for converting existing collections to new vector sizes
- Support for multiple vector sizes in the same collection (multi-vector search)
