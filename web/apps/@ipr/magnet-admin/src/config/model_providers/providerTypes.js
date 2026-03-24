/**
 * Shared provider type definitions and labels.
 *
 * Single source of truth for provider types used across the admin UI.
 * Keep in sync with backend PROVIDER_TYPE_TO_LITELLM_PREFIX mapping
 * in api/src/services/ai_services/providers/universal.py
 */

// Provider type options for create/select dropdowns
export const providerTypeOptions = [
  // Major Cloud Providers
  { label: 'OpenAI', value: 'openai' },
  { label: 'Azure OpenAI', value: 'azure_open_ai' },
  { label: 'Azure AI', value: 'azure_ai' },
  { label: 'AWS Bedrock', value: 'bedrock' },
  { label: 'Google Vertex AI', value: 'vertex_ai' },
  // Inference Providers
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google Gemini', value: 'gemini' },
  { label: 'Groq', value: 'groq' },
  { label: 'Mistral', value: 'mistral' },
  { label: 'Cohere', value: 'cohere' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'xAI (Grok)', value: 'xai' },
  { label: 'Perplexity', value: 'perplexity' },
  { label: 'Fireworks AI', value: 'fireworks_ai' },
  { label: 'Together AI', value: 'together_ai' },
  { label: 'AI21 Labs', value: 'ai21' },
  { label: 'Cerebras', value: 'cerebras' },
  { label: 'SambaNova', value: 'sambanova' },
  { label: 'FriendliAI', value: 'friendliai' },
  { label: 'OpenRouter', value: 'openrouter' },
  // Self-hosted / Local
  { label: 'Ollama', value: 'ollama' },
  { label: 'vLLM', value: 'vllm' },
  { label: 'LM Studio', value: 'lm_studio' },
  // Audio / Multimodal
  { label: 'ElevenLabs', value: 'elevenlabs' },
  { label: 'Azure Speech', value: 'azure_speech' },
  { label: 'Mistral STT', value: 'mistral_stt' },
  { label: 'Deepgram', value: 'deepgram' },
  // OCI
  { label: 'OCI', value: 'oci' },
  { label: 'OCI Llama', value: 'oci_llama' },
  { label: 'OCI GenAI', value: 'oci_genai' },
  // Custom
  { label: 'Custom (OpenAI-compatible)', value: 'custom' },
]

// Build type labels map from options
const _typeLabels = Object.fromEntries(
  providerTypeOptions.map(({ value, label }) => [value, label])
)

/**
 * Format a provider type string to a human-readable label.
 * Falls back to the raw type value if not found in the mapping.
 */
export const formatProviderType = (type) => {
  if (!type) return '-'
  return _typeLabels[type] || type
}

/**
 * Endpoint hints per provider type, shown when creating a new provider.
 */
export const providerEndpointHints = {
  openai: 'Leave empty to use official OpenAI API. Only specify for OpenAI-compatible APIs.',
  azure_open_ai: 'Required. Your Azure OpenAI resource URL (e.g., https://your-resource.openai.azure.com)',
  azure_ai: 'Required. Your Azure AI endpoint URL.',
  groq: 'Leave empty to use default Groq API endpoint.',
  anthropic: 'Leave empty to use official Anthropic API.',
  gemini: 'Leave empty to use official Google Gemini API.',
  mistral: 'Leave empty to use official Mistral API.',
  cohere: 'Leave empty to use official Cohere API.',
  deepseek: 'Leave empty to use official DeepSeek API.',
  xai: 'Leave empty to use official xAI API.',
  perplexity: 'Leave empty to use official Perplexity API.',
  fireworks_ai: 'Leave empty to use official Fireworks AI API.',
  together_ai: 'Leave empty to use official Together AI API.',
  ai21: 'Leave empty to use official AI21 Labs API.',
  cerebras: 'Leave empty to use official Cerebras API.',
  sambanova: 'Leave empty to use official SambaNova API.',
  friendliai: 'Leave empty to use official FriendliAI API.',
  openrouter: 'Leave empty to use official OpenRouter API.',
  bedrock: 'AWS region-based. Configure AWS credentials in secrets (aws_access_key_id, aws_secret_access_key, aws_region_name).',
  vertex_ai: 'Google Cloud project-based. Configure project & credentials in connection config.',
  ollama: 'Required. Your Ollama server URL (e.g., http://localhost:11434).',
  vllm: 'Required. Your vLLM server URL (e.g., http://localhost:8000).',
  lm_studio: 'Required. Your LM Studio server URL (e.g., http://localhost:1234).',
  elevenlabs: 'Leave empty to use official ElevenLabs API.',
  mistral_stt: 'Leave empty to use official Mistral API for speech-to-text.',
  deepgram: 'Leave empty to use official Deepgram API.',
  oci: 'Required. Your OCI endpoint URL.',
  oci_llama: 'Required. Your OCI Llama endpoint URL.',
  oci_genai: 'Required. Your OCI GenAI endpoint URL.',
  custom: 'Required. Your OpenAI-compatible API endpoint URL.',
}

/**
 * Recommended secret keys per provider type.
 * Used to show pre-populated secret fields when configuring a provider.
 */
export const providerSecretKeys = {
  openai: [
    { key: 'api_key', label: 'API Key', placeholder: 'sk-...' },
  ],
  azure_open_ai: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Azure OpenAI API key' },
  ],
  azure_ai: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Azure AI API key' },
  ],
  anthropic: [
    { key: 'api_key', label: 'API Key', placeholder: 'sk-ant-...' },
  ],
  gemini: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Google AI API key' },
  ],
  groq: [
    { key: 'api_key', label: 'API Key', placeholder: 'gsk_...' },
  ],
  mistral: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Mistral API key' },
  ],
  cohere: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Cohere API key' },
  ],
  deepseek: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your DeepSeek API key' },
  ],
  xai: [
    { key: 'api_key', label: 'API Key', placeholder: 'xai-...' },
  ],
  perplexity: [
    { key: 'api_key', label: 'API Key', placeholder: 'pplx-...' },
  ],
  fireworks_ai: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Fireworks AI API key' },
  ],
  together_ai: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Together AI API key' },
  ],
  ai21: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your AI21 Labs API key' },
  ],
  cerebras: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Cerebras API key' },
  ],
  sambanova: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your SambaNova API key' },
  ],
  friendliai: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your FriendliAI API key' },
  ],
  openrouter: [
    { key: 'api_key', label: 'API Key', placeholder: 'sk-or-...' },
  ],
  bedrock: [
    { key: 'aws_access_key_id', label: 'AWS Access Key ID', placeholder: 'AKIA...' },
    { key: 'aws_secret_access_key', label: 'AWS Secret Access Key', placeholder: 'Your AWS secret key' },
    { key: 'aws_region_name', label: 'AWS Region', placeholder: 'us-east-1' },
  ],
  vertex_ai: [
    { key: 'vertex_project', label: 'GCP Project ID', placeholder: 'my-gcp-project' },
    { key: 'vertex_location', label: 'GCP Location', placeholder: 'us-central1' },
    { key: 'vertex_credentials', label: 'Service Account JSON', placeholder: '{"type": "service_account", ...}' },
  ],
  ollama: [],
  vllm: [
    { key: 'api_key', label: 'API Key (optional)', placeholder: 'Leave empty if not required' },
  ],
  lm_studio: [],
  elevenlabs: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your ElevenLabs API key' },
  ],
  mistral_stt: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Mistral API key' },
  ],
  deepgram: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your Deepgram API key' },
  ],
  oci: [
    { key: 'api_key', label: 'API Key / Token', placeholder: 'Your OCI auth token' },
  ],
  oci_llama: [
    { key: 'api_key', label: 'API Key / Token', placeholder: 'Your OCI auth token' },
  ],
  oci_genai: [
    { key: 'api_key', label: 'API Key / Token', placeholder: 'Your OCI GenAI auth token' },
  ],
  custom: [
    { key: 'api_key', label: 'API Key', placeholder: 'Your API key (if required)' },
  ],
}

/**
 * Recommended connection_config keys per provider type.
 * These are non-secret configuration values.
 */
export const providerConnectionConfigKeys = {
  azure_open_ai: [
    { key: 'api_version', label: 'API Version', placeholder: '2024-02-01', defaultValue: '2024-02-01' },
  ],
  azure_ai: [
    { key: 'api_version', label: 'API Version', placeholder: '2024-05-01-preview', defaultValue: '2024-05-01-preview' },
  ],
  bedrock: [
    { key: 'aws_region_name', label: 'AWS Region', placeholder: 'us-east-1' },
  ],
  vertex_ai: [
    { key: 'vertex_project', label: 'GCP Project ID', placeholder: 'my-gcp-project' },
    { key: 'vertex_location', label: 'GCP Location', placeholder: 'us-central1' },
  ],
}
