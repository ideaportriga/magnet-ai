export const ROUTE_PERMISSION_BY_ENTITY: Record<string, string> = {
  agents: 'read:agents',
  ai_apps: 'read:ai_apps',
  api_keys: 'read:api_keys',
  api_servers: 'read:api_servers',
  assistant_tools: 'read:api_servers',
  collections: 'read:collections',
  conversation: 'read:observability',
  deep_research: 'read:deep_research',
  documents: 'read:collections',
  evaluation_jobs: 'read:evaluations',
  evaluation_sets: 'read:evaluations',
  files: 'read:files',
  jobs: 'read:jobs',
  knowledge_graph: 'read:knowledge_graph',
  mcp_servers: 'read:mcp_servers',
  model: 'read:ai_models',
  note_taker: 'read:note_taker',
  observability: 'read:observability',
  observability_traces: 'read:observability',
  oauth_clients: 'write:roles',
  promptTemplates: 'read:prompts',
  prompt_queue: 'read:prompt_queue',
  provider: 'read:ai_models',
  rag_tools: 'read:rag_tools',
  retrieval: 'read:retrieval_tools',
  settings: 'read:settings',
}

const ROUTE_PERMISSION_BY_PATH_PREFIX: Array<[string, string]> = [
  ['/admin/access-log', 'read:audit'],
  ['/admin/roles', 'read:roles'],
  ['/admin/users', 'read:users'],
  ['/ai-apps', 'read:ai_apps'],
  ['/agents', 'read:agents'],
  ['/api-keys', 'read:api_keys'],
  ['/api-servers', 'read:api_servers'],
  ['/assistant-tools', 'read:api_servers'],
  ['/conversation', 'read:observability'],
  ['/deep-research', 'read:deep_research'],
  ['/evaluation-jobs', 'read:evaluations'],
  ['/evaluation-sets', 'read:evaluations'],
  ['/evaluation/compare', 'read:evaluations'],
  ['/files', 'read:files'],
  ['/jobs', 'read:jobs'],
  ['/knowledge-graph', 'read:knowledge_graph'],
  ['/knowledge-providers', 'read:knowledge_graph'],
  ['/knowledge-sources', 'read:collections'],
  ['/mcp', 'read:mcp_servers'],
  ['/model-providers', 'read:ai_models'],
  ['/model', 'read:ai_models'],
  ['/note-taker', 'read:note_taker'],
  ['/oauth-clients', 'write:roles'],
  ['/observability-traces', 'read:observability'],
  ['/prompt-queue', 'read:prompt_queue'],
  ['/prompt-templates', 'read:prompts'],
  ['/rag-tools', 'read:rag_tools'],
  ['/retrieval', 'read:retrieval_tools'],
  ['/settings', 'read:settings'],
  ['/usage', 'read:observability'],
]

export function permissionForRouteMeta(meta: Record<string, unknown> | undefined): string | undefined {
  const explicit = meta?.permission
  if (typeof explicit === 'string') return explicit

  const entity = meta?.entity
  if (typeof entity === 'string') return ROUTE_PERMISSION_BY_ENTITY[entity]

  return undefined
}

export function permissionForRoute(route: { meta?: Record<string, unknown>, path?: string, matched?: Array<{ meta?: Record<string, unknown> }> }): string | undefined {
  const byMeta = permissionForRouteMeta(route.meta)
  if (byMeta) return byMeta

  const byMatched = route.matched
    ?.map((record) => permissionForRouteMeta(record.meta))
    .find((permission): permission is string => typeof permission === 'string')
  if (byMatched) return byMatched

  const path = route.path
  if (!path) return undefined

  const match = ROUTE_PERMISSION_BY_PATH_PREFIX.find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`))
  return match?.[1]
}
