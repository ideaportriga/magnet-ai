# REST API

The Magnet AI REST API provides programmatic access to all platform functionality. This API follows RESTful principles and returns JSON responses.

## Base URL

```
http://localhost:5000/api
```

For production environments, replace with your deployed API URL.

## Authentication

Most API endpoints require authentication. Magnet AI supports token-based authentication.

### Getting an API Token

See [Authentication](/docs/en/developers/api/authentication) for detailed authentication setup.

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/agents
```

## API Conventions

### HTTP Methods

- `GET` - Retrieve resources
- `POST` - Create new resources
- `PUT` - Update existing resources (full update)
- `PATCH` - Partially update resources
- `DELETE` - Delete resources

### Response Format

All responses are in JSON format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Responses

Error responses include appropriate HTTP status codes:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Resource Endpoints

### Agents

#### List Agents

```http
GET /api/agents
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "agent_123",
      "name": "Customer Support Agent",
      "description": "Handles customer inquiries",
      "model_id": "gpt-4",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Agent

```http
GET /api/agents/{id}
```

#### Create Agent

```http
POST /api/agents
Content-Type: application/json

{
  "name": "New Agent",
  "description": "Agent description",
  "model_id": "gpt-4",
  "system_prompt": "You are a helpful assistant",
  "temperature": 0.7,
  "tools": ["rag_tool_1", "api_tool_2"]
}
```

#### Update Agent

```http
PUT /api/agents/{id}
Content-Type: application/json

{
  "name": "Updated Agent Name",
  "description": "Updated description"
}
```

#### Delete Agent

```http
DELETE /api/agents/{id}
```

### Prompt Templates

#### List Prompt Templates

```http
GET /api/prompt-templates
```

#### Get Prompt Template

```http
GET /api/prompt-templates/{id}
```

#### Create Prompt Template

```http
POST /api/prompt-templates
Content-Type: application/json

{
  "name": "Customer Support Template",
  "template": "You are a customer support agent. Help the user with: {{topic}}",
  "variables": ["topic"],
  "type": "system"
}
```

### Knowledge Sources

#### List Knowledge Sources

```http
GET /api/knowledge-sources
```

#### Create Knowledge Source

```http
POST /api/knowledge-sources
Content-Type: application/json

{
  "name": "Product Documentation",
  "type": "file",
  "configuration": {
    "file_types": ["pdf", "txt", "md"]
  }
}
```

#### Sync Knowledge Source

```http
POST /api/knowledge-sources/{id}/sync
```

### RAG Tools

#### List RAG Tools

```http
GET /api/rag-tools
```

#### Create RAG Tool

```http
POST /api/rag-tools
Content-Type: application/json

{
  "name": "Product Q&A",
  "knowledge_source_id": "ks_123",
  "embedding_model": "text-embedding-ada-002",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "top_k": 5
}
```

#### Query RAG Tool

```http
POST /api/rag-tools/{id}/query
Content-Type: application/json

{
  "query": "How do I reset my password?",
  "top_k": 3
}
```

### Conversations

#### List Conversations

```http
GET /api/conversations
```

#### Get Conversation

```http
GET /api/conversations/{id}
```

#### Create Conversation

```http
POST /api/conversations
Content-Type: application/json

{
  "agent_id": "agent_123",
  "user_id": "user_456"
}
```

#### Send Message

```http
POST /api/conversations/{id}/messages
Content-Type: application/json

{
  "message": "Hello, I need help with my order",
  "stream": false
}
```

### Models

#### List Models

```http
GET /api/models
```

#### Add Model

```http
POST /api/models
Content-Type: application/json

{
  "name": "GPT-4 Turbo",
  "provider": "openai",
  "model_id": "gpt-4-turbo-preview",
  "api_key": "sk-...",
  "pricing": {
    "input": 0.01,
    "output": 0.03
  }
}
```

### Evaluations

#### List Evaluations

```http
GET /api/evaluations
```

#### Create Evaluation

```http
POST /api/evaluations
Content-Type: application/json

{
  "name": "Agent Accuracy Test",
  "type": "agent",
  "target_id": "agent_123",
  "test_cases": [
    {
      "input": "Test query",
      "expected_output": "Expected response"
    }
  ]
}
```

#### Run Evaluation

```http
POST /api/evaluations/{id}/run
```

### Usage Metrics

#### Get Usage Statistics

```http
GET /api/usage/stats?start_date=2025-01-01&end_date=2025-01-31
```

#### Get Cost Analysis

```http
GET /api/usage/costs?entity_type=agent&entity_id=agent_123
```

## Pagination

List endpoints support pagination:

```http
GET /api/agents?page=1&limit=20
```

**Response:**

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

## Filtering and Sorting

### Filtering

```http
GET /api/agents?type=customer_support&status=active
```

### Sorting

```http
GET /api/agents?sort=created_at&order=desc
```

## Rate Limiting

API requests are rate-limited to prevent abuse:

- Rate limit: 100 requests per minute
- Headers include rate limit information

## Webhooks

Configure webhooks for event notifications:

- Conversation completed
- Evaluation finished
- Usage threshold exceeded

## API Versioning

The API version is included in the URL:

```
/api/v1/agents
```

Current version: v1

## Next Steps

- [Authentication](/docs/en/developers/api/authentication) - Set up authentication
- [API Endpoints](/docs/en/developers/api/endpoints) - Detailed endpoint reference
- [Plugin API](/docs/en/developers/plugins/plugin-api) - Plugin development API
