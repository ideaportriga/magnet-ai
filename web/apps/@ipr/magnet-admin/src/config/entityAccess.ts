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
  api_keys: access('api_keys', 'api_keys', 'apiKeyReadonly', {
    deletePermission: 'write:api_keys',
  }),
  api_servers: access('api_servers', 'api_servers', 'apiServerReadonly'),
  assistant_tools: access('assistant_tools', 'api_servers', 'assistantToolReadonly', {
    deletePermission: 'write:api_servers',
  }),
  collections: access('collections', 'collections', 'collectionReadonly'),
  deep_research: access('deep_research', 'deep_research', 'deepResearchReadonly', {
    deletePermission: 'write:deep_research',
  }),
  evaluation_sets: access('evaluation_sets', 'evaluations', 'evaluationSetReadonly', {
    deletePermission: 'write:evaluations',
  }),
  knowledge_graph: access('knowledge_graph', 'knowledge_graph', 'knowledgeGraphReadonly'),
  knowledge_providers: access('provider', 'knowledge_graph', 'knowledgeProviderReadonly'),
  mcp_servers: access('mcp_servers', 'mcp_servers', 'mcpReadonly'),
  model: access('model', 'ai_models', 'modelReadonly', {
    deletePermission: 'write:ai_models',
  }),
  model_providers: access('provider', 'ai_models', 'modelProviderReadonly', {
    deletePermission: 'write:ai_models',
  }),
  note_taker: access('note_taker', 'note_taker', 'noteTakerReadonly', {
    deletePermission: 'write:note_taker',
  }),
  oauth_clients: access('oauth_clients', 'roles', 'oauthClientReadonly', {
    readPermission: 'write:roles',
    writePermission: 'write:roles',
    deletePermission: 'write:roles',
  }),
  promptTemplates: access('promptTemplates', 'prompts', 'promptReadonly'),
  rag_tools: access('rag_tools', 'rag_tools', 'ragReadonly'),
  retrieval: access('retrieval', 'retrieval_tools', 'retrievalReadonly'),
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
