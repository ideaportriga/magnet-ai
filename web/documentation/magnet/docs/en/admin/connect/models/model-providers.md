# Model Providers Configuration Guide

This is a detailed configuration guide for admins with access to model deployments. Depending on Model Provider type selected, you will need to fill in required connection fields.

## Supported Providers

### 1. OpenAI Provider

**Type:** `openai`

#### Parameters

**Endpoint:** Leave `null` for official OpenAI API. Specify custom URL only for compatible APIs (e.g., local models with OpenAI-compatible interface).

**Secrets:**

- `api_key` - Your OpenAI API key

---

### 2. Azure OpenAI Provider

**Type:** `azure_open_ai`

#### Parameters

**Endpoint:** URL of your Azure OpenAI resource (required, e.g., `https://your-resource.openai.azure.com`)

**Connection_config:**

- `api_version` - Azure OpenAI API version (e.g., `2023-03-15-preview`, `2024-02-01`)

**Secrets_encrypted:**

- `api_key` - Azure OpenAI access key

#### Features

- Azure uses deployment names, not model names

---

### 3. Azure AI Provider

**Type:** `azure_ai`

#### Parameters

**Endpoint:** URL of your Azure AI Service endpoint (e.g., `https://your-ai-service.cognitiveservices.azure.com`)

**Connection_config:**

- `api_version` - API version (recommended `2025-01-01-preview`)
- `timeout` - Timeout in milliseconds (default 30000)

**Secrets:**

- `api_key` - Azure AI access key

---

### 4. Groq Provider

**Type:** `groq`

#### Parameters

**Endpoint:** `https://api.groq.com/openai/v1` (standard endpoint)

**Secrets_encrypted:**

- `api_key` - Your Groq API key

#### Features

- Uses OpenAI-compatible interface
- Does not support embeddings

---

### 5. OCI Provider (Oracle Cloud - Cohere)

**Type:** `oci`

#### Parameters

**Endpoint:** OCI Generative AI endpoint URL for your region (e.g., `https://inference.generativeai.us-chicago-1.oci.oraclecloud.com`)

**Secrets_encrypted:**

- `compartment_id` - OCID of your compartment
- `user` - User OCID
- `fingerprint` - API key fingerprint
- `tenancy` - Tenancy OCID
- `region` - OCI region (e.g., `us-chicago-1`)
- `key_content` - Private key content (with escaped `\n`)

#### Features

- Uses OCI SDK for Python
- Supports embeddings via Cohere models
- Embeddings usage counted in characters
- Requires OCI API key setup

---

### 6. OCI Llama Provider (Oracle Cloud - Llama)

**Type:** `oci_llama`

#### Parameters

**Endpoint:** OCI Generative AI endpoint URL for your region (e.g., `https://inference.generativeai.us-chicago-1.oci.oraclecloud.com`)

**Secrets_encrypted:**

- Same parameters as OCI Provider (compartment_id, user, fingerprint, tenancy, region, key_content)

#### Features

- Uses Generic Chat Request API (different from Cohere API)
- Supports system messages via special format
- Does not support embeddings
- Requires OCI API key setup

---

## General Guidelines

- **Endpoint** - Base URL only, without path (stored as separate field)
- **Connection** - Non-sensitive configuration (api_version, timeout, etc.)
- **Secrets** - All keys and credentials (API keys, private keys, etc.)

---

## Troubleshooting

### Provider not working

- Verify endpoint URL (should not have trailing slash)

### Authentication errors

- Verify API keys are current and valid
- For OCI, ensure private key is properly escaped (`\\n` instead of `\n`)

### Model not found

- For Azure, verify you're using deployment name, not model name
- Ensure the model is available in your region/account
