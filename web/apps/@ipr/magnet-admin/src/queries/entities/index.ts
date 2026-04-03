import type { EntityApis } from '@/api'
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
import { createEntityQueries, type EntityQueries } from '../createEntityQueries'

export interface AllEntityQueries {
  collections: EntityQueries<Collection>
  documents: EntityQueries<Document>
  rag_tools: EntityQueries<RagTool>
  retrieval: EntityQueries<RetrievalTool>
  promptTemplates: EntityQueries<PromptTemplate>
  ai_apps: EntityQueries<AiApp>
  evaluation_sets: EntityQueries<EvaluationSet>
  evaluation_jobs: EntityQueries<EvaluationJob>
  model: EntityQueries<Model>
  provider: EntityQueries<Provider>
  agents: EntityQueries<Agent>
  assistant_tools: EntityQueries<AssistantTool>
  jobs: EntityQueries<Job>
  mcp_servers: EntityQueries<McpServer>
  api_keys: EntityQueries<ApiKey>
  api_servers: EntityQueries<ApiServer>
  observability_traces: EntityQueries<ObservabilityTrace>
  knowledge_graph: EntityQueries<KnowledgeGraph>
  plugins: EntityQueries<Plugin>
  files: EntityQueries<StoredFile>
}

let _queries: AllEntityQueries | null = null

export function initEntityQueries(apis: EntityApis): AllEntityQueries {
  _queries = {
    collections: createEntityQueries<Collection>('collections', apis.collections),
    documents: createEntityQueries<Document>('documents', apis.documents),
    rag_tools: createEntityQueries<RagTool>('rag_tools', apis.rag_tools),
    retrieval: createEntityQueries<RetrievalTool>('retrieval', apis.retrieval),
    promptTemplates: createEntityQueries<PromptTemplate>('promptTemplates', apis.promptTemplates),
    ai_apps: createEntityQueries<AiApp>('ai_apps', apis.ai_apps),
    evaluation_sets: createEntityQueries<EvaluationSet>('evaluation_sets', apis.evaluation_sets),
    evaluation_jobs: createEntityQueries<EvaluationJob>('evaluation_jobs', apis.evaluation_jobs),
    model: createEntityQueries<Model>('model', apis.model),
    provider: createEntityQueries<Provider>('provider', apis.provider),
    agents: createEntityQueries<Agent>('agents', apis.agents),
    assistant_tools: createEntityQueries<AssistantTool>('assistant_tools', apis.assistant_tools),
    jobs: createEntityQueries<Job>('jobs', apis.jobs),
    mcp_servers: createEntityQueries<McpServer>('mcp_servers', apis.mcp_servers),
    api_keys: createEntityQueries<ApiKey>('api_keys', apis.api_keys),
    api_servers: createEntityQueries<ApiServer>('api_servers', apis.api_servers),
    observability_traces: createEntityQueries<ObservabilityTrace>('observability_traces', apis.observability_traces),
    knowledge_graph: createEntityQueries<KnowledgeGraph>('knowledge_graph', apis.knowledge_graph),
    plugins: createEntityQueries<Plugin>('plugins', apis.plugins),
    files: createEntityQueries<StoredFile>('files', apis.files),
  }
  return _queries
}

export function useEntityQueries(): AllEntityQueries {
  if (!_queries) throw new Error('Entity queries not initialized. Call initEntityQueries() first.')
  return _queries
}
