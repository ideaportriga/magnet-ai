type QueryKeyFactory = {
  all: readonly string[]
  lists: () => readonly string[]
  list: (params: Record<string, unknown>) => readonly unknown[]
  details: () => readonly string[]
  detail: (id: string) => readonly unknown[]
}

function createEntityKeys(entityName: string): QueryKeyFactory {
  return {
    all: [entityName] as const,
    lists: () => [entityName, 'list'] as const,
    list: (params: Record<string, unknown>) => [entityName, 'list', params] as const,
    details: () => [entityName, 'detail'] as const,
    detail: (id: string) => [entityName, 'detail', id] as const,
  }
}

export const entityKeys = {
  collections: createEntityKeys('collections'),
  documents: createEntityKeys('documents'),
  rag_tools: createEntityKeys('rag_tools'),
  retrieval: createEntityKeys('retrieval'),
  promptTemplates: createEntityKeys('promptTemplates'),
  ai_apps: createEntityKeys('ai_apps'),
  evaluation_sets: createEntityKeys('evaluation_sets'),
  evaluation_jobs: createEntityKeys('evaluation_jobs'),
  model: createEntityKeys('model'),
  provider: createEntityKeys('provider'),
  agents: createEntityKeys('agents'),
  assistant_tools: createEntityKeys('assistant_tools'),
  jobs: createEntityKeys('jobs'),
  mcp_servers: createEntityKeys('mcp_servers'),
  api_keys: createEntityKeys('api_keys'),
  api_servers: createEntityKeys('api_servers'),
  observability_traces: createEntityKeys('observability_traces'),
  knowledge_graph: createEntityKeys('knowledge_graph'),
  plugins: createEntityKeys('plugins'),
  files: createEntityKeys('files'),
} as const
