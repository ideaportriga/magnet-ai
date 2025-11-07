# Backend Architecture

The Magnet AI backend is built with Python and Flask, providing a robust API layer and AI orchestration capabilities.

## Project Structure

```
api/
├── src/
│   ├── app.py                 # Application entry point
│   ├── models.py              # SQLAlchemy models
│   ├── api/                   # API endpoints
│   ├── config/                # Configuration management
│   ├── core/                  # Core business logic
│   ├── data_sources/          # Data source integrations
│   ├── guards/                # Authorization guards
│   ├── middlewares/           # Request/response middlewares
│   ├── open_ai/              # OpenAI integration
│   ├── plugins/               # Plugin system
│   ├── routes/                # Route definitions
│   ├── scheduler/             # Background tasks
│   ├── services/              # Business services
│   ├── stores/                # Data access layer
│   ├── tools/                 # AI tools (RAG, retrieval)
│   └── utils/                 # Utility functions
├── scripts/                   # Database and setup scripts
├── static/                    # Static files
├── tests/                     # Test suite
├── pyproject.toml            # Dependencies (Poetry)
└── run.py                    # Development server
```

## Core Components

### Application Layer (`app.py`)
- Flask application factory
- Middleware registration
- Route registration
- Database initialization
- CORS configuration

### Models (`models.py`)
SQLAlchemy ORM models representing:
- Agents
- Prompt Templates
- Knowledge Sources
- RAG Tools
- Retrieval Tools
- Conversations
- Usage metrics

### API Layer (`/api`)
RESTful endpoints organized by resource:
- `/agents` - Agent management
- `/prompt-templates` - Prompt template CRUD
- `/knowledge-sources` - Knowledge source management
- `/rag-tools` - RAG tool configuration
- `/conversations` - Conversation history
- `/evaluations` - Evaluation management

### Services (`/services`)
Business logic layer containing:
- Agent execution service
- RAG orchestration service
- Embedding generation service
- Model management service
- Evaluation service

### Plugin System (`/plugins`)
Extensible plugin architecture:
- Base plugin interface
- Plugin discovery and loading
- Plugin lifecycle management
- External plugin support

### Data Sources (`/data_sources`)
Connectors for various data sources:
- File uploads
- External APIs
- Database connections
- Vector stores

### Tools (`/tools`)
AI tools implementation:
- RAG tools for document Q&A
- Retrieval tools for semantic search
- API tools for external integrations

## Key Architectural Patterns

### 1. Service Layer Pattern
Business logic is encapsulated in service classes:
```python
# Example service structure
class AgentService:
    def create_agent(self, data):
        # Validation
        # Business logic
        # Database operations
        pass
```

### 2. Repository Pattern
Data access is abstracted through stores:
```python
# Example store/repository
class AgentStore:
    def find_by_id(self, agent_id):
        return Agent.query.get(agent_id)
```

### 3. Plugin Pattern
Extensions are loaded dynamically:
```python
# Plugin discovery and registration
plugin_manager.discover_plugins()
plugin_manager.register(plugin_instance)
```

### 4. Dependency Injection
Configuration and dependencies are injected:
- Environment-based configuration
- Service initialization
- Database session management

## Database Integration

### SQLAlchemy ORM
- Models defined in `models.py`
- Migrations managed with Alembic (or custom scripts)
- Support for SQLite (dev) and PostgreSQL (prod)

### Vector Database
- Embedding storage for semantic search
- Integration with retrieval tools
- Configurable vector dimensions

## AI Integration

### OpenAI Service
- GPT model integration
- Streaming support
- Token usage tracking
- Error handling and retries

### LangChain Integration
- Agent framework
- Tool calling
- Memory management
- Prompt templating

## Background Tasks

### Scheduler (`/scheduler`)
APScheduler for background jobs:
- Data synchronization
- Periodic cleanups
- Metric aggregation

## Configuration Management

### Environment Variables
- `OPENAI_API_KEY`
- `DATABASE_URL`
- `VECTOR_DB_CONFIG`
- Plugin-specific settings

### Configuration Files
- `config/` directory for environment-specific settings
- Support for development, staging, production

## Error Handling

- Custom exception classes
- Consistent error responses
- Logging and monitoring
- Graceful degradation

## Testing

Located in `/tests`:
- Unit tests for services
- Integration tests for API endpoints
- Mock data and fixtures
- Test database configuration

## API Documentation

- OpenAPI/Swagger specification (if available)
- Endpoint documentation
- Request/response examples
- Authentication requirements

## Next Steps

- [Frontend Architecture](/docs/en/developers/architecture/frontend) - Frontend details
- [Database Schema](/docs/en/developers/architecture/database) - Data models
- [REST API](/docs/en/developers/api/rest-api) - API reference
