# API Endpoints

Complete reference for all Magnet AI REST API endpoints.

## Base URL

```
http://localhost:5000/api
```

All endpoints are prefixed with `/api`.

## Agents

### List All Agents

```http
GET /api/agents
```

**Query Parameters:**
- `page` (integer) - Page number (default: 1)
- `limit` (integer) - Items per page (default: 20)
- `sort` (string) - Sort field (default: created_at)
- `order` (string) - Sort order: asc|desc (default: desc)

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
      "temperature": 0.7,
      "tools": ["rag_tool_1"],
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5
  }
}
```

### Get Single Agent

```http
GET /api/agents/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "agent_123",
    "name": "Customer Support Agent",
    "description": "Handles customer inquiries",
    "system_prompt": "You are a helpful customer support assistant",
    "model_id": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "tools": ["rag_tool_1", "api_tool_2"],
    "topics": [...],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T12:30:00Z"
  }
}
```

### Create Agent

```http
POST /api/agents
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "New Agent",
  "description": "Agent description",
  "system_prompt": "You are a helpful assistant",
  "model_id": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "tools": ["rag_tool_1"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "agent_456",
    "name": "New Agent",
    ...
  }
}
```

### Update Agent

```http
PUT /api/agents/{id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "temperature": 0.8
}
```

### Delete Agent

```http
DELETE /api/agents/{id}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent deleted successfully"
}
```

## Prompt Templates

### List Prompt Templates

```http
GET /api/prompt-templates
```

### Get Prompt Template

```http
GET /api/prompt-templates/{id}
```

### Create Prompt Template

```http
POST /api/prompt-templates
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Customer Support Template",
  "description": "Template for customer support",
  "template": "You are a customer support agent. Topic: {{topic}}",
  "variables": ["topic"],
  "type": "system"
}
```

### Update Prompt Template

```http
PUT /api/prompt-templates/{id}
```

### Delete Prompt Template

```http
DELETE /api/prompt-templates/{id}
```

## Knowledge Sources

### List Knowledge Sources

```http
GET /api/knowledge-sources
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ks_123",
      "name": "Product Documentation",
      "type": "file",
      "status": "active",
      "last_sync": "2025-01-15T10:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Get Knowledge Source

```http
GET /api/knowledge-sources/{id}
```

### Create Knowledge Source

```http
POST /api/knowledge-sources
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Product Documentation",
  "type": "file",
  "configuration": {
    "file_types": ["pdf", "txt", "md"],
    "max_file_size": 10485760
  }
}
```

### Update Knowledge Source

```http
PUT /api/knowledge-sources/{id}
```

### Delete Knowledge Source

```http
DELETE /api/knowledge-sources/{id}
```

### Sync Knowledge Source

```http
POST /api/knowledge-sources/{id}/sync
```

Triggers a synchronization of the knowledge source.

## RAG Tools

### List RAG Tools

```http
GET /api/rag-tools
```

### Get RAG Tool

```http
GET /api/rag-tools/{id}
```

### Create RAG Tool

```http
POST /api/rag-tools
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Product Q&A",
  "description": "Answer questions about products",
  "knowledge_source_id": "ks_123",
  "embedding_model": "text-embedding-ada-002",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "top_k": 5
}
```

### Update RAG Tool

```http
PUT /api/rag-tools/{id}
```

### Delete RAG Tool

```http
DELETE /api/rag-tools/{id}
```

### Query RAG Tool

```http
POST /api/rag-tools/{id}/query
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "How do I reset my password?",
  "top_k": 3,
  "filters": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "How do I reset my password?",
    "results": [
      {
        "content": "To reset your password...",
        "score": 0.92,
        "metadata": {
          "source": "user_guide.pdf",
          "page": 15
        }
      }
    ],
    "answer": "Based on the documentation, to reset your password..."
  }
}
```

## Retrieval Tools

### List Retrieval Tools

```http
GET /api/retrieval-tools
```

### Create Retrieval Tool

```http
POST /api/retrieval-tools
```

### Query Retrieval Tool

```http
POST /api/retrieval-tools/{id}/search
```

## Conversations

### List Conversations

```http
GET /api/conversations?agent_id=agent_123
```

### Get Conversation

```http
GET /api/conversations/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "conv_789",
    "agent_id": "agent_123",
    "user_id": "user_456",
    "messages": [
      {
        "role": "user",
        "content": "Hello",
        "timestamp": "2025-01-15T10:00:00Z"
      },
      {
        "role": "assistant",
        "content": "Hi! How can I help you?",
        "timestamp": "2025-01-15T10:00:02Z"
      }
    ],
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

### Create Conversation

```http
POST /api/conversations
Content-Type: application/json
```

**Request Body:**
```json
{
  "agent_id": "agent_123",
  "user_id": "user_456"
}
```

### Send Message

```http
POST /api/conversations/{id}/messages
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "I need help with my order",
  "stream": false
}
```

**Streaming Response:**
Set `stream: true` for streaming responses via Server-Sent Events (SSE).

## Models

### List Models

```http
GET /api/models
```

### Get Model

```http
GET /api/models/{id}
```

### Add Model

```http
POST /api/models
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "GPT-4 Turbo",
  "provider": "openai",
  "model_id": "gpt-4-turbo-preview",
  "api_key": "sk-...",
  "endpoint": "https://api.openai.com/v1",
  "pricing": {
    "input_per_1k": 0.01,
    "output_per_1k": 0.03
  }
}
```

### Update Model

```http
PUT /api/models/{id}
```

### Delete Model

```http
DELETE /api/models/{id}
```

## Evaluations

### List Evaluations

```http
GET /api/evaluations
```

### Get Evaluation

```http
GET /api/evaluations/{id}
```

### Create Evaluation

```http
POST /api/evaluations
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Agent Accuracy Test",
  "type": "agent",
  "target_id": "agent_123",
  "test_cases": [
    {
      "input": "What is your return policy?",
      "expected_output": "Our return policy allows...",
      "metadata": {}
    }
  ]
}
```

### Run Evaluation

```http
POST /api/evaluations/{id}/run
```

### Get Evaluation Results

```http
GET /api/evaluations/{id}/results
```

## Usage & Analytics

### Get Usage Statistics

```http
GET /api/usage/stats
```

**Query Parameters:**
- `start_date` (ISO date) - Start date
- `end_date` (ISO date) - End date
- `entity_type` (string) - Filter by entity type
- `entity_id` (string) - Filter by entity ID

**Response:**
```json
{
  "success": true,
  "data": {
    "total_tokens": 1500000,
    "total_cost": 45.50,
    "by_model": {
      "gpt-4": {
        "tokens": 1000000,
        "cost": 35.00
      }
    },
    "by_entity": {...}
  }
}
```

### Get Cost Analysis

```http
GET /api/usage/costs?entity_type=agent&entity_id=agent_123
```

### Get Conversation Analytics

```http
GET /api/analytics/conversations
```

## API Tools

### List API Tools

```http
GET /api/api-tools
```

### Create API Tool

```http
POST /api/api-tools
```

### Test API Tool

```http
POST /api/api-tools/{id}/test
```

## Health & Status

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "vector_db": "connected"
}
```

### System Status

```http
GET /api/status
```

## Next Steps

- [REST API](/docs/en/developers/api/rest-api) - API overview
- [Authentication](/docs/en/developers/api/authentication) - Authentication guide
- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
