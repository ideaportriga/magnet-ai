# Database Schema

Magnet AI uses **PostgreSQL** as its primary database, leveraging the **pgvector** extension to store both relational data and vector embeddings in a single system.

## Core Models

### Agents

Stores AI agent configurations.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Agent name
- `description` - Agent description
- `system_prompt` - Base system prompt
- `model_id` - Associated LLM model
- `temperature` - Model temperature setting
- `max_tokens` - Maximum tokens
- `tools` - JSON array of available tools
- `topics` - Agent topics configuration
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Prompt Templates

Reusable prompt templates.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Template name
- `description` - Template description
- `template` - Prompt template text
- `variables` - JSON array of variables
- `type` - Template type (system, user, etc.)
- `is_default` - Default template flag
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Knowledge Sources

Data source configurations.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Source name
- `type` - Source type (file, api, database, etc.)
- `connection_string` - Connection details (Encrypted)
- `configuration` - JSON configuration
- `status` - Connection status
- `last_sync` - Last synchronization time
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### RAG Tools

RAG (Retrieval Augmented Generation) tool configurations.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Tool name
- `description` - Tool description
- `knowledge_source_id` - FK to knowledge source
- `embedding_model` - Embedding model name
- `retrieval_params` - JSON retrieval parameters
- `chunk_size` - Document chunk size
- `chunk_overlap` - Chunk overlap
- `top_k` - Number of results to retrieve
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Retrieval Tools

Semantic search and retrieval configurations.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Tool name
- `description` - Tool description
- `knowledge_source_id` - FK to knowledge source
- `retrieval_strategy` - Retrieval strategy
- `filters` - JSON filters
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Models

LLM model configurations.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Model name
- `provider` - Provider (OpenAI, Azure, etc.)
- `model_id` - Provider's model identifier
- `api_key` - Encrypted API key
- `endpoint` - Custom endpoint (if applicable)
- `pricing` - JSON pricing information
- `capabilities` - JSON capabilities
- `is_active` - Active status
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Conversations

Agent conversation history.

**Fields:**

- `id` - Primary key (UUID)
- `agent_id` - FK to agent
- `user_id` - User identifier
- `messages` - JSON array of messages
- `metadata` - JSON metadata
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Evaluations

Evaluation runs and results.

**Fields:**

- `id` - Primary key (UUID)
- `name` - Evaluation name
- `type` - Evaluation type
- `target_id` - FK to evaluated entity
- `test_cases` - JSON test cases
- `results` - JSON results
- `metrics` - JSON metrics
- `status` - Evaluation status
- `created_at` - Creation timestamp
- `completed_at` - Completion timestamp

### Usage Metrics

Track LLM usage and costs.

**Fields:**

- `id` - Primary key (UUID)
- `entity_type` - Entity type (agent, rag_tool, etc.)
- `entity_id` - Entity ID
- `model_id` - FK to model
- `prompt_tokens` - Input tokens
- `completion_tokens` - Output tokens
- `total_tokens` - Total tokens
- `cost` - Calculated cost
- `timestamp` - Usage timestamp

## Relationships

```
Models
  └── 1:N → Agents
  └── 1:N → Usage Metrics

Knowledge Sources
  └── 1:N → RAG Tools
  └── 1:N → Retrieval Tools

Agents
  └── 1:N → Conversations
  └── 1:N → Evaluations
  └── 1:N → Usage Metrics

RAG Tools
  └── 1:N → Evaluations
  └── 1:N → Usage Metrics

Prompt Templates
  └── M:N → Agents (used by agents)
```

## Vector Database (pgvector)

Magnet AI uses the `pgvector` extension within PostgreSQL to store and query embeddings. This allows for unified transaction management and simplified infrastructure.

### Document Embeddings Table

**Fields:**

- `id` - Document ID (UUID)
- `source_id` - FK to knowledge source
- `content` - Original text
- `embedding` - `vector(1536)` (or other dimension)
- `metadata` - JSON metadata
- `created_at` - Creation timestamp

### Vector Similarity Search

Queries use the `<=>` (cosine distance) or `<->` (Euclidean distance) operators for efficient similarity search.

## Migration Management

Migrations are managed using **Alembic**.

### Creating Migrations

```bash
npm run db:migrate -- -m "Add new field"
```

### Applying Migrations

```bash
npm run db:upgrade
```

## Database Configuration

### Connection String

We use the `asyncpg` driver for high-performance async access.

```python
DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"
```

## Fixtures and Seed Data

Located in `/api`:

- `manage_fixtures.py` - Load/save fixtures
- Sample data for development
- Test data for evaluations

## Indexes

Key indexes for performance:

- `agents.name` - Agent lookup
- `conversations.agent_id` - Conversation queries
- `usage_metrics.timestamp` - Time-based queries
- `knowledge_sources.type` - Source filtering
- **IVFFlat / HNSW Indexes**: On vector columns for fast approximate nearest neighbor search.

## Constraints

- Foreign key constraints enabled
- Unique constraints on names (where applicable)
- NOT NULL constraints on required fields
- Check constraints for enums

## Best Practices

1. **Use Migrations**: Always create migrations for schema changes
2. **Index Strategy**: Add indexes for frequently queried fields
3. **JSON Fields**: Use JSON for flexible, schema-less data
4. **Soft Deletes**: Consider soft deletes for audit trails
5. **Timestamps**: Always include created_at/updated_at

## Next Steps

- [Backend Architecture](/docs/en/developers/architecture/backend) - Backend implementation
- [REST API](/docs/en/developers/api/rest-api) - API endpoints
- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
