export interface EntityAccessConfig {
  entityKey: string
  permissionResource: string
  readPermission: string
  writePermission: string
  deletePermission: string
  readonlyProvideKey: string
}

interface EntityAccessOptions {
  readPermission?: string
  writePermission?: string
  deletePermission?: string
}

const entityAccess = {
  ai_apps: access('ai_apps', 'ai_apps', 'aiAppReadonly'),
  agents: access('agents', 'agents', 'agentReadonly'),
  api_keys: access('api_keys', 'api_keys', 'apiKeyReadonly'),
  api_servers: access('api_servers', 'api_servers', 'apiServerReadonly'),
  assistant_tools: access('assistant_tools', 'api_servers', 'assistantToolReadonly'),
  collections: access('collections', 'collections', 'collectionReadonly'),
  deep_research: access('deep_research', 'deep_research', 'deepResearchReadonly'),
  evaluations: access('evaluations', 'evaluations', 'evaluationReadonly'),
  evaluation_sets: access('evaluation_sets', 'evaluations', 'evaluationSetReadonly'),
  files: access('files', 'files', 'fileReadonly'),
  jobs: access('jobs', 'jobs', 'jobReadonly', {
    // Jobs catalog has no delete:* code today — keep delete behind write.
    deletePermission: 'write:jobs',
  }),
  knowledge_graph: access('knowledge_graph', 'knowledge_graph', 'knowledgeGraphReadonly'),
  knowledge_providers: access('provider', 'knowledge_graph', 'knowledgeProviderReadonly'),
  mcp_servers: access('mcp_servers', 'mcp_servers', 'mcpReadonly'),
  metrics: access('metrics', 'metrics', 'metricReadonly'),
  model: access('model', 'ai_models', 'modelReadonly'),
  model_providers: access('provider', 'providers', 'modelProviderReadonly'),
  note_taker: access('note_taker', 'note_taker', 'noteTakerReadonly'),
  oauth_clients: access('oauth_clients', 'oauth_clients', 'oauthClientReadonly'),
  promptTemplates: access('promptTemplates', 'prompts', 'promptReadonly'),
  rag_tools: access('rag_tools', 'rag_tools', 'ragReadonly'),
  retrieval: access('retrieval', 'retrieval_tools', 'retrievalReadonly'),
  settings: access('settings', 'settings', 'settingsReadonly', {
    // Settings has no delete:* — admin gates write/seed via write:settings.
    deletePermission: 'write:settings',
  }),
  traces: access('traces', 'traces', 'traceReadonly'),
} as const

function access(
  entityKey: string,
  permissionResource: string,
  readonlyProvideKey: string,
  options: EntityAccessOptions = {},
): EntityAccessConfig {
  return {
    entityKey,
    permissionResource,
    readPermission: options.readPermission ?? `read:${permissionResource}`,
    writePermission: options.writePermission ?? `write:${permissionResource}`,
    deletePermission: options.deletePermission ?? `delete:${permissionResource}`,
    readonlyProvideKey,
  }
}

export type EntityAccessKey = keyof typeof entityAccess

export function getEntityAccessConfig(entityKey: EntityAccessKey): EntityAccessConfig {
  return entityAccess[entityKey]
}

export { entityAccess }
