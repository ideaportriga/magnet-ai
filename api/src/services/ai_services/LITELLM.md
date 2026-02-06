# AI Services - LiteLLM Provider

## Overview

The LiteLLM provider enables advanced features for AI model management:

- **Load Balancing**: Distribute requests across multiple deployments
- **Failover**: Automatic fallback when a deployment fails
- **Rate Limiting**: RPM/TPM limits per deployment or per model
- **Batch Processing**: Efficient parallel request handling
- **Caching**: In-memory response caching with TTL
- **Per-Model Configuration**: Configure routing via AIModel.routing_config

## Configuration Modes

### 1. Router Mode (Provider-level configuration)

Use when you have multiple deployments for load balancing. Configure `model_list` in the provider's `router_config`.

### 2. Direct Mode (Model-level configuration)  

Use when you want simpler setup with per-model routing configuration. Configure `routing_config` on each AIModel.

## Provider Configuration (Router Mode)

Create a provider in the database with `type: "litellm"`:

### Database Provider Record

```json
{
  "system_name": "litellm-gpt4",
  "name": "LiteLLM GPT-4 Router",
  "type": "litellm",
  "endpoint": null,
  "connection_config": {
    "redis_host": "localhost",
    "redis_port": 6379,
    "cache_enabled": false
  },
  "secrets_encrypted": {
    "azure_api_key": "your-azure-key",
    "openai_api_key": "your-openai-key"
  },
  "metadata_info": {
    "defaults": {
      "model": "gpt-4o",
      "temperature": 0.7,
      "top_p": 1.0
    },
    "router_config": {
      "routing_strategy": "simple-shuffle",
      "num_retries": 3,
      "retry_after": 5,
      "timeout": 120,
      "allowed_fails": 3,
      "cooldown_time": 60,
      "model_list": [
        {
          "model_name": "gpt-4o",
          "litellm_params": {
            "model": "azure/gpt-4o-deployment",
            "api_key": "{azure_api_key}",
            "api_base": "https://your-resource.openai.azure.com/",
            "api_version": "2024-02-01",
            "rpm": 1000,
            "tpm": 100000
          }
        },
        {
          "model_name": "gpt-4o",
          "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": "{openai_api_key}",
            "rpm": 500,
            "tpm": 50000
          }
        }
      ],
      "embedding_model": "text-embedding-3-small",
      "rerank_model": "cohere/rerank-english-v3.0"
    }
  }
}
```

### Configuration Fields

#### `connection_config`

| Field | Type | Description |
|-------|------|-------------|
| `redis_host` | string | Redis host for distributed rate limiting (optional) |
| `redis_port` | int | Redis port (default: 6379) |
| `redis_password` | string | Redis password (optional) |
| `cache_enabled` | bool | Enable response caching |
| `cache_config` | object | Cache configuration options |

#### `router_config`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `routing_strategy` | string | `"simple-shuffle"` | Load balancing strategy |
| `num_retries` | int | `3` | Number of retries on failure |
| `retry_after` | int | `5` | Seconds to wait before retry |
| `timeout` | int | `120` | Request timeout in seconds |
| `allowed_fails` | int | `3` | Fails before marking deployment unhealthy |
| `cooldown_time` | int | `60` | Seconds before retrying failed deployment |
| `model_list` | array | **required** | List of model deployments |
| `embedding_model` | string | - | Default embedding model |
| `rerank_model` | string | - | Default rerank model |

## AIModel routing_config (Direct Mode)

When using Direct Mode, configure routing on each AIModel record:

```json
{
  "system_name": "gpt-4o-prod",
  "ai_model": "gpt-4o",
  "provider_system_name": "litellm-direct",
  "routing_config": {
    "rpm": 1000,
    "tpm": 100000,
    "fallback_models": ["gpt-4o-mini", "claude-3-sonnet"],
    "cache_enabled": true,
    "cache_ttl": 3600,
    "num_retries": 3,
    "retry_after": 5,
    "timeout": 120,
    "priority": 1,
    "weight": 0.8,
    "litellm_params": {
      "custom_llm_provider": "azure"
    }
  }
}
```

### routing_config Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rpm` | int | - | Requests per minute limit |
| `tpm` | int | - | Tokens per minute limit |
| `fallback_models` | array | - | List of model system_names for failover |
| `cache_enabled` | bool | `false` | Enable in-memory response caching |
| `cache_ttl` | int | `3600` | Cache TTL in seconds |
| `num_retries` | int | `3` | Number of retries on failure |
| `retry_after` | int | `5` | Seconds to wait before retry |
| `timeout` | int | `120` | Request timeout in seconds |
| `priority` | int | - | Priority for load balancing (lower = higher) |
| `weight` | float | - | Weight for weighted load balancing (0.0-1.0) |
| `litellm_params` | object | - | Additional LiteLLM parameters |

#### Routing Strategies

- `simple-shuffle`: Random selection (default)
- `least-busy`: Route to deployment with fewest in-flight requests
- `latency-based-routing`: Route based on response latency
- `cost-based-routing`: Route to cheapest available deployment

#### `model_list` Entry

```json
{
  "model_name": "alias-for-requests",
  "litellm_params": {
    "model": "provider/actual-model-name",
    "api_key": "{secret_placeholder}",
    "api_base": "https://endpoint.url/",
    "api_version": "2024-02-01",
    "rpm": 1000,
    "tpm": 100000
  }
}
```

### Secret Placeholders

Use `{secret_name}` syntax in `litellm_params` to reference values from `secrets_encrypted`:

```json
{
  "secrets_encrypted": {
    "azure_key": "actual-secret-value"
  },
  "metadata_info": {
    "router_config": {
      "model_list": [{
        "litellm_params": {
          "api_key": "{azure_key}"
        }
      }]
    }
  }
}
```

## Usage Examples

### Basic Chat Completion

```python
from services.ai_services.factory import get_ai_provider

provider = await get_ai_provider("litellm-gpt4")

response = await provider.create_chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4o",  # Uses the alias from model_list
    temperature=0.7
)
```

### Batch Processing

```python
from services.ai_services.factory import get_ai_provider

provider = await get_ai_provider("litellm-gpt4")

# Multiple requests processed in parallel with load balancing
responses = await provider.batch_completions([
    {"messages": [{"role": "user", "content": "Question 1"}], "model": "gpt-4o"},
    {"messages": [{"role": "user", "content": "Question 2"}], "model": "gpt-4o"},
    {"messages": [{"role": "user", "content": "Question 3"}], "model": "gpt-4o"},
])
```

### Embeddings with Failover

```python
provider = await get_ai_provider("litellm-gpt4")

# If Azure fails, automatically falls back to next deployment
embedding = await provider.get_embeddings(
    text="Sample text to embed",
    llm="text-embedding-3-small"
)
```

### Router Statistics

```python
provider = await get_ai_provider("litellm-gpt4")

# Get health and usage stats
stats = provider.get_router_stats()
# {
#   "healthy_deployments": ["azure/gpt-4o", "openai/gpt-4o"],
#   "model_list": ["gpt-4o"],
#   "routing_strategy": "simple-shuffle"
# }
```

## Load Balancing Scenarios

### Multi-Region Azure Deployment

```json
{
  "model_list": [
    {
      "model_name": "gpt-4o",
      "litellm_params": {
        "model": "azure/gpt-4o",
        "api_base": "https://eastus.openai.azure.com/",
        "api_key": "{azure_eastus_key}",
        "rpm": 1000
      }
    },
    {
      "model_name": "gpt-4o",
      "litellm_params": {
        "model": "azure/gpt-4o",
        "api_base": "https://westeurope.openai.azure.com/",
        "api_key": "{azure_westeurope_key}",
        "rpm": 1000
      }
    }
  ]
}
```

### Multi-Provider Fallback

```json
{
  "model_list": [
    {
      "model_name": "gpt-4o",
      "litellm_params": {
        "model": "azure/gpt-4o-deployment",
        "api_key": "{azure_key}",
        "api_base": "https://xxx.openai.azure.com/"
      }
    },
    {
      "model_name": "gpt-4o",
      "litellm_params": {
        "model": "openai/gpt-4o",
        "api_key": "{openai_key}"
      }
    },
    {
      "model_name": "gpt-4o",
      "litellm_params": {
        "model": "anthropic/claude-3-5-sonnet-20241022",
        "api_key": "{anthropic_key}"
      }
    }
  ]
}
```

## Supported Providers via LiteLLM

LiteLLM supports 100+ providers including:

- OpenAI
- Azure OpenAI
- Anthropic Claude
- Google Gemini/Vertex AI
- AWS Bedrock
- Cohere
- Groq
- Mistral
- Together AI
- Ollama (local)
- And many more...

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for full list.
