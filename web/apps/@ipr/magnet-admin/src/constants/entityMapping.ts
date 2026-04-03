import type { AllEntityQueries } from '@/queries/entities'

/**
 * Maps route.meta.entity values to the entityType stored in editBufferStore.
 *
 * During migration from Pinia entity detail stores to composables, the buffer
 * entityType changes from old camelCase names to AllEntityQueries keys.
 * This mapping handles both old and new names.
 *
 * After full migration, all values will equal their keys (1:1 mapping)
 * and this constant can be replaced with a direct passthrough.
 */
export const ROUTE_ENTITY_TO_BUFFER_TYPE: Record<string, string> = {
  // Old stores use camelCase names; these will change to match keys as components are migrated
  provider: 'provider',
  ai_apps: 'ai_apps',
  collections: 'collections',
  evaluation_sets: 'evaluation_sets',
  assistant_tools: 'assistant_tools',
  model: 'model',
  mcp_servers: 'mcp_servers',
  api_servers: 'api_servers',

  observability_traces: 'observability_traces',
  rag_tools: 'rag_tools',
  retrieval: 'retrieval',
  promptTemplates: 'promptTemplates',
  agents: 'agents',
}

/**
 * Maps route.meta.entity values to AllEntityQueries keys for mutations.
 */
export const ROUTE_ENTITY_TO_QUERY_KEY: Record<string, keyof AllEntityQueries> = {
  provider: 'provider',
  ai_apps: 'ai_apps',
  collections: 'collections',
  evaluation_sets: 'evaluation_sets',
  assistant_tools: 'assistant_tools',
  model: 'model',
  mcp_servers: 'mcp_servers',
  api_servers: 'api_servers',

  observability_traces: 'observability_traces',
  rag_tools: 'rag_tools',
  retrieval: 'retrieval',
  promptTemplates: 'promptTemplates',
  agents: 'agents',
}
