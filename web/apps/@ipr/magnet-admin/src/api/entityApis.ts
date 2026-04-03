import { createApiClient, createEntityApi } from '@shared/api'
import type { ApiClient, EntityApi } from '@shared/api'
import type {
  Agent,
  AiApp,
  ApiKey,
  ApiServer,

  AssistantTool,
  Collection,
  Document,
  EvaluationJob,
  EvaluationSet,
  Job,
  KnowledgeGraph,
  McpServer,
  Model,
  ObservabilityTrace,
  Plugin,
  PromptTemplate,
  Provider,
  RetrievalTool,
  RagTool,
  StoredFile,
} from '@/types'

export interface EntityApis {
  collections: EntityApi<Collection>
  documents: EntityApi<Document>
  rag_tools: EntityApi<RagTool>
  retrieval: EntityApi<RetrievalTool>
  promptTemplates: EntityApi<PromptTemplate>
  ai_apps: EntityApi<AiApp>
  evaluation_sets: EntityApi<EvaluationSet>
  evaluation_jobs: EntityApi<EvaluationJob>
  model: EntityApi<Model>
  provider: EntityApi<Provider>
  agents: EntityApi<Agent>
  assistant_tools: EntityApi<AssistantTool>
  jobs: EntityApi<Job>
  mcp_servers: EntityApi<McpServer>
  api_keys: EntityApi<ApiKey>
  api_servers: EntityApi<ApiServer>
  observability_traces: EntityApi<ObservabilityTrace>
  knowledge_graph: EntityApi<KnowledgeGraph>
  plugins: EntityApi<Plugin>
  files: EntityApi<StoredFile>
}

/** Entity key → API service path (matching existing chroma.js config) */
const SERVICE_PATHS: Record<keyof EntityApis, string> = {
  collections: 'sql_collections',
  documents: 'collections',  // documents are nested: collections/{id}/documents/paginate/offset
  rag_tools: 'rag_tools',
  retrieval: 'retrieval_tools',
  promptTemplates: 'prompt_templates',
  ai_apps: 'ai_apps',
  evaluation_sets: 'evaluation_sets',
  evaluation_jobs: 'evaluations',
  model: 'models',
  provider: 'providers',
  agents: 'agents',
  assistant_tools: 'assistant_tools',
  jobs: 'jobs',
  mcp_servers: 'mcp_servers',
  api_keys: 'api_keys',
  api_servers: 'api_servers',
  observability_traces: 'traces',
  knowledge_graph: 'knowledge_graphs',
  plugins: 'knowledge_sources/plugins',
  files: 'files',
}

let _client: ApiClient | null = null
let _apis: EntityApis | null = null

export function createEntityApis(baseUrl: string, credentials: RequestCredentials = 'include'): EntityApis {
  _client = createApiClient({ baseUrl, credentials })

  _apis = {} as EntityApis
  for (const [key, path] of Object.entries(SERVICE_PATHS)) {
    ;(_apis as Record<string, EntityApi<unknown>>)[key] = createEntityApi(_client, path)
  }

  // evaluation_jobs: list uses the aggregated /evaluations/list endpoint,
  // but detail/update/delete use the standard /evaluations/{id} endpoints.
  const baseEvalJobsApi = _apis.evaluation_jobs
  const evalJobsListApi = createEntityApi<EvaluationJob>(_client, 'evaluations/list')
  _apis.evaluation_jobs = {
    ...baseEvalJobsApi,
    list: evalJobsListApi.list,
  }

  return _apis
}

export function getEntityApis(): EntityApis {
  if (!_apis) throw new Error('Entity APIs not initialized. Call createEntityApis() first.')
  return _apis
}

export function getApiClient(): ApiClient {
  if (!_client) throw new Error('API client not initialized. Call createEntityApis() first.')
  return _client
}
